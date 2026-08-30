# Agent Skills

[![Install with skills.sh](https://img.shields.io/badge/skills.sh-install-111111)](https://github.com/josemarcilio/skills)

Reusable agent skills installable via [skills.sh](https://www.skills.sh/) and the Vercel skills CLI.

> The live install-count badge (`https://skills.sh/b/josemarcilio/skills`) appears after skills.sh indexes this repo from `npx skills add` telemetry. Until then, use the static badge above so the README does not show a broken image.

## Install

```bash
# List skills in this repo
npx skills add josemarcilio/skills --list

# Install the OKF documentation skill
npx skills add josemarcilio/skills --skill okf
```

## Skills

| Skill | Path | Description |
| --- | --- | --- |
| **okf** | [`skills/misc/okf/`](skills/misc/okf/) | Produce and bootstrap project knowledge docs using Open Knowledge Format (OKF) in `.okf/` |
| **feed-second-brain** | [`skills/misc/feed-second-brain/`](skills/misc/feed-second-brain/) | Capture notes into `SECOND_BRAIN_PATH` using that vault's `AGENTS.md` / `CLAUDE.md` |

## Repository layout

```
skills/
└── misc/
    ├── okf/
    │   └── SKILL.md
    └── feed-second-brain/
        └── SKILL.md
```

Skills are discovered from `skills/` up to three levels deep (`skills/<category>/<skill-name>/SKILL.md`).

## License

MIT — see [LICENSE](LICENSE).
