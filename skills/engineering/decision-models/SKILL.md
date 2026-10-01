---
name: decision-models
description: Design, evaluate and wire JEV-style decision models (typed AI decisions with probabilities — TypeSafe Jev, Ollama's /v1/systemone, models like tev1 and jev-latest) into agent harnesses, skills and apps. Covers what they are, which decisions fit (routing, guards, injection flags, triage, verification) and which don't, a tested never-fail Python client with thresholds, an eval runner on labeled cases, and the optional-adapter pattern for skills and hooks. Use this whenever someone wants to add a classifier, gate, guardrail, router, prompt-injection check, yes/no or multiple-choice judgment to an agent, skill or workflow, asks "could a small/local model decide this instead of the LLM", mentions Jev, System One, TypeSafe, decision models, typed decisions or Ollama decision models — even if they don't name decision models explicitly.
---

# Decision models

A decision model answers **closed, typed questions** about some text — yes/no, one of a list, a
level on a rubric — and returns **probabilities** instead of prose. Your code applies thresholds
and decides what to do. They are a small, fast, cheap complement to an LLM: the LLM writes, the
decision model checks, sorts and warns.

This skill packages what was learned building real guards into an agent skill: what works, what
failed, the safety rules, and code you can reuse.

## The five rules

1. **A signal, never a verdict.** The model sorts, warns, hints or asks for caution. The agent,
   the user or deterministic code makes the call.
2. **Only in the safe direction.** Act on an answer only when it makes the system *more careful*
   (warn, ask, keep open, escalate). Never let it remove a check.
3. **Thresholds live in code.** Below "sure" (default 0.85 / 0.15) the answer is `undecided` and
   the caller judges as if there were no model.
4. **Never fail the caller.** Server down, model missing, timeout, bad reply → "no signal",
   exit 0, work goes on. Check health once per run; stop calling after the first failure.
5. **Measure before shipping.** Label 20–50 real cases per question and run the eval. Ship only
   questions with no sure-but-wrong answers (or an acceptable cost).

Why rule 2 matters so much: the text being judged is often written by outsiders (PR comments,
tickets, web pages), and it can try to steer the judge too. A decision model can raise an alarm;
it cannot clear text as safe.

## How to work

Pick the path that matches the request:

| The user wants to… | Do this |
|---|---|
| understand decision models, compare to LLMs, pick a model | read [references/what-are-decision-models.md](references/what-are-decision-models.md) and answer |
| know *where* a decision model would help in their skill, harness or app | read [references/use-cases.md](references/use-cases.md); read their code/steps; run each candidate through the fit test and the direction rule; recommend 2–3, say what you'd skip and why |
| call a decision model from code | read [references/implementing.md](references/implementing.md); prefer `scripts/jev.py` with a spec file; write tests with a mock transport |
| add decision signals to a skill or hooks | read [references/in-skills.md](references/in-skills.md) and follow its step-by-step and checklist |
| check whether a model is good enough | write a spec + labeled cases, run `scripts/eval.py`, report right / WRONG / undecided per question |

Before recommending anything, ask yourself honestly whether the decision model adds value over
the LLM that is already running: calibrated numbers, the same answer every run, a log, privacy,
or isolation from untrusted text. If none apply, say so.

## Bundled files

| File | What it is |
|---|---|
| `scripts/jev.py` | Never-fail CLI and library: `health` and `ask --spec … --state-file/--state-json …`; providers `ollama` (default, local) and `typesafe` (cloud, `TYPESAFE_API_KEY`). Prints a `STATUS:` block, always exits 0. |
| `scripts/eval.py` | Runs labeled cases through the same thresholds; prints right / WRONG / undecided and MISSED flags. |
| `scripts/test_jev.py` | Unit tests with a mock transport (no model needed): `uv run scripts/test_jev.py`. |
| `examples/pr-comment.spec.json` | A worked spec: injection flag, general-rule hint, comment kind. |
| `examples/pr-comment.cases.json` | 30 labeled PR comments for it (5 injections). |

Quick start (local):

```
ollama pull tev1
uv run "<skill_dir>/scripts/jev.py" health --model tev1
uv run "<skill_dir>/scripts/eval.py" --spec "<skill_dir>/examples/pr-comment.spec.json" --cases "<skill_dir>/examples/pr-comment.cases.json" --model tev1
```

`uv run` installs the `typesafe-sdk` dependency declared inside each script. Suggest setup
commands to the user; don't install software, pull models or create keys yourself — they cost
disk, memory or money. Never put an API key in a command line, a file in the repo, or the chat.
