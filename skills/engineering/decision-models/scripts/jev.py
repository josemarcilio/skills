# /// script
# requires-python = ">=3.10"
# dependencies = ["typesafe-sdk>=0.7.2,<0.8"]
# ///
"""Ask a JEV-style decision model typed questions, with thresholds and a never-fail contract.

The model only adds a signal. Every problem (server down, model not pulled, timeout, bad reply)
ends as "no signal" with exit code 0, so the caller falls back to its own judgment.

  uv run jev.py health [--provider ollama|typesafe] [--model <name>]
  uv run jev.py ask --spec <spec.json> (--state-file <text file> | --state-json <json file>)
                    [--provider ollama|typesafe] [--model <name>]

Providers:
  ollama    local Ollama 0.35+ (default). Base URL: --base-url, else TYPESAFE_BASE_URL, else
            http://localhost:11434. Model: --model, else TYPESAFE_DEFAULT_MODEL, else tev1.
  typesafe  TypeSafe's hosted API. Needs TYPESAFE_API_KEY. Base URL: --base-url, else
            https://api.typesafe.ai. Model: --model, else jev-latest. TYPESAFE_BASE_URL and
            TYPESAFE_DEFAULT_MODEL are ignored here: the Ollama setup sets them to local values.

Spec (JSON):
  {
    "state_key": "comment",          # key for --state-file text (default "text")
    "max_chars": 6000,               # per string field; longer keeps start + end (default 6000)
    "questions": {
      "<name>": {"type": "noul",   "instructions": "...", "sure": 0.85},                    # yes | no | undecided
      "<name>": {"type": "noul",   "instructions": "...", "mode": "flag", "threshold": 0.5}, # flag | no | unknown
      "<name>": {"type": "choice", "instructions": "...", "criteria": {"opt": "meaning"},
                 "sure": 0.85, "min_confidence": 0.0},                                      # opt | undecided
      "<name>": {"type": "score",  "instructions": "...", "criteria": ["Low", "High"],
                 "sure": 0.85}                                                              # level | undecided
    }
  }
`sure`, `mode`, `threshold` and `min_confidence` stay local; only type, instructions and criteria
are sent to the model.
"""

import argparse
import codecs
import json
import math
import os
import re
import sys

import httpx2
from typesafe_sdk import (
    Choice,
    Noul,
    RetryPolicy,
    Score,
    TypeSafeAuthenticationError,
    TypeSafeBadRequestError,
    TypeSafeClient,
    TypeSafeNotFoundError,
    TypeSafePermissionDeniedError,
)

PROVIDERS = {
    "ollama": {"base_url": "http://localhost:11434", "model": "tev1"},
    "typesafe": {"base_url": "https://api.typesafe.ai", "model": "jev-latest"},
}
DEFAULT_PROVIDER = "ollama"
DEFAULT_BASE_URL = PROVIDERS["ollama"]["base_url"]
DEFAULT_MODEL = PROVIDERS["ollama"]["model"]
MIN_OLLAMA = (0, 35)
TIMEOUT = 120.0  # a cold model load takes 10-25 s on a laptop
HEALTH_TIMEOUT = 3.0
DEFAULT_MAX_CHARS = 6_000  # tev1 takes 2050 tokens per question prompt (state + question)
MAX_REQUEST_BYTES = 60 * 1024  # the endpoint takes 64 KiB per request; keep a margin
DEFAULT_SURE = 0.85
DEFAULT_FLAG = 0.5
TYPES = ("noul", "choice", "score")


class SpecError(ValueError):
    pass


def validate_spec(spec):
    questions = spec.get("questions") if isinstance(spec, dict) else None
    if not isinstance(questions, dict) or not questions:
        raise SpecError("spec needs a non-empty 'questions' object")
    if len(questions) > 64:
        raise SpecError("at most 64 questions per request")
    for name, q in questions.items():
        if not isinstance(q, dict) or q.get("type") not in TYPES:
            raise SpecError(f"question {name!r}: type must be one of {TYPES}, got {q.get('type') if isinstance(q, dict) else q!r}")
        if not q.get("instructions"):
            raise SpecError(f"question {name!r}: missing instructions")
        if q["type"] == "choice" and not (isinstance(q.get("criteria"), dict) and q["criteria"]):
            raise SpecError(f"question {name!r}: choice needs a criteria object")
        if q["type"] == "score" and not (isinstance(q.get("criteria"), list) and 2 <= len(q["criteria"]) <= 10):
            raise SpecError(f"question {name!r}: score needs 2-10 criteria levels")
        if q.get("mode", "two_sided") not in ("two_sided", "flag"):
            raise SpecError(f"question {name!r}: mode must be two_sided or flag")
    return spec


def _probability(p):
    try:
        p = float(p)
    except (TypeError, ValueError):
        return None
    return p if 0.0 <= p <= 1.0 and not math.isnan(p) else None


def _top(probabilities):
    probs = {}
    for key, value in (probabilities or {}).items():
        p = _probability(value)
        if p is not None:
            probs[key] = p
    if not probs:
        return None, None
    top = max(probs, key=probs.get)
    return top, probs[top]


def verdict(question, value, confidence=None):
    """Turn one raw answer into the word the caller acts on."""
    kind = question["type"]
    sure = question.get("sure", DEFAULT_SURE)
    if kind == "noul":
        p = _probability(value)
        if question.get("mode") == "flag":
            if p is None:
                return "unknown"
            return "flag" if p >= question.get("threshold", DEFAULT_FLAG) else "no"
        if p is None:
            return "undecided"
        return "yes" if p >= sure else "no" if p <= 1 - sure else "undecided"
    top, p = _top(value)
    if top is None or p < sure:
        return "undecided"
    if kind == "choice":
        min_conf = question.get("min_confidence")
        if min_conf is not None and (_probability(confidence) or 0.0) < min_conf:
            return "undecided"
        return top
    levels = question.get("criteria") or []
    index = int(top)
    return str(levels[index]) if 0 <= index < len(levels) else "undecided"


def _no_answer(question):
    return "unknown" if question.get("mode") == "flag" else "undecided"


def _one_line(text, limit=200):
    return " ".join(str(text).split())[:limit]


def no_signal(spec, reason):
    result = {name: _no_answer(q) for name, q in spec["questions"].items()}
    result["raw"] = f"unavailable ({_one_line(reason)})"
    return result


def _sdk_question(q):
    if q["type"] == "noul":
        return Noul(instructions=q["instructions"])
    if q["type"] == "choice":
        return Choice(instructions=q["instructions"], criteria=q["criteria"])
    return Score(instructions=q["instructions"], criteria=q["criteria"])


def _truncate(state, max_chars):
    truncated = False
    out = {}
    for key, value in state.items():
        if isinstance(value, str) and len(value) > max_chars:
            # Keep the start and the end: instructions hidden at the end still get read.
            marker = "\n[...]\n"
            head = (max_chars - len(marker)) // 2
            tail = max_chars - len(marker) - head
            value, truncated = value[:head] + marker + value[-tail:], True
        out[key] = value
    return out, truncated


def _raw_part(name, q, answer):
    if q["type"] == "noul":
        return f"{name}={answer.noul:.2f}"
    top, p = _top(answer.probabilities)
    label = top
    if q["type"] == "score" and top is not None and 0 <= int(top) < len(q["criteria"]):
        label = q["criteria"][int(top)]
    return f"{name}={label}:{p if p is None else round(p, 2)}"


def resolve_target(provider, base_url, model):
    """Explicit values win; then, for ollama only, the SDK's env vars; then provider defaults."""
    defaults = PROVIDERS[provider]
    if provider == "ollama":
        base_url = base_url or os.environ.get("TYPESAFE_BASE_URL") or defaults["base_url"]
        model = model or os.environ.get("TYPESAFE_DEFAULT_MODEL") or defaults["model"]
    return base_url or defaults["base_url"], model or defaults["model"]


def _api_key(provider):
    key = (os.environ.get("TYPESAFE_API_KEY") or "").strip()
    if provider == "ollama":
        return key or "ollama"  # Ollama ignores it, the SDK requires one
    return key or None


def _redact(text):
    key = (os.environ.get("TYPESAFE_API_KEY") or "").strip()
    return text.replace(key, "***") if len(key) >= 4 else text


def _auth_reason(provider):
    if provider == "ollama":
        return "server refused the request (401/403)"
    return "TYPESAFE_API_KEY rejected (401/403); check the key and its balance"


def _missing_model_reason(provider, model):
    if provider == "ollama":
        return f"model {model} not found; run: ollama pull {model}"
    return f"model {model} not offered by the API; list models with: jev.py health --provider typesafe"


def ask(spec, state, *, base_url, model, provider=DEFAULT_PROVIDER, transport=None, retry_backoff=0.5):
    questions = spec["questions"]
    api_key = _api_key(provider)
    if api_key is None:
        return no_signal(spec, "TYPESAFE_API_KEY is not set")
    state, truncated = _truncate(state, spec.get("max_chars", DEFAULT_MAX_CHARS))
    size = len(json.dumps({"state": state, "questions": questions}, ensure_ascii=False).encode("utf-8"))
    if size > MAX_REQUEST_BYTES:
        return no_signal(spec, f"request is {size} bytes; the endpoint takes 64 KiB")
    # One retry covers cold-load failures (500 / bad_alloc right after load). A timeout is not
    # retried, so the worst case is one TIMEOUT plus one fast failure.
    retry = RetryPolicy(max_retries=1, backoff_initial=retry_backoff, timeout=None, api_timeout_error=False)
    try:
        with TypeSafeClient(base_url=base_url, api_key=api_key, model=model, timeout=TIMEOUT, retry=retry, transport=transport) as client:
            reply = client.system_one(state=state, questions={n: _sdk_question(q) for n, q in questions.items()})
        result, raw = {}, []
        for name, q in questions.items():
            answer = reply.answers[name]
            if q["type"] == "noul":
                result[name] = verdict(q, answer.noul)
            else:
                result[name] = verdict(q, answer.probabilities, getattr(answer, "confidence", None))
            raw.append(_raw_part(name, q, answer))
    except TypeSafeNotFoundError:
        return no_signal(spec, _missing_model_reason(provider, model))
    except TypeSafeBadRequestError as error:
        reason = _one_line(_redact(str(error)), 160)
        if "tokens" in reason:
            reason += "; lower max_chars in the spec"
        return no_signal(spec, reason)
    except (TypeSafeAuthenticationError, TypeSafePermissionDeniedError):
        return no_signal(spec, _auth_reason(provider))
    except Exception as error:  # never fail the caller; any problem is "no signal"
        return no_signal(spec, f"{type(error).__name__}: {_one_line(_redact(str(error)), 120)}")
    if truncated:
        for name, q in questions.items():
            if q.get("mode") == "flag" and result[name] == "no":
                result[name] = "unknown"  # the cut-off part was never read
    result["raw"] = " ".join(raw) + (" truncated" if truncated else "")
    return result


def _version(text):
    return tuple(int(part) for part in re.findall(r"\d+", str(text))[:2])


def _has_model(names, model):
    tagged = ":" in model.rsplit("/", 1)[-1]
    return model in names or (not tagged and f"{model}:latest" in names)


def health(*, base_url, model, provider=DEFAULT_PROVIDER, transport=None):
    if provider == "typesafe":
        return _health_typesafe(base_url, model, transport)
    return _health_ollama(base_url, model, transport)


def _health_typesafe(base_url, model, transport):
    def unavailable(reason):
        return {"available": "no", "model": model, "reason": reason}

    api_key = _api_key("typesafe")
    if api_key is None:
        return unavailable("TYPESAFE_API_KEY is not set")
    try:
        with TypeSafeClient(base_url=base_url, api_key=api_key, model=model, timeout=10.0,
                            retry=RetryPolicy(max_retries=0), transport=transport) as client:
            names = {m.name for m in client.models.list().models}
    except (TypeSafeAuthenticationError, TypeSafePermissionDeniedError):
        return unavailable(_auth_reason("typesafe"))
    except Exception as error:
        return unavailable(f"API not reachable at {base_url} ({type(error).__name__}: {_one_line(_redact(str(error)), 80)})")
    if model not in names:
        return unavailable(f"model {model} not offered; available: {', '.join(sorted(names)) or 'none'}")
    return {"available": "yes", "model": model, "reason": f"TypeSafe API, {len(names)} models"}


def _health_ollama(base_url, model, transport):
    def unavailable(reason):
        return {"available": "no", "model": model, "reason": reason}

    try:
        with httpx2.Client(base_url=base_url, timeout=HEALTH_TIMEOUT, transport=transport) as http:
            version_reply = http.get("/api/version")
            tags_reply = http.get("/api/tags")
    except Exception as error:
        return unavailable(f"Ollama not reachable at {base_url} ({type(error).__name__})")
    try:
        version_reply.raise_for_status()
        tags_reply.raise_for_status()
        version = str(version_reply.json()["version"])
        names = {m["name"] for m in tags_reply.json()["models"]}
        if len(_version(version)) < 2:
            raise ValueError(f"version {version!r}")
    except Exception as error:
        return unavailable(f"unexpected reply from {base_url} ({type(error).__name__}: {_one_line(error, 80)})")
    if _version(version) < MIN_OLLAMA:
        return unavailable(f"Ollama {version} is too old; decision models need 0.35+")
    if not _has_model(names, model):
        return unavailable(f"model {model} not pulled; run: ollama pull {model}")
    return {"available": "yes", "model": model, "reason": f"Ollama {version}"}


def read_text(path):
    """UTF-8 with or without BOM, or UTF-16 with BOM (what Windows PowerShell 5.1 writes)."""
    with open(path, "rb") as f:
        data = f.read()
    if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return data.decode("utf-16")
    return data.decode("utf-8-sig", errors="replace")


def block(operation, result=None, error=None):
    lines = ["STATUS: ERROR" if error else "STATUS: OK", "RESULT:", f"- operation: {operation}"]
    lines += [f"  {key}: {_one_line(value, 400)}" for key, value in (result or {}).items()]
    lines.append("ERRORS:")
    if error:
        lines.append(f"- {operation}: {_one_line(error, 400)}")
    return "\n".join(lines)


def main(argv=None, transport=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="operation", required=True)
    for name in ("health", "ask"):
        op = sub.add_parser(name)
        op.add_argument("--provider", choices=sorted(PROVIDERS),
                        default=os.environ.get("JEV_PROVIDER") or DEFAULT_PROVIDER)
        op.add_argument("--model")
        op.add_argument("--base-url")
        if name == "ask":
            op.add_argument("--spec", required=True)
            source = op.add_mutually_exclusive_group(required=True)
            source.add_argument("--state-file")
            source.add_argument("--state-json")
    args = parser.parse_args(argv)
    if args.provider not in PROVIDERS:  # a bad JEV_PROVIDER value bypasses argparse choices
        print(block(args.operation, error=f"unknown provider {args.provider!r}; use one of {sorted(PROVIDERS)}"))
        return 0
    base_url, model = resolve_target(args.provider, args.base_url, args.model)
    target = {"base_url": base_url, "model": model, "provider": args.provider, "transport": transport}

    if args.operation == "health":
        print(block("health", health(**target)))
        return 0
    try:
        spec = validate_spec(json.loads(read_text(args.spec)))
        if args.state_file:
            state = {spec.get("state_key", "text"): read_text(args.state_file)}
        else:
            state = json.loads(read_text(args.state_json))
            if not isinstance(state, dict):
                raise SpecError("--state-json must hold a JSON object")
    except (OSError, ValueError) as error:
        print(block("ask", error=f"{type(error).__name__}: {error}"))
        return 0
    print(block("ask", ask(spec, state, **target)))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
