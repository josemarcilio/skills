# Phase B — Execute

Loop over the tasks in `plan.md`, in table order. Tasks are INVEST-independent, so any one can be
paused and resumed alone from its handoff. After the last task, run the PR audit.

**Exit:** every task `Done`, `handoffs/pr-audit.md` `Passed` or `Accepted by user`, PR out of
draft → Phase C.

## Per task

1. **Start.** cli-runner: `set_item_state` → `active` (task `state_map` from `plan.md`). Create
   `handoffs/<task-id>.md` from [templates/task-handoff.md](../templates/task-handoff.md), copying
   acceptance criteria and candidate seams from the task's Tickets block in `plan.md` — or open the
   existing one and resume from its **Next step** and seam statuses. Status `In progress`.

2. **Seams.** Show the task's candidate seams; confirm or adjust with the user. Record them in the
   handoff. If the code area is unfamiliar, do a read-only exploration first and mirror the
   conventions you find — don't invent a new shape.

3. **Build with TDD.** Follow [references/tdd.md](../references/tdd.md): per seam, RED → tests
   review → GREEN → code **and** tests review together; then one task-level tests review of the
   whole suite against the acceptance criteria. Tasks with no runtime behavior skip the loop and
   get one code review. Update the handoff after every review round.

4. **Verification gate.** Run the project's test and lint commands for the affected area. A
   reviewer `PASS` means "no issues found by reading", not "it works". Failing checks: fix, re-run;
   re-review only if the fix changed production logic.

5. **Close.** Write the handoff first (status `Done`, commits, gotchas, next step for the story),
   then commit (task-scoped, per [conventions.md](../references/conventions.md)) and push.
   cli-runner: `set_item_state` → `done`. Tick the task in the PR description's managed block
   ([conventions.md](../references/conventions.md) → PR description → Update).

6. **Scope drift.** When a task duplicates another, or a mid-flight decision makes a task's scope
   wrong: spawn a fresh `planner` (`mode: replan`), confirm with the user, apply via cli-runner
   (`update_item`, `set_item_state` → `removed`, `create_child_item`). Update the Tasks table and
   Tickets blocks in `plan.md` (the only edit allowed after setup besides Changes), append one line
   to Changes and to the affected handoffs. Never pad work to match a stale plan.

## Review rounds

**Choose reviewers once per session.** If the project has its own review mechanism — a skill like
`checkpoints`, or reviewer agents under its agents folder — use it for every round and follow its
own procedure. Otherwise use the bundled personas: spawn a `general-purpose` agent with the full
text of [agents/reviewer-code.md](../agents/reviewer-code.md) (or
[reviewer-tests.md](../agents/reviewer-tests.md)) as its instructions, at tier `standard`.

**Lifecycle** (checkpoints fidelity):

- First round of the session: spawn. Write the returned agent id in the handoff's "Reviewer ids"
  line (valid for this session only).
- Every later round: `SendMessage` to that same id. Never spawn a second instance of a lane that
  is running — it loses the memory of earlier rounds.
- `reviewer-tests` joins on the first round that touches tests; `reviewer-code` on the first
  round with production code. When both apply in one round (every GREEN round does), send both in
  the same message so they run concurrently.
- A change to a test file always goes to `reviewer-tests`, a change to production code always goes
  to `reviewer-code` — never only one when both changed.
- A new session (next day, cleared context) starts fresh reviewers. Note it in the handoff.
- Past ~25–30 rounds in one session, offer the user a reviewer restart (cheaper rounds, lost
  repeat-violation memory). Never restart silently.

**Each round** send only the files changed in that round (not a full diff), plus for tests the
`phase` (`red`, `green`, `task`, `tests`), seam, acceptance criteria, and — for `red` — the failure
output. `green` rounds include the production files too; `task` rounds include every test and
production file the task touched.

**Merge and act.** When both lanes ran: verdict = the worst (`FAIL` > `NEEDS_CHANGES` > `PASS`),
issues concatenated.

- `NEEDS_CHANGES` — fix every `blocking` issue, re-review the fixed files. Mention what you do
  about `minor` issues; don't drop them silently.
- `FAIL` — stop. Show the issues to the user before fixing anything. A critical-rule break or a
  design question needs a human call. Mark the handoff `Blocked`.
- `PASS` — continue (to GREEN, the next seam, or the verification gate).
- **Loop guard:** the same `blocking` issue surviving three rounds → stop, tell the user what it
  is, what you tried, and why it isn't resolving.

## PR audit (after the last task)

1. Confirm every task is ticked in `handoffs/pr-description.md`, the branch is pushed, and
   `git fetch origin` ran. Note `head_sha`. cli-runner: `get_pr_description` into `temp_dir` — the
   auditor needs the whole description, including the parts people wrote.
2. Spawn a fresh `general-purpose` agent at tier `capable` with the full text of
   [agents/pr-auditor.md](../agents/pr-auditor.md) and: repo root, worktree, target branch,
   `head_sha`, `plan.md`, the fetched description file, test/lint commands.
3. Save `handoffs/pr-audit.md` from [templates/audit-handoff.md](../templates/audit-handoff.md)
   (`Ready: no`); put the result line and top findings in the Audit section of the managed block
   (PR description → Update). Commit, push.
4. `Blocked` → stay in draft. Show the findings. Fix them as a normal task round (TDD, reviews),
   then re-run the audit fresh. The user may accept a finding instead — record who and why.
5. `Passed` (or all remaining findings accepted) → cli-runner: `set_pr_ready`, then set
   `Ready: yes` in `pr-audit.md`, commit, push. (A stop between the two only means the next run
   repeats `set_pr_ready`, which is harmless.) Set the parent item's state to match reality
   (`done` only if every task is done and verified; otherwise `active`, and say what's
   unverified). Tell the user. Next: Phase C once reviewers comment.
