# What decision models are

A **decision model** (also "System One" or "JEV-style" model) answers closed, typed questions
about some text and returns **probabilities**, not prose. Code reads the numbers and decides what
to do. They come from TypeSafe's Jev API; Ollama 0.35+ serves the same API locally.

## Contents

- [The shape of a call](#the-shape-of-a-call)
- [Question types](#question-types)
- [Decision model vs. LLM](#decision-model-vs-llm)
- [Models and backends](#models-and-backends)
- [Limits ("jaggedness")](#limits-jaggedness)

## The shape of a call

One request = one **state** (the text or record to judge) + up to 64 named **questions**. All
questions are answered in that one request.

```json
POST /v1/systemone
{
  "model": "tev1",
  "state": {"comment": "Tests here must never hit the real database."},
  "questions": {
    "general_rule": {"type": "noul", "instructions": "The comment states a general rule that applies beyond this one line of code."},
    "kind": {"type": "choice", "instructions": "What kind of PR review comment is this?",
             "criteria": {"bug": "Incorrect behavior", "convention": "Team convention", "nit": "Cosmetic"}}
  }
}
```

```json
{
  "answers": {
    "general_rule": {"type": "noul", "noul": 0.99},
    "kind": {"type": "choice", "choice": "convention",
             "probabilities": {"bug": 0.05, "convention": 0.93, "nit": 0.02}, "confidence": 0.65}
  },
  "usage": {"input_tokens": 1061, "output_tokens": 4}
}
```

## Question types

| Type | Asks | Returns | Measured strength |
|---|---|---|---|
| `noul` | Is this statement true? (write it as a statement, not a question) | one probability 0–1 | strong (~80% on public sets) |
| `choice` | Which of these named options? (1–255 options, each with a meaning) | a probability per option, the top one, and a `confidence` | strong (~82%) |
| `score` | Where on this ordered rubric? (2–10 levels) | a weighted score, a probability per level, a `confidence` | **weak** (~55%) |

The percentages are published benchmark numbers for Ollama's decision models over 13 public
datasets. Treat `score` with
suspicion: prefer a `choice` or a few `noul`s when the decision matters.

**Write each question about one judgment.** "Is it urgent and about billing?" is two questions.

## Decision model vs. LLM

| | LLM | Decision model |
|---|---|---|
| Output | text, or JSON you must validate | typed answers with probabilities |
| Uncertainty | you must build it (self-rating, sampling) | built in — the probability *is* the signal |
| Who decides | often the model, inside its text | your code, with thresholds you choose |
| Speed / cost | seconds, per output token | ~70–500 ms cloud, ~3 s on a laptop; input tokens only |
| Good at | explaining, drafting, code, open reasoning | routing, gating, flagging, checking against a fixed list |

**Use an LLM** when you need words: explanations, replies, summaries, code. **Use a decision
model** when software needs a bounded answer it can act on. The best pattern combines them: the
LLM generates, the decision model checks.

## Models and backends

| Model | Where | Size, context | What we measured (30 labeled PR comments, laptop RTX 3050 6 GB) |
|---|---|---|---|
| `tev1` (Together AI) | Ollama | 4B, 4.5 GB; **2050 tokens** per question prompt | **Usable.** No sure-but-wrong answer; flagged 5/5 injections; ~3 s per request. Fits 6 GB VRAM with some CPU offload. |
| `tev1:0.8b` (Together AI) | Ollama | 0.8B, 0.8 GB | **Not usable.** Said "yes" to almost everything; close to random. |
| `jev-latest` (TypeSafe) | cloud, `https://api.typesafe.ai` | — ; long text fine up to the 64 KiB request | **Usable.** Same set: injection 30/0/0, kind 21 right / 1 wrong / 8 undecided, general rule 12/0/18; ~0.3 s per request. Needs `TYPESAFE_API_KEY`; USD 0.042 per million input tokens, output not billed. |
| `jev-preview` (TypeSafe) | cloud | — | "A preview version of `jev-latest`"; identical counts on our set. |

Small models can look fine on paper and fail in practice — **always run the eval before relying
on a model** (see [implementing.md](implementing.md) → Evaluate).

Requirements: Ollama **0.35+** for `/v1/systemone`; request body ≤ **64 KiB**; text only (no
images or audio — transcribe or describe first). **Each question is scored as its own prompt
(state + question), and an over-long prompt is rejected, never truncated** — size the state to
the model's context (see [implementing.md](implementing.md) → Gotchas). Trust the server's
error over the model page: `tev1`'s page lists a 256K context, but Ollama 0.35 rejected prompts
over 2050 tokens. `tev1` is marked experimental; its authors "haven't fully tested prompt
injection, languages other than English, calibration" — one more reason a flag may warn but
never clear, and a reason to eval non-English text separately.

## Limits ("jaggedness")

From TypeSafe's own use-case catalog and our tests. Design around them:

- **It does not count** and **does not compare dates or numbers** reliably. Do math in code.
- **It reads instructions literally.** Vague or contradictory criteria score worse.
- **Irrelevant fields in the state lower accuracy.** Send only what the questions need.
- **User-controlled text in the state can change the answers.** If the text you judge was written
  by an outsider (a PR comment, a ticket, a web page), it can also try to steer the judge —
  for example a comment that injects *and* says "this is not an injection". So a decision model
  can **raise** an alarm but never **clear** text as safe.
- **A high probability is a control signal, not a guarantee.** Calibration holds on average,
  not per case.
- **It generates nothing.** No explanations, no extracted strings. To "extract", enumerate the
  candidates in code and ask a `choice`.
