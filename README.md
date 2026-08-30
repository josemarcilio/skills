# Agent Skills

[![skills.sh](https://skills.sh/b/josemarcilio/skills)](https://skills.sh/josemarcilio/skills)

Reusable agent skills installable via [skills.sh](https://www.skills.sh/) and the Vercel skills CLI.

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

## Repository layout

```
skills/
└── misc/
    └── okf/
        └── SKILL.md
```

Skills are discovered from `skills/` up to three levels deep (`skills/<category>/<skill-name>/SKILL.md`).

## License

MIT — see [LICENSE](LICENSE).
