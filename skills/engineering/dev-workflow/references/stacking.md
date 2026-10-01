# Stacked PRs

Optional PR mode, chosen once at the start of Phase A. Instead of one PR for the whole item, each
task becomes its own small PR, stacked on the one below it:

```
target ← L1 (T1) ← L2 (T2) ← L3 (T3)
```

Each layer PR targets the branch below it, so its diff shows only that task (a PR's diff is its
branch minus its base, and the base already holds the lower layers). Reviewers read small diffs,
bottom-up, while later layers are still being built. Layers merge bottom-up into the target
branch; after each merge the next PR is retargeted to the target branch and still shows only its
own layer. Based on GitHub's
[stacked PRs guide](https://docs.github.com/en/copilot/tutorials/stack-ai-generated-code-in-pull-requests).

`plan.md` records `PR mode: single | stacked`. Missing line → `single`. Every rule in the phases
marked **Stacked** applies only in this mode; everything else applies to both.

## When to offer it

Ask at Phase A step 0. Recommend `stacked` when the plan will likely produce three or more tasks,
or one PR would be too big to review in one sitting. Recommend `single` for one or two small
tasks. Tell the user the costs before they choose:

- Fixing a lower layer rewrites the layers above it, so they are **force-pushed** (with lease).
  Stacked mode needs a standing yes for that, recorded in `plan.md` (`Force-push:` line). No yes →
  use `single`.
- With the `squash` or `rebase` merge strategy, every merge also restacks the layers above. With
  `merge`, it doesn't. If the repo dismisses stale approvals on push, a restack can reset the
  approvals of the layers above.
- Every layer lands in the target branch as soon as it merges — the feature arrives in pieces.
  Each layer must be safe to ship alone (INVEST tasks already are).
- More PRs to track, one per task.

## Layers are INVEST tasks

- One layer = one task = one PR. Tasks stay vertical slices (planner rules unchanged). Don't split
  by technical layer (model / API / UI / tests), even though generic stacking guides do.
- The stack order is a **review order**, not a dependency. The planner proposes it: shared or
  riskiest code first, so the most-reused code is reviewed first.
- Because tasks are independent, reviewers can review layers in parallel. Merging stays bottom-up.

## Layout on disk

Stack branches never hold the working notes: the stack worktree switches branches all the time,
and the bottom layer merges first. The notes live on a separate **notes branch** that never gets a
PR.

```
<repo>/.agents/dev-workflows/<item-id>/worktrees/
├── stack/     one worktree, switched between the layer branches
└── notes/     the notes branch; plan.md and handoffs/ live here
```

```
notes worktree/.agents/dev-workflows/<item-id>/
├── plan.md
└── handoffs/
    ├── <task-id>.md             one per task, as in single mode
    ├── learnings.md
    └── L<n>/                    one folder per layer PR
        ├── pr-description.md    this PR's managed block, as last pushed
        ├── pr-audit.md
        └── pr/<thread-id>.md    this PR's threads
```

- **Notes branch**: from the target branch, named by the project's pattern with the description
  `<item-id>-dev-workflow-notes`. Pushed like any branch, never opened as a PR, deleted in Phase D.
- **Layer branches**: the project's pattern with the description `<item-id>-l<n>-<task-slug>`
  (default `<item-id>-l<n>-<kebab-task-title>`). Verify each name right after creating it.
- Commit notes in the notes worktree, code in the stack worktree. Never copy notes into a layer
  branch.
- Needs git 2.38 or newer (`rebase --update-refs`). Older → stop and tell the user.

## Layer PR titles

Every layer PR title shows the parent item's type, the layer, and the task title, so a PR list
shows the stack order at a glance.

- Default, when the project has no PR title pattern:
  `<work-item-type> <item-id>: L<n> — <task title>`, for example
  `Story 1234: L2 — Add retry policy to payment client`. `<work-item-type>` is the parent item's
  `type` from `get_item` (or the type it was created with), as the tracker spells it.
- The project has a pattern → use it, and put `L<n> — ` right before the task title. If the
  pattern already holds the item type, don't add it twice.
- Use `L<n>`, never `<n>/<total>`: layer numbers never change (new layers go on top, built layers
  are never reordered), so titles never need renaming.
- Record the resolved pattern in `plan.md` (`PR:` line).

## Operations

Git commands run in the stack worktree, by the orchestrator — rebases can need judgment. PR work
still goes through the cli-runner and the code-host adapter.

### Start a layer

`L1`: Phase A creates the stack worktree on it. `L<n>` for n > 1: `git switch <branch-(n-1)>`,
then `git switch -c <branch-n>`. Record branch and base in the Stack table first.

### Open a layer PR

After the layer's first push (a PR needs at least one commit): cli-runner `create_draft_pr` with
`source_branch` = the layer branch, `target_branch` = the layer below (the target branch for the
bottom open layer), `item_ids` = the parent item **and** this layer's task. Title: see Layer PR
titles below. Then `link_stack` with every open layer's PR, bottom first —
`status: unsupported` is fine. Then update the Stack section of the other open layers'
descriptions (see Descriptions).

### Restack after a lower layer changed

A commit landed on layer `L<k>` (a PR-comment fix, an audit fix):

1. Clean tree required. A layer mid-build → finish the current seam and commit it first.
2. `git fetch origin`. For every layer above `L<k>`: `git rev-list --count <branch>..origin/<branch>`
   must be `0`. Anything else → someone else pushed there; stop and ask.
3. In the fixed task's handoff, note each layer's sha (`git rev-parse <branch>`) as `before
   restack`.
4. `git switch <top-branch>`, then `git rebase --update-refs <branch-k>`. This replays every layer
   above `L<k>` and moves their branch refs in one run.
5. Conflict → resolve it only when the right result is obvious; otherwise `git rebase --abort` and
   ask the user.
6. For each moved layer: `git range-diff <old-parent-sha>..<old-sha> <parent-branch>..<branch>`.
   Only `=` pairs → its own diff didn't change. Anything else → that layer changed: run its
   verification gate and re-audit it (Phase B → PR audit, for that layer).
7. Run the project's test and lint commands on the top branch (it contains every layer).
8. `git push --force-with-lease origin <branch-k> <every-moved-branch>`.

### After a lower layer merged

Phase D merged `L<k>`, the bottom open layer:

1. cli-runner: `set_pr_target` on `L<k+1>`'s PR → the target branch. Do this **before** deleting
   `<branch-k>`: on some hosts, deleting a PR's target branch closes or breaks that PR.
2. Merge strategy `merge` → no restack; the next PR already shows only its own layer.
3. `squash` or `rebase` → the target branch holds the same changes as new commits. Restack:
   `git fetch origin`, the check in Restack step 2, `git switch <top-branch>`,
   `git rebase --update-refs --onto origin/<target-branch> <branch-k>`, then Restack steps 5–8
   (push only the moved branches).
4. Delete `<branch-k>` on the remote only if the user agreed in Phase D:
   `git push origin --delete <branch-k>`.
5. Stack table: `L<k>` → `merged`; `L<k+1>` base → the target branch. Update the Stack section of
   the open layers' descriptions.

## Descriptions

Each layer PR has its own managed block ([templates/pr-description.md](../templates/pr-description.md),
stacked variant), recorded in `handoffs/L<n>/pr-description.md` and updated by the normal
procedure ([conventions.md](conventions.md) → PR description). Its Stack section lists every layer
bottom-up with PR link and state, and marks this PR. Update the other layers' Stack sections only
when a layer is added or merged.

## Rules

- Keep each fix in the layer that owns the code, then restack. Never fix a lower layer's code in a
  higher layer to skip a restack.
- Merge strictly bottom-up into the target branch. Never merge a layer into the layer below it,
  and never merge a layer whose base is not yet the target branch.
- Force-push only layer branches, only with `--force-with-lease`, only after the Restack step 2
  check, and only because `plan.md` records the user's yes. Never force-push the target branch or
  the notes branch.
- `link_stack` is the only `gh stack` command this skill runs. Never run the ones that restructure
  or merge (`modify`, `rebase`, `sync`, `merge`, `unstack`) for the user.
