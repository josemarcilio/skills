# Agent entrypoint snippets

Append to repo-root `AGENTS.md` and/or `CLAUDE.md` when the OKF section is missing. Do not duplicate if an equivalent section already points at `.okf/`.

## Section title

Use one of:

- `## Project knowledge (OKF)`
- `## Project knowledge`

## Markdown block

```markdown
## Project knowledge (OKF)

Agents MUST read and treat as source of truth the Open Knowledge Format bundle at [`.okf/`](.okf/).

### How to read

1. Start at [`.okf/index.md`](.okf/index.md) for the map of all knowledge bundles.
2. Open the relevant bundle:
   - [`.okf/business/`](.okf/business/) — domain language, actors, rules, flows, constraints, product scope
   - [`.okf/architecture/`](.okf/architecture/) — structural, runtime, and technical decisions
3. Each linked `.md` file is one **concept** with YAML frontmatter (`type`, `title`, `description`, trust fields).
4. Check `generated`, `verified`, `status`, and `stale_after` before trusting a concept.
5. Follow bundle-relative links (paths like `/business/glossary/order.md`) to related concepts.

### Maintainer rules

- Prefer settled OKF concepts over inventing business meaning or tech policy in chat.
- When code or decisions change project knowledge, update the matching concept under `.okf/`.
- Append the bundle `log.md` (e.g. `.okf/business/log.md`) with a dated entry; keep indexes in sync.

### Format

This project uses [Open Knowledge Format (OKF) v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md). The bundle root is always `.okf/` at the repository root.
```

## Minimal variant

When the file should stay short:

```markdown
## Project knowledge (OKF)

Read [`.okf/index.md`](.okf/index.md) first. Business knowledge: [`.okf/business/`](.okf/business/). Architecture: [`.okf/architecture/`](.okf/architecture/). Update concepts and logs when knowledge changes. Spec: OKF v0.2 in `.okf/`.
```

## CLAUDE.md note

`CLAUDE.md` and `AGENTS.md` can share the same section. If only one exists, update that file. If both exist, keep them aligned so Cursor and Claude Code agents see the same entrypoint.
