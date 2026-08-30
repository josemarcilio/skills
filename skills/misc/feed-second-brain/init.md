# feed-second-brain init

One-time (idempotent) setup on **this machine** for **all local agents**: soft capture reminders + `SECOND_BRAIN_PATH` wiring. No blocking hooks.

## Layered setup (what actually works)

| Layer | Target | Role |
| --- | --- | --- |
| **Claude** | `~/.claude/CLAUDE.md` | Full reminder — reliable in Claude IDE + CLI |
| **Cursor** | `~/.cursor/feed-second-brain/reminder.md` | Source of truth for Cursor nudges |
| **Cursor** | User Rules (one-liner) | Points agent at `reminder.md` — IDE + likely CLI (account sync) |
| **Cursor** | `sessionStart` hook | Injects `SECOND_BRAIN_PATH` env only — not reminder text |
| **Capture** | `/feed-second-brain` skill | Explicit write; reminders never auto-write |

Do **not** rely on User Rules alone for CLI-only workflows. Claude CLI is covered by `CLAUDE.md`. Cursor CLI should get the same User Rule when signed into the same account; if nudges miss, invoke `/feed-second-brain` manually after meaningful CLI sessions.

## When to run

User invokes **`/feed-second-brain init`** or asks to initialize second-brain reminders.

## Prerequisites

1. **`SECOND_BRAIN_PATH`** must point to an existing directory (vault root).
2. If missing, run [setup.md](setup.md) path scripts first, or pass `-Path` / first arg to the init script.

## Run init

**Windows (PowerShell):**

```powershell
& "$env:USERPROFILE\.cursor\skills\feed-second-brain\scripts\init.ps1"
# or from repo:
.\scripts\init.ps1 -Path "G:\second-brain"
```

**Unix:**

```bash
~/.cursor/skills/feed-second-brain/scripts/init.sh "/path/to/second-brain"
```

## What init installs

| Target | Action |
| --- | --- |
| `~/.claude/CLAUDE.md` | Merge [templates/reminder-block.md](templates/reminder-block.md) (replace if markers exist) |
| `~/.cursor/feed-second-brain/reminder.md` | Full reminder text — Cursor source of truth |
| `~/.cursor/feed-second-brain/user-rule.txt` | **One-liner** to paste into **Cursor → Settings → Rules → User Rules** |
| `~/.cursor/hooks.json` + hook script | `sessionStart` injects `SECOND_BRAIN_PATH` into agent env (merge, do not overwrite unrelated hooks) |
| `~/.cursor/feed-second-brain/installed.json` | Records init version and path |

## Cursor User Rules (manual once)

Cursor User Rules live in the UI (**Settings → Rules → User Rules**). Init cannot write there programmatically.

After the script runs:

1. Open **Settings → Rules → User Rules**.
2. If this line is not already present, append the contents of `~/.cursor/feed-second-brain/user-rule.txt`:

```text
When wrapping up durable work, read ~/.cursor/feed-second-brain/reminder.md and softly suggest /feed-second-brain if worth capturing. Never write to the vault unless the user invokes that skill.
```

The User Rule stays short; the agent reads the full triggers and skip rules from `reminder.md` when relevant.

## Coverage by agent

| Agent | Reminder | Path / capture |
| --- | --- | --- |
| Claude IDE + CLI | `~/.claude/CLAUDE.md` | `/feed-second-brain` |
| Cursor IDE | User Rule → `reminder.md` | `/feed-second-brain` + env hook |
| Cursor CLI | Same User Rule (account sync) | `/feed-second-brain` + env hook |

User Rules apply to **Agent (Chat)**, not Tab or Cmd+K. Cloud agents use repo rules only, not local `~/.claude/` or `~/.cursor/`.

## Agent checklist after init

```
- [ ] Script exited 0
- [ ] SECOND_BRAIN_PATH verified
- [ ] ~/.claude/CLAUDE.md contains feed-second-brain markers
- [ ] User pasted one-liner from user-rule.txt into Cursor User Rules (once)
- [ ] Tell user: /feed-second-brain to capture; reminders are soft only
```

## Re-run / uninstall

- **Re-run init** — safe; replaces marked blocks and refreshes `reminder.md` / `user-rule.txt`.
- **Uninstall** — remove markers from `~/.claude/CLAUDE.md`, delete `~/.cursor/feed-second-brain/`, remove the User Rules line, remove `sessionStart` hook entry from `~/.cursor/hooks.json` if added by this skill.

## Limits

- **Local only** — cloud agents do not read your machine's `~/.claude/` or `~/.cursor/`.
- **Soft only** — no `Stop` / `SessionEnd` blocking hooks.
- **No global `~/.cursor/rules/`** — not auto-loaded across projects; use User Rules + `reminder.md` instead.
