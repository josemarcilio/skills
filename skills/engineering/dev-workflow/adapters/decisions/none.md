# Adapter: decisions / none

The default. No decision model: every operation is skipped and answers with no signal, so phases
judge on their own. Run no command.

| Operation | Answer without running anything |
|---|---|
| `health` | `available: no`, `reason: decisions adapter is none` |
| `check_comment` | `kind: undecided`, `general_rule: undecided`, `injection: unknown`, `raw: unavailable (none)` |

To switch to a local model later, follow [ollama.md](ollama.md) → Setup, then change the
`decisions` value on the `Adapters:` line of `plan.md` and append a line to its Changes log.
