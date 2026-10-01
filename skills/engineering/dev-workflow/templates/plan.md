# <item-id> — <title>

<!-- Built up during Phase A, written to disk before each side effect. Once Setup is
     `complete`, it is frozen: only the Changes log is appended. Every value a later phase or
     a later day needs is here. A replan (Phase B) may also update Tasks and Tickets; in stacked
     mode the Stack table is also kept current. The user may switch the decisions adapter
     (adapters/decisions/none.md) on the Adapters line. -->

- Setup: in progress | complete
- PR mode: single | stacked  <!-- stacked: see references/stacking.md -->
- Item: [<item-id>](<item-url>)
- PR: [<pr-id>](<pr-url>) — title pattern `<pattern>`, merge strategy `<squash|merge>`
  <!-- stacked: "one per layer, see Stack" instead of a link; the pattern includes the type and
       `L<n>` per references/stacking.md → Layer PR titles -->
- Branch: `<branch>` → `<target-branch>` (remote `origin`)
  <!-- stacked: the notes branch; layer branches are in the Stack table -->
- Worktree: `<user-home>/.../.agents/dev-workflows/<item-id>/worktrees/<slug>`
  <!-- stacked: two lines — stack=`.../worktrees/stack`, notes=`.../worktrees/notes` -->
- Force-push: layer branches with `--force-with-lease`, approved by <user> on <yyyy-mm-dd>
  <!-- stacked only -->
- Adapters: work-items=`<name>`, code-host=`<name>`, decisions=`none` | `ollama (model <name>)`
- Context: org=`<org>`, project=`<project>`, repo=`<repo>`, team=`<team or ->`
- Conventions: parent_type=`<type>`, task_type=`<type>`, area=`<area>`, iteration=`<iteration>`,
  assignee=`<display name, login or @me>`
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

## Stack

<!-- Stacked mode only. Bottom layer first; same order as Tasks. State: building | review |
     merged. Base changes to the target branch when the layer below merges. -->

| Layer | Task | Branch | Base | PR | State |
|---|---|---|---|---|---|
| L1 | T1 | `<branch>` | `<target-branch>` | [<pr-id>](<url>) or — | building |

## Tickets

<!-- The planner's final output, one block per ticket. Source of context, acceptance criteria,
     seams and definition of done for Phase B and the PR audit. Each block stands alone: a fresh
     agent can start the ticket from this block plus the header, Scope and Decisions. -->

### T1 — <title>

- What to build: <one paragraph>
- Context:
  - Why: <the problem and how it serves the goal>
  - Where: <file or module>, <file or module>
  - Patterns: <existing code or project rule to mirror>
  - Constraints: <binding decision or limit>
  - Out of scope: <nearby work> (<owning ticket or none>)
- Acceptance criteria:
  - <criterion>
- Candidate seams: <seam>, <seam>
- Definition of done:
  - <checkable statement>

## Changes

<!-- Appended when a replan changes the tickets, or the user switches the decisions adapter.
     One line each. -->
- <yyyy-mm-dd> — <what changed and why>
