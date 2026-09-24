---
name: dev-workflow
description: Runs a piece of work end to end and resumably — creates the work item and INVEST tasks, a worktree and draft PR, builds each task with TDD and paired reviewer agents, audits the PR, answers human PR comments thread by thread, and completes the PR. State lives in per-task and per-thread handoff files, so work can stop and resume on any day. Tracker-agnostic through adapters (Azure DevOps included). Use when the user says "start this work", "set up the PBI/story/ticket", "continue the work", "check the PR comments", "resume task X", or "complete the PR".
---

# Dev workflow

You are the **orchestrator**. You delegate planning, tracker and code-host commands, review and
audit to agents. You write code yourself only inside the TDD loop and for PR-comment fixes.

## Agents and tiers

| Agent | Persona | Tier | Lifecycle |
|---|---|---|---|
| cli-runner | [agents/cli-runner.md](agents/cli-runner.md) | cheap | fresh per logical step |
| planner | [agents/planner.md](agents/planner.md) | capable | fresh per planning run |
| reviewer-code | [agents/reviewer-code.md](agents/reviewer-code.md) | standard | persistent per session |
| reviewer-tests | [agents/reviewer-tests.md](agents/reviewer-tests.md) | standard | persistent per session |
| pr-auditor | [agents/pr-auditor.md](agents/pr-auditor.md) | capable | fresh per audit |

**Tier → model** (edit this table for other harnesses):

| Harness | cheap | standard | capable |
|---|---|---|---|
| Claude Code | `model: haiku` | omit (inherit) | `model: opus` |
| Other | cheapest fast model | session default | strongest available |

**Spawning:** a `general-purpose` agent, the tier's model, and a prompt made of the persona
file's full text followed by the task inputs. Read `STATUS:` / `VERDICT:` / `status:` from the
reply exactly as the persona defines. If the project defines its own agent or skill for a role
(for example a review skill), prefer it — see [phases/b-execute.md](phases/b-execute.md).

**cli-runner dispatch:** the adapter file, the operation(s) from
[adapters/CONTRACT.md](adapters/CONTRACT.md) with their inputs, context values from `plan.md`,
and a `temp_dir` for any JSON it must write. One dispatch per logical step (for example "create
and link all child tasks"). Use tier `standard` for operations the adapter marks so. Never run
tracker or host commands yourself. `STATUS: ERROR` → stop and show it; don't retry with guesses.

## State on disk

```
main checkout/.agents/dev-workflows/<item-id>/worktrees/<slug>/   the worktree (excluded)
worktree/.agents/dev-workflows/<item-id>/                          committed on the branch
├── plan.md                  context, conventions, tickets; frozen after setup
└── handoffs/
    ├── pr-description.md    source of truth for the PR description
    ├── <task-id>.md         one per task
    ├── pr-audit.md          audit result and ready flag
    └── pr/<thread-id>.md    one per PR comment thread
```

Nothing depends on chat memory: every run starts by reading these files in the worktree.

## Route each invocation

1. Resolve `<item-id>`: the user's words → the current branch → `git worktree list`. None and the
   user is starting new work → **Phase A**. Otherwise ask.
2. No `plan.md` but the branch has the cleanup commit → **Phase D** (it resumes).
3. No worktree, no `plan.md`, or `plan.md` says `Setup: in progress` → **Phase A** (it resumes).
4. A task in `plan.md` without a `Done` handoff → **Phase B**, that task or the one named.
5. All tasks `Done`, `pr-audit.md` missing or not `Ready: yes` → **Phase B → PR audit**.
6. `Ready: yes` → **Phase C**. User asks to complete → **Phase D**.

The user's explicit request ("check the comments", "redo the audit") overrides the route. Say
which phase you're entering and why, in one line.

| Phase | File | Ends with |
|---|---|---|
| A Setup | [phases/a-setup.md](phases/a-setup.md) | item + tasks, worktree, `plan.md`, draft PR |
| B Execute | [phases/b-execute.md](phases/b-execute.md) | tasks done via TDD + reviews, audit passed, PR ready |
| C Feedback | [phases/c-feedback.md](phases/c-feedback.md) | every human thread answered |
| D Complete | [phases/d-complete.md](phases/d-complete.md) | notes removed, PR completed |

## Always

- Follow [references/conventions.md](references/conventions.md): discover project rules, never
  guess; `<user-home>` in written paths; handoff before side effect; confirm before merging or
  deleting.
- The project's own `AGENTS.md` / `CLAUDE.md` rules win over this skill's defaults.
- Before stopping for the day, make sure the current handoff's **Next step** is accurate.

## Credits

Built on work by Matt Pocock (`handoff`, `to-tickets`, `tdd`) and Fabio Akita (`pr-audit`). See
[CREDITS.md](CREDITS.md).
