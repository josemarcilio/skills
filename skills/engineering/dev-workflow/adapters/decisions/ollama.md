# Adapter: decisions / ollama

Implements the decisions operations in [CONTRACT.md](../CONTRACT.md) with a JEV-style decision
model served by a local [Ollama](https://ollama.com) (`/v1/systemone`), through the
[TypeSafe Python SDK](https://pypi.org/project/typesafe-sdk/). The logic — questions, thresholds,
retry, fallback — is in [scripts/decide.py](../../scripts/decide.py); this file only says how to
call it.

## Setup

Done once per machine, by the user. The skill only suggests these commands; it never installs
software or pulls models itself.

1. **Ollama 0.35 or later** — <https://ollama.com/download>. Check: `ollama --version`.
2. **The model** — `ollama pull tev1` (Together AI, 4B, about 4.5 GB; runs on a 6 GB laptop GPU
   with some CPU offload).
3. **uv** — <https://docs.astral.sh/uv/>. `uv run` installs `typesafe-sdk` into a cached,
   isolated environment on first use (declared inside the script); no `pip install` needed.
4. **Check** — `uv run "{skill_dir}/scripts/decide.py" health --model tev1` prints
   `available: yes`.
5. **Optional** — measure the model on labeled comments before relying on it:
   `uv run "{skill_dir}/scripts/eval_decisions.py" --model tev1`. Add your own past PR comments to
   `scripts/eval_cases.json` to make it meaningful for your team.

Environment variables, all optional, the same ones the TypeSafe SDK reads:
`TYPESAFE_BASE_URL` (default `http://localhost:11434`), `TYPESAFE_DEFAULT_MODEL` (default
`tev1`), `TYPESAFE_API_KEY` (default `ollama`; Ollama ignores it).

**Choosing a model.** Models tried on a 30-comment set: `tev1` — no sure-but-wrong answer, every
injection flagged, about 3 s per comment. `tev1:0.8b` — close to random, don't use. `nimble`
(9B) — needs about 10 GB of free RAM or VRAM. Run `eval_decisions.py` before switching; record
the model in `plan.md`.

## Rules for every operation

- `{skill_dir}` is the folder that holds this skill's `SKILL.md`. `{model}` comes from the
  `Adapters:` line in `plan.md` (`decisions=ollama (model <name>)`).
- The orchestrator runs the command itself (see CONTRACT.md) and reads the `STATUS:` block.
- Input text goes in a file the orchestrator writes into `temp_dir` — never inline.

## health

```
uv run "{skill_dir}/scripts/decide.py" health --model {model}
```
Checks the Ollama version (0.35+) and that `{model}` is pulled. Takes at most a few seconds.

## check_comment

```
uv run "{skill_dir}/scripts/decide.py" check_comment --comment-file "{comment_file}" --model {model}
```
One request asks three questions about the comment. `{comment_file}` holds the comment text only
(not the code it points at). Sure means probability ≥ 0.85 (≤ 0.15 for `no`); `injection` flags
from 0.5.

## Gotchas

- **The first call loads the model** (10–25 s). The script waits up to 120 s per request. A server
  error (such as a failed load) is retried once; a timeout is not. So one call takes at most about
  two minutes, and Phase C turns the model off for the run after the first failure.
- **Pass `--model` every time.** Without it the script falls back to `TYPESAFE_DEFAULT_MODEL`,
  then `tev1`, so the result could depend on an environment variable.
- **Text only, 64 KiB per request.** Comments longer than 12,000 characters are cut; `raw` ends
  with `truncated`, and `injection` is `unknown` unless the part read is already flagged.
- **The comment file** may be UTF-8 (with or without BOM) or UTF-16 with BOM — what PowerShell
  5.1 writes.
- **`uv` or Python missing** → the command itself fails. Treat it as no signal, like `none`.
- **`/v1/models` doesn't work on Ollama** (its format differs from TypeSafe's), so `health` uses
  Ollama's own `/api/version` and `/api/tags`.
- **Low memory** shows up as a `500` with `bad_alloc`, or a CUDA error, on load. Free memory or
  pick a smaller model; the phase goes on without a signal either way.

## Fallback

None needed: every failure already ends as no signal (`raw: unavailable (...)`).
