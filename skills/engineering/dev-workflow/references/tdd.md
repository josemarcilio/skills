# TDD loop

Adapted from mattpocock's `tdd` skill (see CREDITS.md). If the project has its own testing docs,
their conventions (stack, file placement, naming) win; the loop rules below still apply.

## Seams first

A **seam** is the public boundary where behavior is observed without reaching inside: an
exported function, an endpoint, a component's inputs and outputs, a CLI command.

- The planner proposes seams per ticket. At task start, show them to the user and confirm.
- **No test is written at an unconfirmed seam.** If the right seam is unclear (how deep the
  module is, what the interface should expose), stop and agree it with the user first.

## The cycle — one seam, one behavior at a time

1. **RED** — write one failing test for one behavior at a confirmed seam. Run it. It must fail
   because the behavior is missing, not because of an import error or broken setup.
2. **Review the test** — send `reviewer-tests` the test file(s), `phase: red`, the seam, the
   acceptance criteria, and the failure output. Act on the verdict (see
   [phases/b-execute.md](../phases/b-execute.md)).
3. **GREEN** — write only enough code to pass. Don't anticipate the next test, don't add
   speculative features. Run the relevant tests; all must pass.
4. **Review both** — in one message, so they run concurrently:
   - `reviewer-code`: the production files changed in this cycle. Refactoring suggestions come
     from this review — refactoring is not part of the loop.
   - `reviewer-tests`, `phase: green`: the cycle's test file(s) **and** the production files. It
     checks the test against the real code — branches the green code added without a test, and
     any test edits made while getting to green.
   Merge the verdicts and act on them. A fix or refactor that touches a test file goes back to
   `reviewer-tests` (`phase: tests`); one that touches production code goes back to
   `reviewer-code`. Re-run the tests after every change.

Repeat for the next behavior. Each test is a tracer bullet: let what the last cycle taught you
shape the next test. Never write all tests first and all code after (horizontal slicing).

## Task close — one review of the whole suite

After the last seam, before the verification gate: send `reviewer-tests` `phase: task` with every
test file the task touched, the production files, and all its acceptance criteria. It checks that
each criterion has a test at a confirmed seam, and finds duplicates across cycles — things no
single cycle can see.

## What a good test is

- Verifies behavior through the public seam. Code can change entirely; the test shouldn't.
- Reads like a specification: the name says **what** the caller can do, not **how**.
- One logical assertion per test.
- Expected values come from an independent source of truth — a literal, a worked example, the
  spec — never recomputed the way the code computes them.

## Anti-patterns

- **Implementation-coupled** — mocks internal collaborators, tests private methods, asserts call
  order, or verifies through a side channel (querying the database instead of the interface).
  Tell: it breaks on refactor while behavior is unchanged.
- **Tautological** — the assertion recomputes the expected value like the code does, so it passes
  by construction.
- **Horizontal slicing** — all tests first, then all code. Tests end up checking imagined shape
  instead of real behavior.

## Mocking

Mock only at system boundaries: external APIs, time, randomness, sometimes the database or file
system (prefer a test instance). Never mock the project's own modules. Where a boundary is hard
to mock, pass the dependency in rather than constructing it inside.

## Tasks with no runtime behavior

Docs, config, styling, pure renames: skip the loop. Make the change, then one `reviewer-code`
round, then the verification gate.
