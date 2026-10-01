# /// script
# requires-python = ">=3.10"
# dependencies = ["typesafe-sdk>=0.7.2,<0.8"]
# ///
"""Measure a decision model on labeled cases, through the same thresholds jev.py applies.

  uv run eval.py --spec <spec.json> --cases <cases.json> [--provider ollama|typesafe] [--model <name>]

cases.json:
  {"cases": [
     {"text": "...",                 # or "state": {...} for several fields
      "expect": {"<question>": true | false | "<option or level>"}}
  ]}
  noul expects true/false (yes/no, or flag/no in flag mode); choice an option; score a level name.
  Questions missing from "expect" are not scored for that case.

Per question it counts:
  right      sure and correct
  WRONG      sure and incorrect — the number that matters; the caller acts on it
  undecided  no sure answer — the caller judges on its own, as without a model
A flag-mode question that misses a real positive is listed as MISSED.
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jev  # noqa: E402


def expected(question, value):
    if question["type"] == "noul":
        if question.get("mode") == "flag":
            return "flag" if value else "no"
        return "yes" if value else "no"
    return str(value)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--cases", required=True)
    parser.add_argument("--provider", choices=sorted(jev.PROVIDERS), default=jev.DEFAULT_PROVIDER)
    parser.add_argument("--model")
    parser.add_argument("--base-url")
    args = parser.parse_args()
    args.base_url, args.model = jev.resolve_target(args.provider, args.base_url, args.model)
    target = {"base_url": args.base_url, "model": args.model, "provider": args.provider}

    spec = jev.validate_spec(json.loads(jev.read_text(args.spec)))
    cases = json.loads(jev.read_text(args.cases))["cases"]
    status = jev.health(**target)
    if status["available"] != "yes":
        print(f"{args.model}: {status['reason']}")
        return 1

    key = spec.get("state_key", "text")
    names = list(spec["questions"])
    counts = {n: {"right": 0, "WRONG": 0, "undecided": 0} for n in names}
    notes, times = [], []
    if args.provider == "ollama":
        jev.ask(spec, {key: "warm-up"}, **target)  # load the model so timings are fair
    for case in cases:
        state = case.get("state") or {key: case["text"]}
        start = time.time()
        result = jev.ask(spec, state, **target)
        times.append(time.time() - start)
        if result["raw"].startswith("unavailable"):
            print(f"stopped: {result['raw']}")
            return 1
        for name in names:
            if name not in case.get("expect", {}):
                continue
            q = spec["questions"][name]
            got, want = result[name], expected(q, case["expect"][name])
            if got in ("undecided", "unknown"):
                counts[name]["undecided"] += 1
            elif got == want:
                counts[name]["right"] += 1
            else:
                counts[name]["WRONG"] += 1
                label = "MISSED" if q.get("mode") == "flag" and want == "flag" else f"{got}!={want}"
                text = json.dumps(state, ensure_ascii=False)[:70]
                notes.append(f"{name} {label} [{result['raw']}]: {text}")

    print(f"{args.provider}/{args.model} on {len(cases)} cases, avg {sum(times) / len(times):.2f}s per request")
    width = max(len(n) for n in names)
    for name in names:
        c = counts[name]
        print(f"  {name:{width}}  right {c['right']:3}   WRONG {c['WRONG']:3}   undecided {c['undecided']:3}")
    for note in notes:
        print(f"  - {note}")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
