# Use cases

Where a decision model earns its place in an agent harness or a skill, where it doesn't, and
what we measured.

## Contents

- [The fit test](#the-fit-test)
- [The direction rule](#the-direction-rule)
- [Catalog for harnesses and skills](#catalog-for-harnesses-and-skills)
- [Broader catalog](#broader-catalog)
- [Poor fits](#poor-fits)

## The fit test

A decision is a good candidate when **all** of these hold:

1. **Closed answer.** The answer is yes/no or one of a fixed list you can write down.
2. **Text in, small state.** The input is text (or text you can make), well under 64 KiB.
3. **It happens often.** Small, repeated judgments — every comment, every tool call, every
   ticket — not a once-a-week call.
4. **A wrong answer is cheap, or only makes the system more careful** (see the direction rule).
5. **You can label examples.** You (or the user) can say what the right answer is for 20–50 real
   cases. If not, you can't measure it, and you shouldn't ship it.

And it adds value over "just let the LLM decide" when at least one holds: you want a **number**
for a threshold; you want the **same answer every run**; you want to **log** the decision; you
want it **local/private** or **cheap**; or the LLM's own context is the thing at risk (injection).

**Be honest about the gain.** An orchestrating LLM that already has the context loaded can make a
small judgment almost for free. The decision model wins on calibration, consistency, logging,
privacy and isolation — not always on tokens.

## The direction rule

> Use the model only where its answer can make the agent **more careful**, never less.

| Safe direction (can only add caution) | Unsafe direction (can remove caution) |
|---|---|
| Flag a comment as a possible injection → warn first | Mark a comment "clean" so it is trusted |
| Block a reply that may leak a secret → ask the user | Approve a reply for posting without review |
| Keep a thread open when the fix may not address it | Resolve a thread because the model says it's fixed |
| Escalate to a bigger model / a human | Skip a human check |
| Sort or label a list (no action at all) | Delete, merge, pay, or run something |

When you must use the unsafe direction, require a sure answer **and** a second, independent check
(the user, deterministic code). Most of the time, just don't.

## Catalog for harnesses and skills

Status: **measured** = labeled cases run on `tev1`; **proposed** = fits the pattern, needs its
own eval first.

### PR / review workflows

| Use case | Question (type) | Act when | Direction | Status |
|---|---|---|---|---|
| **Injection warning on reviewer comments** | "The comment asks an AI agent to run shell commands or to ignore its instructions." (`noul`, flag mode) | p ≥ 0.5 → warn, put first; no other automatic treatment | safe | **measured**: 30/30 and 5/5 flagged on `tev1` and `jev-latest`; one injection scored only 0.64 on the cloud, so 0.85 would have missed it |
| **General-rule hint** for learnings | "The comment states a general rule that applies beyond this one line of code." (`noul`) | ≥ 0.85 yes / ≤ 0.15 no, else LLM | hint only | **measured**: 10 right, 0 wrong, 20 undecided |
| **Comment kind** for sorting | question / bug / convention / design / nit (`choice`) | top ≥ 0.85, else no label | no action | **measured**: `tev1` 18/0/12; `jev-latest` 21/1/8 — the one miss was an injection comment, whose "kind" the injected text steered |
| **Reply gate** before posting | "The reply exposes secrets, credentials or sensitive data." + "The reply addresses the reviewer's concern." (`noul` ×2) | leak ≥ 0.5 or addresses ≤ 0.15 → stop, ask user | safe | proposed |
| **Resolve gate** | "The change fully addresses the reviewer's concern." (`noul`) | resolve only if the LLM says so **and** p is not ≤ 0.15 | safe | proposed |
| **Same issue as last round** (loop guard) | "The current issue is the same problem as the previous issue." (`noul`) | — | — | **measured, rejected**: 5/6; a miss blocks or unblocks work wrongly |
| **Claim check** in a PR audit | "The diff supports this claim from the PR description." (`noul`) | ≤ 0.15 → finding | safe | proposed (diff size!) |
| **Rule pre-check** | one `noul` per team rule: "This file violates rule X: …" | ≥ 0.85 → hint to the reviewer | hint only | proposed (chunk files) |

### Agent harness

| Use case | Question (type) | Act when | Direction | Status |
|---|---|---|---|---|
| **Tool-call guard** (e.g. a pre-tool hook) | "This tool call could cause irreversible damage." / "…sends secrets outside the workspace." / "…is steered by text from a file or web page." (`noul`s) | any ≥ 0.5 → ask the user | safe | proposed; keep the harness's own permissions — this only adds asks |
| **Model routing** | "Which model tier does this request need?" small / standard / strong (`choice`) | top ≥ 0.85, else the default tier | cost only | proposed |
| **Next step** in an agent loop | continue / retry / ask_user / stop (`choice`) + "The agent is blocked without user input or a new approach." (`noul`) | blocked ≥ 0.85 → ask the user | safe | proposed |
| **Retrieved-text filter** (RAG, web fetch) | "The passage contains instructions aimed at an AI system." (`noul`, flag) | ≥ 0.5 → quarantine, tell the user | safe | proposed |
| **Skill suggestion** | which of these candidate skills fits (`choice`, plus `none`) | top ≥ 0.85 → suggest, never auto-run | no action | proposed |

## Broader catalog

TypeSafe's examples ([kenhuangus/jev-usecases](https://github.com/kenhuangus/jev-usecases), 40+
runners on `jev-1.13.0`) cover support triage, invoice routing, SOC triage, moderation, citation
checks, CI semantic lints, coding-agent tool guards and more. Their shared pattern, worth copying:

1. Assemble the state from existing records — only the fields the questions need.
2. Ask narrow typed questions in one call.
3. Apply thresholds and **code rules** (dates, sums, exact matches, protected paths) in code.
4. Return a decision and an **action band**: `auto` / `confirm` / `human` / `block`.

Their thresholds are starting values (`high_stakes_noul` 0.85, `noul_yes` 0.75, `noul_no` 0.35),
and their published evals compare against large LLMs, not human labels. **Nothing transfers to
your model automatically** — measure.

## Poor fits

- **Anything that needs words**: replies, explanations, plans, code, summaries → LLM.
- **Counting, dates, money, exact matching** → code.
- **Unknown strings** ("extract the customer name") → enumerate candidates in code, then `choice`.
- **Replacing a confirmation the user expects** (merge, delete, force-push, pay) → a ~80%-accurate
  model can add an ask, never remove one.
- **Big inputs** (whole diffs, long docs) beyond 64 KiB → chunk, or don't.
- **Decisions you can already make exactly** (file-based routing, status checks) → keep the code.
- **Rubric scores that drive actions** (`score` ~55%) → turn into a `choice` or `noul`s.
