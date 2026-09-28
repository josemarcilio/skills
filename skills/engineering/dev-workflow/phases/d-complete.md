# Phase D — Complete

Only on an explicit user request ("complete the PR", "merge it"). Removes the working notes so
the final tree holds only the real work, then completes the PR.

**Exit:** PR completed; worktree removed if the user agreed.

**Stacked:** follow [Stacked completion](#stacked-completion) below instead of the steps.

## Resuming

If `plan.md` is gone but the branch has the cleanup commit, the values are still readable:
`git log --diff-filter=D --format=%H -1 -- .agents/dev-workflows/<item-id>/plan.md` gives the
commit; `git show <commit>^:.agents/dev-workflows/<item-id>/plan.md` gives the file. Confirm
again (step 3 — the earlier answers lived only in chat), then continue at step 6.

## Steps

1. **Pre-check.** cli-runner: `list_threads`. Any thread with a comment newer than its handoff's
   "Last seen", or with status `Needs user`, or with no handoff → tell the user and ask whether to
   continue anyway.

2. **Harvest learnings.** Run the [learnings harvest](e-learnings.md) — always, because the
   cleanup commit deletes the thread handoffs it reads. It only processes threads not harvested
   yet.

3. **Confirm.** Show: PR, target branch, merge strategy from `plan.md` (`squash`, `merge`, or
   `rebase` where the code-host adapter supports it), delete source branch yes/no. With `merge` (not `squash`), warn that the commits which added the notes stay in the
   target branch's history even though the final tree drops them. Completing a PR is hard to
   reverse — wait for an explicit yes.

4. **Final PR description.** Update the managed block without the "Working notes" section,
   keeping the Items, Tasks, Audit and Follow-up lines
   ([conventions.md](../references/conventions.md) → PR description → Update).

5. **Cleanup commit.** In the worktree, delete `.agents/dev-workflows/<item-id>/plan.md` and
   `.agents/dev-workflows/<item-id>/handoffs/`. `git status` must show only those deletions.
   Commit as `Remove dev-workflow working notes (<item-id>)`, adapted to the project's commit
   style, and push.

6. **Complete.** cli-runner: `complete_pr` with the confirmed options (`pr_id` from `plan.md`).
   Policy block → report the policy message; never bypass.

7. **Tidy.** Set the parent item to `done` (parent `state_map`) if the project closes items on
   merge and the tracker didn't already. Offer to remove the worktree (`git worktree remove
   <path>`) — and the learnings worktree once its follow-up PR is merged or closed — and, if no other worktrees remain under `.agents/dev-workflows/`, the
   `.git/info/exclude` line. Deleting only on a yes.

## Stacked completion

Layers merge one at a time, strictly bottom-up, into the target branch
([stacking.md](../references/stacking.md)). They can merge on different days: each run merges
from the bottom open layer up to where the user says to stop. There is no cleanup commit — the
notes never touched the layer branches.

**Resuming:** a layer in state `merging` → cli-runner `get_pr_status` on its PR. `completed` →
continue at step 5 for it. `open` → it didn't merge; start again at step 1.

1. **Which layers.** Ask how far: the bottom open layer only, or every approved layer in order.
2. **Pre-check** each chosen layer, bottom-up: cli-runner `list_threads` (the checks of step 1
   above, on `handoffs/L<n>/pr/`) and `get_pr_status`. The first layer not approved, or with
   unanswered threads the user doesn't wave through, is where this run stops.
3. **Harvest learnings** only when the chosen layers include the top open layer — the last
   chance, as the notes branch is deleted afterwards. Otherwise later layers may still get
   comments.
4. **Confirm once** for the whole run: the layers in order, the merge strategy, delete merged
   branches yes/no. With `squash` or `rebase`, warn that after each merge the layers above are
   restacked and force-pushed, which can reset their approvals where the repo dismisses stale
   reviews. Wait for an explicit yes.
5. **Per layer, bottom-up:**
   1. Final description: update that layer's managed block without the Working notes line.
   2. Set the layer's Stack state to `merging`; commit the notes.
   3. cli-runner: `complete_pr` with `delete_source_branch: false` — the next layer's PR still
      targets this branch. Policy block → report it, stop the run.
   4. stacking.md → After a lower layer merged (retarget, restack if needed, delete the branch if
      agreed, Stack table, other layers' Stack sections). Commit and push the notes.
6. **After the last layer:** set the parent item to `done` (as step 7 above). Offer to delete the
   notes branch (`git push origin --delete <notes-branch>`), then remove the stack and notes
   worktrees (and the learnings worktree once its PR is merged or closed), and the
   `.git/info/exclude` line if no other worktrees remain. Deleting only on a yes.
