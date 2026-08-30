---
name: feed-second-brain
description: >-
  Capture knowledge into the user's second brain at SECOND_BRAIN_PATH. Reads
  AGENTS.md / CLAUDE.md in that directory for write conventions, then creates
  or updates files from the invocation prompt or by asking what to capture.
  Use when the user invokes /feed-second-brain, feed-second-brain init, or asks
  to save notes, capture learnings, or feed their second brain.
disable-model-invocation: true
license: MIT
metadata:
  author: josemarcilio
  version: "0.2.1"
---

# Feed Second Brain

Write into the second-brain directory at `SECOND_BRAIN_PATH`, following that vault's own agent instructions.

## Modes

| Invocation | Action |
| --- | --- |
| `/feed-second-brain` | Capture workflow (below) |
| `/feed-second-brain init` | One-time machine setup — [init.md](init.md) |

## Init (`/feed-second-brain init`)

Run [init.md](init.md): installs **soft** capture reminders for **all local agents** on this machine (Claude + Cursor). No blocking hooks.

1. Require valid `SECOND_BRAIN_PATH` ([setup.md](setup.md) if missing).
2. Run `scripts/init.ps1` (Windows) or `scripts/init.sh` (Unix).
3. Ask user to paste the **one-liner** from `~/.cursor/feed-second-brain/user-rule.txt` into **Cursor → Settings → Rules → User Rules** (once). Full triggers live in `reminder.md`; Claude gets the full block in `~/.claude/CLAUDE.md`. See [init.md](init.md).

## Capture workflow

```
Task progress:
- [ ] 1. Resolve SECOND_BRAIN_PATH
- [ ] 2. Read AGENTS.md / CLAUDE.md
- [ ] 3. Decide payload (prompt vs ask)
- [ ] 4. Write files under the vault
- [ ] 5. Summarize what was written
```

### 1. Resolve path

1. Read env `SECOND_BRAIN_PATH`.
2. If unset, empty, or not an existing directory → stop. Help the user set it via [setup.md](setup.md) or run **init** after path is set. Do not invent a path.
3. Treat that absolute path as the only write root for this skill.

### 2. Read vault instructions

In `$SECOND_BRAIN_PATH`, read (prefer both when present):

| File | Role |
| --- | --- |
| `AGENTS.md` | Primary write / layout rules |
| `CLAUDE.md` | Same for Claude-oriented vaults |

On conflict, prefer `AGENTS.md`. Follow those files for folder layout, naming, frontmatter, indexes, and linking. Discover structure from the repo — stay generic in reminders.

If neither exists, ask once how notes should be structured before writing.

### 3. Decide what to capture

- **Invocation includes instructions** (text after `/feed-second-brain` or an explicit payload) → use that as the content to capture. Shape it to vault rules; ask only for missing critical fields.
- **Invoked with no instructions** → use conversation context as candidates and ask the user what to fill (topic, decision, link, excerpt, etc.). Do not dump the whole chat unless they ask.

### 4. Write

1. Create or update files **only** under `$SECOND_BRAIN_PATH`.
2. Obey vault `AGENTS.md` / `CLAUDE.md`.
3. Do not commit unless the user explicitly asks.
4. Reply with paths written and any open follow-ups.

## Setup

Persistent `SECOND_BRAIN_PATH`: [setup.md](setup.md).  
Machine-wide soft reminders: [init.md](init.md).
