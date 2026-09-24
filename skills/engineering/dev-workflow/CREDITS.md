# Credits

This skill adapts ideas and text from the works below. Thank you to their authors.

| Source | Author | License | Used for |
|---|---|---|---|
| [pr-audit](https://github.com/akitaonrails/my-skills/blob/master/pr-audit/SKILL.md) | Fabio Akita ([@akitaonrails](https://github.com/akitaonrails)) | See upstream repo | `agents/pr-auditor.md`: trusted state, claim ledger, hostile-change gate, audit dimensions, severity levels, report layout, evidence rules |
| [handoff](https://github.com/mattpocock/skills/blob/main/skills/productivity/handoff/SKILL.md) | Matt Pocock ([@mattpocock](https://github.com/mattpocock)) | MIT | `templates/*-handoff.md` and handoff rules: resumable by a fresh agent, reference artifacts instead of copying them, suggested skills, no secrets |
| [to-tickets](https://github.com/mattpocock/skills/tree/main/skills/engineering/to-tickets) ([article](https://www.aihero.dev/skills-to-tickets)) | Matt Pocock | MIT | `agents/planner.md`: ticket schema (title, what to build, acceptance criteria, ready-for-agent), vertical slices, quiz-until-approved. Dependency edges were deliberately left out in favor of INVEST independence |
| [tdd](https://github.com/mattpocock/skills/tree/main/skills/engineering/tdd) | Matt Pocock | MIT | `references/tdd.md` and parts of `agents/reviewer-tests.md`: seams, one test per cycle, anti-patterns, mocking at boundaries, refactor-in-review |
| `checkpoints` skill and `copilot` / `copilot-tests` agents | Marcilio Farias (earlier private work) | — | Review lifecycle in `phases/b-execute.md` and both reviewer personas: persistent reviewers via SendMessage, two lanes, merged verdict, loop guard, verification gate, strict `VERDICT` output |

The INVEST criteria for user stories are from Bill Wake, "INVEST in Good Stories, and SMART
Tasks" (2003).

Before publishing, confirm the license of `akitaonrails/my-skills` and keep any notice it
requires. MIT-licensed sources require keeping their copyright and permission notice with
substantial portions — see each repository's `LICENSE`.
