# OKF v0.2 reference (condensed)

Full spec: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md

This skill targets **OKF 0.2**. Declare `okf_version: "0.2"` in bundle-root `.okf/index.md` frontmatter.

## Conformance checklist

A bundle is conformant when:

1. Every non-reserved `.md` file has parseable YAML frontmatter.
2. Every concept frontmatter has a non-empty `type`.
3. Reserved files (`index.md`, `log.md`) follow index/log structure when present.

Consumers MUST NOT reject bundles for: missing optional fields, unknown types, unknown extra keys, broken links, or missing indexes.

## Frontmatter families

### Core (§4)

| Field | Required | Notes |
| --- | --- | --- |
| `type` | Yes | Routing label — not centrally registered |
| `title` | Recommended | Display name |
| `description` | Recommended | One-line summary for indexes |
| `resource` | Optional | Canonical URI for underlying asset |
| `tags` | Optional | YAML list |

### Provenance — `sources` (§5.1)

```yaml
sources:
  - id: stable-key
    resource: https://example.com/doc
    title: Human label
    author: team:platform
    usage_count: 1200
    last_modified: 2026-06-01T00:00:00Z
usage_window: { from: 2026-06-01T00:00:00Z, to: 2026-06-30T00:00:00Z }
```

- `resource` required within each entry (URL, bundle path `/…`, or scope descriptor).
- `id` should be present when the body cites the source via footnote.
- Credibility signals (`author`, `usage_count`, `last_modified`) are recorded, not scored.

Footnote join: `[^stable-key]` in body matches `sources[].id`.

### Trust — `generated`, `verified` (§5.2–5.3)

```yaml
generated: { by: agent:cursor/composer, at: 2026-08-29T22:00:00Z }
verified:
  - { by: human:alice, at: 2026-08-30T10:00:00Z }
```

Trust tiers (derived, advisory):

- No `verified` → unverified
- `verified` without `human:` → machine-confirmed
- Any `human:` verifier → human-reviewed

Bare mapping `verified: { by, at }` counts as one-element list.

### Lifecycle (§5.4–5.5)

```yaml
status: stable    # draft | stable | deprecated (default: stable)
stale_after: 2026-12-31T00:00:00Z
```

## Body conventions (§4.2)

| Heading | Use |
| --- | --- |
| `# Schema` | Columns, fields, API shapes |
| `# Examples` | Usage examples |
| `# Computation` | Inline computation for Attested Computation |

## Cross-linking (§6)

- **Preferred:** `/path/from-bundle-root.md`
- **Relative:** `./neighbor.md` or `../other.md`
- Link kind is conveyed by prose, not link syntax.

`references/` subdirectory conventionally holds external mirrors, run instructions, attesters.

## Index files (§8)

No frontmatter except bundle-root `index.md` may carry `okf_version`.

```markdown
# Business

* [Order](/business/glossary/order.md) - One-line from description frontmatter
* [Actors](/business/actors/) - People and roles in the domain
```

## Log files (§9)

```markdown
# OKF update log

## 2026-08-29
* **Update**: Documented [persistence choice](/architecture/persistence/postgres.md).
* **Creation**: Bootstrapped `.okf/` bundle.
```

Date headings: `YYYY-MM-DD`. Newest first.

## Attested Computation (§10)

Standalone concept with `type: Attested Computation`:

- `runtime` (required): e.g. `bigquery`, `dbt`, `python`
- `parameters`: `{ name, type, required }`
- `computation`: path to file OR `# Computation` fenced block in body
- `executor`: `{ resource, receipt }`
- `attester`: `{ resource }`

Narrative concepts link to computations; each computation owns its own trust lifecycle.

`verified` (definition matches policy) ≠ attestation (a specific run used sanctioned computation).

## v0.1 migration notes (§13)

- `timestamp` → `generated.at` (fallback allowed when reading legacy)
- Body `# Citations` → `sources` frontmatter + footnotes
