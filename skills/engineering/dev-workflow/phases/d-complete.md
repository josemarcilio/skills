# Phase D — Complete

Only on an explicit user request ("complete the PR", "merge it"). Removes the working notes so
the final tree holds only the real work, then completes the PR.

**Exit:** PR completed; worktree removed if the user agreed.

## Resuming

If `plan.md` is gone but the branch has the cleanup commit, the values are still readable:
`git log --diff-filter=D --format=%H -1 -- .agents/dev-workflows/<item-id>/plan.md` gives the
commit; `git show <commit>^:.agents/dev-workflows/<item-id>/plan.md` gives the file. Confirm
again (step 2 — the earlier answers lived only in chat), then continue at step 5.

## Steps

1. **Pre-check.** cli-runner: `list_threads`. Any thread with a comment newer than its handoff's
   "Last seen", or with status `Needs user`, or with no handoff → tell the user and ask whether to
   continue anyway.

2. **Confirm.** Show: PR, target branch, merge strategy from `plan.md` (`squash`, `merge`, or
   `rebase` where the code-host adapter supports it), delete source branch yes/no. With `merge` (not `squash`), warn that the commits which added the notes stay in the
   target branch's history even though the final tree drops them. Completing a PR is hard to
   reverse — wait for an explicit yes.

3. **Final PR description.** Edit `handoffs/pr-description.md`: remove the "Working notes"
   section, keep the Audit result line. cli-runner: `update_pr_description`.

4. **Cleanup commit.** In the worktree, delete `.agents/dev-workflows/<item-id>/plan.md` and
   `.agents/dev-workflows/<item-id>/handoffs/`. `git status` must show only those deletions.
   Commit as `Remove dev-workflow working notes (<item-id>)`, adapted to the project's commit
   style, and push.

5. **Complete.** cli-runner: `complete_pr` with the confirmed options (`pr_id` from `plan.md`).
   Policy block → report the policy message; never bypass.

6. **Tidy.** Set the parent item to `done` (parent `state_map`) if the project closes items on
   merge and the tracker didn't already. Offer to remove the worktree (`git worktree remove
   <path>`) and, if no other worktrees remain under `.agents/dev-workflows/`, the
   `.git/info/exclude` line. Deleting only on a yes.
