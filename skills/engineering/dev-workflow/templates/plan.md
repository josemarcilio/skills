# <item-id> — <title>

<!-- Built up during Phase A, written to disk before each side effect. Once Setup is
     `complete`, it is frozen: only the Changes log is appended. Every value a later phase or
     a later day needs is here. A replan (Phase B) may also update Tasks and Tickets. -->

- Setup: in progress | complete
- Item: [<item-id>](<item-url>)
- PR: [<pr-id>](<pr-url>) — title pattern `<pattern>`, merge strategy `<squash|merge>`
- Branch: `<branch>` → `<target-branch>` (remote `origin`)
- Worktree: `<user-home>/.../.agents/dev-workflows/<item-id>/worktrees/<slug>`
- Adapters: work-items=`<name>`, code-host=`<name>`
- Context: org=`<org>`, project=`<project>`, repo=`<repo>`, team=`<team or ->`
- Conventions: parent_type=`<type>`, task_type=`<type>`, area=`<area>`, iteration=`<iteration>`,
  assignee=`<display name>`
- State maps: parent=`<states_parent>`; task=`<states_task>`
- Checks: test=`<command>`; lint=`<command>`

## Scope

<The agreed plan: goal, in scope, out of scope.>

## Decisions

- <decision> — <why>

## Tasks

| Ref | Id | Title |
|---|---|---|
| T1 | [<id or pending>](<url>) | <title> |

## Tickets

<!-- The planner's final output, one block per ticket. Source of acceptance criteria and seams
     for Phase B and the PR audit. -->

### T1 — <title>

- What to build: <one paragraph>
- Acceptance criteria:
  - <criterion>
- Candidate seams: <seam>, <seam>

## Changes

<!-- Appended when a replan changes the tickets. One line each. -->
- <yyyy-mm-dd> — <what changed and why>
