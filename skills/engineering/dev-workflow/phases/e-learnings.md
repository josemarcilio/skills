# Learnings harvest

Turns what human reviewers taught during this story into edits to the project's own rule
documents, delivered as a **separate follow-up PR**. Reviewers read those documents, so an
approved learning is enforced in every future session. The feature PR is never touched here, so
its approvals are never reset.

## When it runs

- **On approval** — Phase C finds `get_pr_status` `approved: yes` and the approval is newer than
  the last harvest in `handoffs/learnings.md` (or there is none). Run it, then return to Phase C.
- **Before completing** — Phase D runs it first, always. The thread handoffs it reads are deleted
  by the cleanup commit, so this is the last chance. It only picks up threads not harvested yet.
- **On request** — "harvest the learnings".

## Steps

1. **Open the record.** Create or open `handoffs/learnings.md` from
   [templates/learnings.md](../templates/learnings.md). Collect the learning ids already
   harvested and the thread ids already processed.

2. **Curate.** Nothing new in `handoffs/pr/` since the last harvest → record "nothing new", stop.
   Otherwise spawn a fresh `general-purpose` agent at tier `capable` with the full text of
   [agents/learnings-curator.md](../agents/learnings-curator.md) and: the `handoffs/pr/` path,
   the already-harvested ids, the repo root.

3. **Decide with the user.** Show each proposal: rule, lane, evidence threads, target document and
   the exact edit. The user approves, edits, or rejects each one. `conflict` proposals need an
   explicit choice (change the old rule, or drop the new one). Record every decision in
   `handoffs/learnings.md` before touching any branch.

4. **Follow-up branch.** Nothing approved → record it, stop. Otherwise:
   - First harvest of the story: create a worktree at
     `.agents/dev-workflows/<item-id>/worktrees/<learnings-slug>` on a new branch from the
     **target branch** (not the feature branch), named by the project's pattern with a
     description like `<item-id>-review-learnings`. Verify the name, per
     [conventions.md](../references/conventions.md). Record branch and path in the record.
   - Later harvests: reuse that worktree and branch. If its PR was already merged, start a new one.

5. **Apply and commit.** Apply the approved edits exactly as approved. One commit per harvest,
   message naming the story and the rules, in the project's commit style. Run the project's
   lint/format if it covers docs. Push (`-u origin <branch>` the first time).

6. **Follow-up PR.** First harvest: write a description (the rules, one line each, and the
   threads they came from, as links) to a payload file. cli-runner: `create_draft_pr` from the
   learnings branch to the target branch, linked to the parent item (with the parent reference in
   the description when the adapter links that way), then `set_pr_ready` — docs
   only, ready for the team's review. Later harvests: `update_pr_description`. Record the PR in
   `handoffs/learnings.md`, and add it to the Follow-up line of the feature PR's
   `handoffs/pr-description.md` (that line survives the cleanup), then `update_pr_description`.

7. **Record and tell the user.** Update `handoffs/learnings.md` (harvested ids, processed
   threads, approval time it covered, follow-up PR). Commit it on the feature branch with the next
   push. Tell the user the follow-up PR link and which rules it adds.

## Rules

- Only rules a human reviewer asked for, or the user accepted. Never add rules the agents invented.
- Never edit rule documents on the feature branch.
- The follow-up PR merges on the team's schedule; completing the feature PR does not wait for it.
