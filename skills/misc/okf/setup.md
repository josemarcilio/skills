# Bootstrap `.okf/`

Run when the project has no `.okf/` directory or the user asks to set up OKF.

## 1. Create directory tree

Minimum viable bootstrap:

```
.okf/
├── index.md
├── log.md
├── business/
│   ├── index.md
│   └── log.md
└── architecture/
    ├── index.md
    └── log.md
```

Add subdirectories (`glossary/`, `patterns/`, etc.) only when first concepts are written.

## 2. Seed root `index.md`

Use the root index template in [templates.md](templates.md). Ensure frontmatter includes `okf_version: "0.2"`.

## 3. Seed bundle indexes

`.okf/business/index.md`:

```markdown
# Business knowledge

* [Scope](/business/scope.md) - Product boundaries (create when scope is settled)

_Add glossary, actors, rules, flows, and constraints as concepts are documented._
```

`.okf/architecture/index.md`:

```markdown
# Architecture knowledge

* [Scope](/architecture/scope.md) - System boundaries (create when scope is settled)

_Add patterns, persistence, runtime, and other domains as decisions are documented._
```

## 4. Seed logs

`.okf/log.md`:

```markdown
# OKF update log

## <YYYY-MM-DD>
* **Initialization**: Bootstrapped `.okf/` bundle (OKF v0.2).
```

Mirror the same date entry in `business/log.md` and `architecture/log.md` (or only bundles you created).

## 5. Wire agent entrypoints

For each file that exists or is standard in the repo:

- `AGENTS.md` — append section from [agents-snippet.md](agents-snippet.md) if missing
- `CLAUDE.md` — same section if the project uses Claude Code

Rules:

- Do not rewrite unrelated content.
- If a legacy section points at `okf/` without the dot, broaden to `.okf/`.
- If only architecture was linked, add business bundle pointer too.

## 6. Verify

- [ ] `.okf/index.md` parses and lists bundles
- [ ] No concept files missing required `type` (indexes/logs exempt)
- [ ] `AGENTS.md` or `CLAUDE.md` tells agents to start at `.okf/index.md`
- [ ] User knows install path: project knowledge lives in `.okf/`, not scattered markdown

## Optional first concepts

If the user provided context during setup, write initial `scope.md` or key glossary/decision concepts before finishing. Always refresh indexes and append logs.
