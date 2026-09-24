# Conventions

Rules every phase follows. Project rules (its `AGENTS.md` / `CLAUDE.md` / contributing docs)
always win over these defaults when they conflict.

## Discover, never assume

Branch pattern, target branch, PR title pattern, team, work-item types, area paths, states, test
and lint commands all vary per project. Look them up in this order, and record what you found in `plan.md`:

1. The repo's `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, and any doc they point to (a
   `docs/branching.md` or similar).
2. The tracker (`discover_conventions`), recent branch names (`git branch -r --sort=-committerdate`),
   recent PR titles.
3. Ask the user. Never guess a team or a branch pattern.

Default branch name only if the project has no rule: `<item-id>-<kebab-description>`.

## Worktree

- Path: `<repo-root>/.agents/dev-workflows/<item-id>/worktrees/<slug>`, where `<slug>` is the
  branch name with `/` replaced by `-`.
- Create: `git worktree add <path> -b <branch> <target-branch>` (after `git fetch`), or the
  harness's own worktree tool if it can take that exact path and branch.
- **Verify the branch name right after creating it** (`git -C <path> branch --show-current`)
  against the discovered pattern. Tool defaults (random or prefixed names) often don't match, and
  automation that parses branch names fails silently. Fix it before any commit.
- Hide worktrees from git with one line in `.git/info/exclude` (shared by all worktrees, never
  committed): `.agents/dev-workflows/*/worktrees/`. Never edit the project's `.gitignore` for this.
- First push: `git push -u origin <branch>`.
- `plan.md` and `handoffs/` are written **inside the worktree**, at the same relative path
  (`.agents/dev-workflows/<item-id>/...`), so they commit on the branch.
- Find an existing worktree with `git worktree list`.

## Paths in anything written or posted

Replace the user's home directory with `<user-home>`
(`C:\Users\jane\src\app` → `<user-home>\src\app`, `/home/jane/src/app` → `<user-home>/src/app`).
Applies to `plan.md`, handoffs, PR descriptions, replies, commit messages.

## Secrets

Never write tokens, keys, passwords, connection strings or personal data into any file this skill
creates, or into any payload. Refer to them by name ("the `API_KEY` env var"). The one exception
is the assignee's name or login, which the tracker needs and `plan.md` records.

## Payload files

Descriptions, replies and JSON bodies for the cli-runner go to the OS temp directory or the
harness's scratch directory (the `temp_dir` of the dispatch) — never into the repo. One exception:
`handoffs/pr-description.md` is the PR description's source of truth, so every update is a small
edit to it instead of a rewrite. Edits someone makes in the web UI are overwritten on the next
update — tell the user when you notice the description changed there.

## Handoffs

- Write so a fresh agent with no chat history can continue from the file + `plan.md` alone.
- Reference artifacts (plan, commits, PR, docs) by path or URL; don't copy their content.
- Short phrases, not paragraphs. One clear **Next step**.
- **Write the handoff before the side effect** (commit, push, reply, resolve). An interrupted run
  then still leaves a record of what was decided.

## Commits

- Scoped to one task (or one thread fix). Reference the task or item id the way the project does.
- Follow the project's message style and attribution rules; check `git log` for the pattern.
- Run the project's lint, format and tests before committing, unless the round touched no code.
- Never commit: `worktrees/`, payload files, secrets, generated files edited by hand.
- Never bypass hooks or signing.

## PR replies

- Every human thread gets a reply. Nobody is left without an answer.
- Short phrase statements, not paragraphs: "Fixed in `a1b2c3d` — null check moved to the parser."
  / "Kept as is: the retry is required by the upstream API (see docs/x.md)."
- Resolve a thread only when its concern is actually addressed. A disagreement or an open
  question gets a reply and stays open.
- Follow the user's own instructions for text meant for others (tone, no personal formatting).

## Confirm before

Completing/merging a PR, deleting branches or worktrees, force-pushing, changing tracker or CLI
configuration. Everything else in the flow runs without asking once the user started it.
