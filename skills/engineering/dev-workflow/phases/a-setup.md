# Phase A — Setup

From "start this work" to a linked item, child tasks, a worktree, `plan.md`, and a draft PR.

**Exit:** `plan.md` with `Setup: complete` committed on the branch, draft PR open → Phase B.

## Inputs — ask if missing, never guess

- **Plan / scope content**: from a prior grilling or spec session, a doc, or the user's own
  description. This skill does not create the plan. If there is none, say so and suggest the
  project's planning skill (for example a grilling or spec skill), then stop.
- **Item**: an existing work item id, or "create one".
- **Assignee**: who to assign items to (usually the user), in the tracker's format — a display
  name for Azure Boards, a login or `@me` for GitHub.
- **Team / owner**: only if the tracker or branch pattern needs it.

## Resuming

`plan.md` exists with `Setup: in progress` → skip every step whose result is already recorded
in it (item id, worktree, ticket ids, PR). Never create an item or PR that `plan.md` already
lists. Before step 6, cli-runner: `get_item` on the parent and match its `children` by title
against `pending` tickets — a stopped dispatch may have created some; record those ids instead of
creating them again.

No `plan.md` yet but the user started this work before → ask whether a parent item was already
created (step 3 always reports its id) before creating one.

## Steps

1. **Adapters and context.** Choose adapters ([CONTRACT.md](../adapters/CONTRACT.md) →
   "Choosing adapters"). cli-runner: `detect_context`. If not configured, stop and show the
   user the configure command from the adapter.

2. **Conventions.** cli-runner (tier `standard`): `discover_conventions` (sample = the given item,
   or ask the user for any recent item id in the same project) and `current_iteration`. Discover
   branch pattern, target branch, PR title pattern, merge strategy, test and lint commands per
   [conventions.md](../references/conventions.md).

3. **Parent item.**
   - **Already exists** (the user gave an id): don't create or edit it. cli-runner: `get_item` for
     its title, url and children. If it already has children, show them and ask whether to reuse
     them as tasks; reused ones go into the Tasks table with their ids, and the planner gets their
     titles in step 5 so it doesn't plan them again.
   - **Doesn't exist**: write the description and acceptance criteria in the format the adapter
     requires (Azure Boards: HTML). cli-runner: `create_parent_item`. Tell the user the new id right
     away — until step 4 it exists only in this chat.

4. **Worktree, branch, stub plan.** Per [conventions.md](../references/conventions.md) →
   Worktree: create it, **verify the branch name** (fix a wrong one before anything else), add the
   `.git/info/exclude` line. Then write `plan.md` from [templates/plan.md](../templates/plan.md)
   inside the worktree at `.agents/dev-workflows/<item-id>/plan.md`: `Setup: in progress`, header
   values from steps 1–3, Scope, Decisions. From here on, every result is written to `plan.md`
   before the next side effect.

5. **Tickets.** Spawn `planner` (tier `capable`, `mode: initial`) with the plan and repo root.
   Relay its questions to the user and its follow-ups back, until the user approves and the
   planner returns `status: final`. Write the Tasks table (ids `pending`) and one Tickets block
   per ticket into `plan.md`.

6. **Child tasks.** Per ticket write one description file: "what to build" plus an "Acceptance
   criteria" list. Dispatch **one** cli-runner step: `create_child_item` for every ticket still
   `pending`, in order. Check each `linked: yes`; re-dispatch only failures. Fill the ids in the
   Tasks table.

7. **Commit and push.** Commit `plan.md`; push with `git push -u origin <branch>`.

8. **Draft PR.** Fill [templates/pr-description.md](../templates/pr-description.md) into
   `handoffs/pr-description.md` (the PR description's source of truth from now on). cli-runner:
   `create_draft_pr` with that file and the **parent item id only** — child tasks are reached
   through the parent, so they are never linked to the PR. Title per the recorded pattern. If the
   code-host adapter links items through the description (GitHub), write the parent reference it
   asks for into the Items line first. Record the
   PR in `plan.md`, set `Setup: complete`, commit, push.

9. **Tell the user**: item and PR links, task list, worktree path. Next: Phase B.
