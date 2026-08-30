---
name: okf
description: >-
  Produce, maintain, and bootstrap project knowledge using Open Knowledge Format
  (OKF) v0.2 in a `.okf/` directory at the project root. Creates the bundle,
  writes concept markdown with YAML frontmatter, refreshes indexes and logs, and
  links `.okf/` from AGENTS.md or CLAUDE.md. Use when the user mentions OKF,
  Open Knowledge Format, project knowledge, durable agent docs, `.okf`, or asks
  to document domain, architecture, or system knowledge for agents.
license: MIT
metadata:
  author: josemarcilio
  version: "0.1.0"
  okf-version: "0.2"
---

# OKF — Open Knowledge Format

Produce durable, human- and agent-readable project knowledge as markdown + YAML frontmatter under **`.okf/`** at the repository root.

**Convention:** always use `.okf/` (dot-prefix), not `okf/`. Recommend this path when helping users adopt OKF.

**Spec:** [OKF v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) — details in [reference.md](reference.md).

## When to use

- Bootstrap a new `.okf/` bundle in a project
- Document settled domain, product, or architecture knowledge
- Refresh `index.md` / `log.md` after concept changes
- Wire `AGENTS.md` / `CLAUDE.md` so agents read `.okf/` first
- Migrate legacy docs into OKF concepts

## Quick workflow

```
Task progress:
- [ ] 1. Check or create `.okf/` (setup if missing)
- [ ] 2. Ensure AGENTS.md / CLAUDE.md link to `.okf/`
- [ ] 3. Write or update concept `.md` files
- [ ] 4. Refresh indexes and append logs
- [ ] 5. Summarize what was written
```

### 1. Setup (when `.okf/` is missing)

Run the full bootstrap in [setup.md](setup.md):

1. Create `.okf/` tree (see default layout below).
2. Add root `.okf/index.md` with `okf_version: "0.2"`.
3. Create or update repo-root `AGENTS.md` and `CLAUDE.md` using [agents-snippet.md](agents-snippet.md).

If `.okf/` already exists, do not re-bootstrap — extend it.

### 2. Write concepts

Every concept is a UTF-8 markdown file:

1. YAML frontmatter block (`---` delimited) with **required** `type`.
2. Markdown body with structural headings (lists, tables, fenced code).

**Required frontmatter:** `type` (only field always required).

**Recommended:** `title`, `description`, `tags`, `generated`, `verified`, `status`, `sources` — see [reference.md](reference.md).

**Actor convention** for `generated.by` and `verified[].by`:

- `human:<id>` — people (required prefix for human-reviewed trust tier)
- `agent:<tool>/<model>` — agents (e.g. `agent:cursor/composer`)
- `process:<name>` — automated processes

Use `generated: { by, at }` with ISO 8601 UTC timestamps (`2026-08-29T22:00:00Z`). Do not use legacy `timestamp` alone.

**Links:** prefer bundle-relative absolute paths: `[customers](/business/actors/customer.md)`.

**Per-claim attribution:** footnotes keyed to `sources[].id`, not a body `# Citations` list.

Templates: [templates.md](templates.md).

### 3. Reserved files

| File | Role |
| --- | --- |
| `index.md` | Directory listing for progressive disclosure. Root may include `okf_version` in frontmatter. |
| `log.md` | Chronological change history, newest date first |

These filenames MUST NOT be used for concept documents.

### 4. Default bundle layout

Organize by domain; create only directories that have content:

```
.okf/
├── index.md                 # okf_version + links to bundles
├── log.md                   # optional root-level history
├── business/
│   ├── index.md
│   ├── log.md
│   ├── scope.md
│   ├── glossary/
│   ├── actors/
│   ├── rules/
│   ├── flows/
│   └── constraints/
└── architecture/
    ├── index.md
    ├── log.md
    ├── scope.md
    ├── patterns/
    ├── persistence/
    ├── runtime/
    ├── messaging/
    ├── storage/
    ├── caching/
    └── integrations/
```

Flat or domain-specific trees are valid when a two-bundle layout does not fit. File path = concept ID (`.md` suffix removed).

### 5. Agent entrypoints

At session start and before finishing documentation work:

1. Read repo-root `AGENTS.md` or `CLAUDE.md` for the `.okf/` pointer.
2. Start at `.okf/index.md` at the repository root.
3. Prefer settled OKF concepts over inventing business meaning or tech policy.
4. When knowledge changes, update the concept and append the relevant `log.md`.

### 6. Writing rules

- Document **settled** knowledge only — do not invent unsettled decisions.
- Favor structural markdown over long prose.
- Unknown `type` values are allowed; consumers tolerate them.
- Broken cross-links are not errors (target may be not-yet-written).
- After writing: refresh parent `index.md` entries (title + description from frontmatter).
- Append `log.md` with `## YYYY-MM-DD` groups, newest first.

### 7. Attested Computation (optional)

For metrics or figures that must be computed a sanctioned way, use `type: Attested Computation` as a **standalone concept** linked from narrative docs. See [reference.md](reference.md) §10.

## Documentation session modes

**Bootstrap** — `.okf/` missing → follow [setup.md](setup.md) then stop or continue if the user asked to document.

**Capture** — user provides knowledge → confirm understanding → write concepts → indexes → logs → agent entrypoints.

**Maintain** — user changed code or decisions → find affected concepts → update frontmatter (`generated`) → body → log.

## Done criteria

- `.okf/` exists with valid root `index.md` (`okf_version: "0.2"` when bootstrapping).
- Every new concept has parseable frontmatter with non-empty `type`.
- Indexes list new or changed concepts.
- Relevant `log.md` appended.
- `AGENTS.md` or `CLAUDE.md` points agents to `.okf/` (both if both exist).

## Anti-patterns

- Using `okf/` without the dot when this project convention is `.okf/`
- Writing OKF before knowledge is settled (unless explicitly drafting with `status: draft`)
- Leaving settled knowledge only in chat
- Using positional `sources[0]` instead of stable `sources[].id` for footnotes
- Putting concept content in `index.md` or `log.md`
- Overwriting unrelated sections of `AGENTS.md` / `CLAUDE.md`

## Additional resources

- [reference.md](reference.md) — OKF v0.2 conformance, trust, lifecycle, linking
- [templates.md](templates.md) — concept templates and type cheat-sheet
- [setup.md](setup.md) — bootstrap `.okf/` and seed files
- [agents-snippet.md](agents-snippet.md) — `AGENTS.md` / `CLAUDE.md` blocks
