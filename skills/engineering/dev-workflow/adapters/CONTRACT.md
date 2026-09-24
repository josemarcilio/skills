# Adapter contract

Phases never name a CLI. They call the operations below. An adapter file maps each operation to
concrete commands for one platform. Adding a platform means adding one adapter file that
implements every operation of its kind — no phase file changes.

There are two adapter kinds, chosen independently per project:

- `work-items/<name>.md` — where items and tasks live (Azure Boards, Jira, GitHub Issues, ...)
- `code-host/<name>.md` — where branches and PRs live (Azure Repos, GitHub, ...)

## Choosing adapters

1. If `plan.md` already records them (`Adapters:` line), use those.
2. Otherwise infer the code host from `git remote get-url origin` (`dev.azure.com` /
   `visualstudio.com` → `azure-repos`, `github.com` → `github`).
3. Infer the work-item tracker from the repo's docs (`AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`)
   or from the code host (Azure Repos → `azure-boards`, GitHub → `github-issues`).
4. If the inferred adapter file does not exist, stop and tell the user which file is missing.
   Never improvise commands for an unsupported platform.

## Every operation section in an adapter must state

- **Inputs** — the named values the caller passes.
- **Commands** — exact commands, one simple command per line (no loops, no arrays, no chained
  pipelines — some environments run safety hooks that cannot verify complex shell).
- **Returns** — the exact `RESULT:` keys the cli-runner must report.
- **Gotchas** — platform traps that fail silently.
- **Fallback** — what to try if the primary route hangs or errors, if one exists.
- **Tier** (optional) — `Tier: standard` when the operation needs more judgment than a cheap
  model reliably has (heavy JSON filtering, multi-step lookups). The orchestrator dispatches it at
  that tier.

## work-items operations

| Operation | Inputs | Returns |
|---|---|---|
| `detect_context` | — | `org`, `project`, `repo`, `configured` (yes/no) |
| `discover_conventions` | `sample_item_id` (optional), `team` (optional) | `parent_type`, `task_type`, `area_path`, `states_parent`, `states_task`, `assign_format` |
| `current_iteration` | `team` | `iteration_path`, `iteration_name` |
| `get_item` | `item_id` | `id`, `type`, `title`, `state`, `area_path`, `iteration_path`, `url`, `children` (ids) |
| `create_parent_item` | `title`, `description_file`, `acceptance_file`, `area_path`, `iteration_path`, `assignee` | `id`, `url` |
| `create_child_item` | `parent_id`, `title`, `description_file` (includes acceptance criteria), `area_path`, `iteration_path`, `assignee` | `id`, `url`, `linked` (yes/no) |
| `update_item` | `item_id`, any of `title`, `description_file`, `acceptance_file` | `id`, `updated_fields` |
| `set_item_state` | `item_id`, `state` (one of `not-started`, `active`, `done`, `removed`), `state_map` | `id`, `state` (the platform's real state name) |

`set_item_state` takes the skill's four neutral states. The adapter maps them to the platform's
real state names using `state_map` — the `states_parent` or `states_task` string that
`discover_conventions` returned and `plan.md` recorded.

## code-host operations

| Operation | Inputs | Returns |
|---|---|---|
| `create_draft_pr` | `source_branch`, `target_branch`, `title`, `description_file`, `item_ids` | `pr_id`, `url` |
| `update_pr_description` | `pr_id`, `description_file` | `pr_id` |
| `set_pr_ready` | `pr_id` | `pr_id`, `draft` (no) |
| `get_pr_status` | `pr_id` | `pr_id`, `draft` (yes/no), `state` (`open` / `completed` / `abandoned`), `approved` (yes/no), `changes_requested` (yes/no), `approvers` (names) |
| `list_threads` | `pr_id` | one block per human thread: `thread_id`, `status`, `file`, `line`, `last_comment_id`, `last_author`, `last_date`, `excerpt` |
| `reply_thread` | `pr_id`, `thread_id`, `body_file` | `thread_id`, `comment_id` |
| `resolve_thread` | `pr_id`, `thread_id` | `thread_id`, `status` |
| `complete_pr` | `pr_id`, `source_branch`, `merge_strategy` (`squash` / `merge` / `rebase`), `delete_source_branch` | `pr_id`, `status`, `merge_commit` |

`list_threads` must drop system/bot threads (status changes, votes, pushes) and return only
threads a person wrote.

`resolve_thread` returns `status: unsupported` (with `STATUS: OK`) for threads the platform
can't resolve — for example GitHub's general PR comments. Record it as not resolved.

`create_draft_pr` links `item_ids` however the platform does it: a flag (Azure Repos) or
references in the description text (GitHub). Each code-host adapter states which; the
orchestrator writes any required references into the description file.

Unsupported `merge_strategy` → `STATUS: ERROR`; never substitute another strategy.

`get_pr_status` `approved` means the platform's own reviewers approved: every required reviewer
approved and nobody rejected or requested changes. It says nothing about checks or builds.

Text payloads (descriptions, replies) are always passed as files the main agent writes to a
scratch/temp location — never inline in a command — so quoting and newlines survive every shell.
Each adapter states the format its files must use (for example HTML vs Markdown).
