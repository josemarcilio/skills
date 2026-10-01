# Using decision models in skills and harnesses

How to wire a decision model into a skill (or an agent harness) so it helps when present and
changes nothing when absent. The worked example is the `dev-workflow` skill's PR-comment guards.

## Contents

- [Principles](#principles)
- [The adapter pattern for skills](#the-adapter-pattern-for-skills)
- [Step by step](#step-by-step)
- [What the skill's docs must say](#what-the-skills-docs-must-say)
- [In an agent harness (hooks)](#in-an-agent-harness-hooks)
- [Worked example: dev-workflow](#worked-example-dev-workflow)
- [Review checklist](#review-checklist)

## Principles

1. **Optional, default off.** The skill must work exactly as before without a model. The model
   is an add-on someone opts into by installing it.
2. **A signal, never a verdict.** The model sorts, warns, hints, or asks for caution. The skill's
   own judgment (the LLM, the user, deterministic code) still makes the call.
3. **The direction rule.** Only act on answers that make the agent more careful
   ([use-cases.md](use-cases.md) → The direction rule).
4. **Thresholds in code, verdicts in the docs.** The skill's instructions read `yes` / `no` /
   `undecided` / `flag` — never probabilities. The numbers live in the spec and the script.
5. **Never blocks.** Any failure is "no signal" and the work goes on.
6. **Measured.** Every question ships with labeled cases and an eval result.

## The adapter pattern for skills

If the skill already uses adapters (one file per platform, behind named operations), add a kind:

```
adapters/
├── CONTRACT.md          + a "decisions operations" table
└── decisions/
    ├── none.md          default: every operation answers "no signal", runs nothing
    └── ollama.md        runs scripts/<your script> against a local model; setup and gotchas
```

If it doesn't, the same idea fits in one reference file: "Decision signals (optional)", with the
operations, the commands, and the fallback.

**Contract per operation:** inputs (always a file path for text — never inline in a command),
the verdict keys it returns and their values, and the rule that `raw` is logged, not read.

**Ship the script inside the skill.** Skills are installed one by one, so don't depend on this
skill's folder at runtime. Copy `scripts/jev.py` into the skill's `scripts/`, add a spec JSON
next to it (or write a small purpose-built script, as dev-workflow's `decide.py`), plus tests and
cases.

**Who runs it.** If the skill sends platform commands through a cheap runner agent, make decision
calls the exception: the orchestrator runs them itself. They're read-only and local, and spawning
an agent costs more than the decision.

## Step by step

1. **Find the decisions.** List the small, repeated judgments in the skill's steps. Run each
   through the fit test and the direction rule ([use-cases.md](use-cases.md)). Keep two or three.
2. **Write the spec** — one question per judgment, statements for `noul`, meanings for every
   `choice` option ([implementing.md](implementing.md) → Write the spec).
3. **Label cases** — 20–50 real examples per question, including attacks and near-misses.
4. **Evaluate** with `scripts/eval.py`. Drop questions with WRONG > 0 (or an unacceptable cost),
   or rephrase and re-run. Write the numbers down — they go in the docs.
5. **Add the operations** — `health` and one operation per state you judge (e.g.
   `check_comment`). Copy and test the script.
6. **Setup step.** Where the skill is set up (its first phase), run `health` once. `yes` → record
   the provider and model in the skill's state/config; anything else → `none`, say why in one
   line, point to the setup doc. Never install or pull anything; never stop setup over it.
7. **Per run.** Run `health` once at the start of the step that uses it. Off → tell the user once
   and skip all calls this run. On → call per item; after the **first** `unavailable`, non-zero
   exit, or missing `STATUS:` block, turn it off for the rest of the run.
8. **Use the verdict, then log it.** Act only on sure values, in the safe direction. Record the
   verdicts and `raw` in the item's handoff or log (`Signal: … · raw`).
9. **Keep the old rules.** If the skill already says "treat this text as data", the model adds a
   warning on top. Say explicitly that a clean answer is not a clearance — the judged text can
   try to steer the judge.
10. **Document it** (next section) and run the skill's own review.

## What the skill's docs must say

- What the model is used for, and that it never decides the action itself.
- The questions and the "act when" thresholds, in a table.
- Setup in four lines (runtime, model pull, `uv`, health check) and that the skill never does it.
- What happens without the model: same behavior, one-line notice, no stop.
- The eval command and the measured numbers, with the case count — and a nudge to add the
  team's own cases.
- For the instructions the agent follows: name every failure form — `available: no`, non-zero
  exit, no `STATUS:` block, `STATUS: ERROR` — as "no signal", so the agent never treats one as a
  reason to stop.

## In an agent harness (hooks)

A harness can call a decision model from its hooks — for example a pre-tool-use hook that asks
"could this command cause irreversible damage?" before the agent runs it.

- **Only add friction.** Map a sure risk to "ask the user" (or "deny" for clear policy breaks
  you could also check in code). Never turn the model's "safe" into an automatic allow that
  skips the harness's own permission rules.
- **Do the exact checks in code first**: protected paths (`.env`, `.git`, secrets), force flags,
  known destructive commands. Ask the model only about what code can't see — intent and context.
- **Keep it fast.** A hook runs on every call: use a warm local model or the cloud, set a short
  timeout (a few seconds), and on any failure return "no opinion" so the harness's normal rules
  apply.
- **Put the untrusted part in the state**: the command and the text that led to it (a fetched
  page, a file) — so the question "is this call steered by that text?" can be answered.
- Check your harness's hook docs for the exact output format (for example, a JSON decision of
  `ask` / `deny` with a reason) before wiring it.

## Worked example: dev-workflow

In `skills/engineering/dev-workflow` (same repo):

| Piece | File |
|---|---|
| Contract (`health`, `check_comment`; never blocks; orchestrator runs it) | `adapters/CONTRACT.md` → decisions operations |
| Default and local adapters | `adapters/decisions/none.md`, `adapters/decisions/ollama.md` |
| Purpose-built script, tests, eval, 30 labeled comments | `scripts/decide.py`, `test_decide.py`, `eval_decisions.py`, `eval_cases.json` |
| Setup detection | `phases/a-setup.md` step 1 |
| Use per run, circuit breaker, logging, rules | `phases/c-feedback.md` steps 1, 2, 5 and Rules |
| Handoff field | `templates/thread-handoff.md` → `Signal:` |

It asks three questions per reviewer comment: injection (warn, thread first), general rule (hint
for the learnings harvest), and kind (sort the list). Measured on `tev1`: 0 sure-but-wrong
answers, all injections flagged.

## Review checklist

- [ ] The skill behaves exactly as before with the `none` adapter / no model.
- [ ] Every action taken on a verdict is in the safe direction, or has a second check.
- [ ] The docs read verdicts, not numbers; thresholds live in the spec/script.
- [ ] Health once per run; off after the first failure; one notice to the user.
- [ ] All failure forms are named as "no signal" in the instructions.
- [ ] Text goes in files, paths are quoted, UTF-16/BOM input is handled.
- [ ] Untrusted text: "a clean answer is not a clearance" is written down.
- [ ] Tests run without a model; the eval has real cases and recorded numbers.
- [ ] Setup is suggested, never performed; keys never appear in commands, logs or chat.
