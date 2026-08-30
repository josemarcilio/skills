# OKF concept templates

Copy and adapt. Replace placeholders. Paths use `.okf/` bundle-root absolute links.

## Root index

```markdown
---
okf_version: "0.2"
---

# Project knowledge

Open Knowledge Format bundle for this repository. Agents: start here.

# Bundles

* [Business](/business/) - Domain language, actors, rules, flows, constraints
* [Architecture](/architecture/) - Structural and technical decisions

# How to read

1. Open the bundle `index.md` for the topic area.
2. Follow links to concept files; each file is one concept.
3. Check `generated` / `verified` / `status` / `stale_after` in frontmatter for trust.
4. Prefer these concepts over inventing policy in chat.
```

## Architecture Decision

Path: `.okf/architecture/<domain>/<name>.md`

```markdown
---
type: Architecture Decision
title: <Short decision title>
description: <One-line outcome>
tags: [architecture, <domain>]
status: stable
generated: { by: agent:cursor/composer, at: 2026-08-29T22:00:00Z }
---

# <Title>

## Decision

<What we chose>

## Alternatives considered

- …

## Rationale

- …

## Consequences

- …

## Links

- Related: […](/architecture/…)
```

## Business Term

Path: `.okf/business/glossary/<term>.md`

```markdown
---
type: Business Term
title: <Term>
description: <One-line definition>
tags: [business, glossary]
status: stable
generated: { by: human:<id>, at: 2026-08-29T22:00:00Z }
---

# <Term>

## Definition

<Settled meaning>

## Notes

- …

## Links

- Used in: […](/business/flows/…)
```

## Business Rule

```markdown
---
type: Business Rule
title: <Rule name>
description: <One-line rule>
tags: [business, rules]
status: stable
generated: { by: human:<id>, at: 2026-08-29T22:00:00Z }
sources:
  - id: policy-doc
    resource: https://example.com/policy
    title: Source policy name
---

# <Rule name>

## Rule

<Statement>

## Details

- …

[^policy-doc]: Source policy name
```

## Actor

```markdown
---
type: Actor
title: <Actor name>
description: <Role in one line>
tags: [business, actors]
status: stable
generated: { by: agent:cursor/composer, at: 2026-08-29T22:00:00Z }
---

# <Actor>

## Role

<What this actor does in the system>

## Goals

- …

## Links

- Participates in: […](/business/flows/…)
```

## Flow

```markdown
---
type: Flow
title: <Flow name>
description: <Outcome in one line>
tags: [business, flows]
status: stable
generated: { by: agent:cursor/composer, at: 2026-08-29T22:00:00Z }
---

# <Flow>

## Steps

1. …
2. …

## Actors

- […](/business/actors/…)

## Links

- Rules: […](/business/rules/…)
```

## Product / system scope

Path: `.okf/business/scope.md` or `.okf/architecture/scope.md`

```markdown
---
type: Product Scope
title: <Scope title>
description: <Boundary in one line>
tags: [business, scope]
status: stable
generated: { by: human:<id>, at: 2026-08-29T22:00:00Z }
---

# Scope

## In scope

- …

## Out of scope

- …
```

For architecture scope, use `type: System Scope`.

## Type cheat-sheet

| Path area | Typical `type` |
| --- | --- |
| `business/glossary/` | Business Term |
| `business/actors/` | Actor |
| `business/rules/` | Business Rule |
| `business/flows/` | Flow |
| `business/constraints/` | Constraint |
| `business/scope.md` | Product Scope |
| `architecture/**` | Architecture Decision |
| `architecture/scope.md` | System Scope |
| `references/**` | Reference |
| computations | Attested Computation |

`index.md` and `log.md` are reserved — no `type` required.
