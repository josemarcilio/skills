# Adapter: code-host / azure-repos

Implements every code-host operation in [CONTRACT.md](../CONTRACT.md) with the Azure CLI
(`az repos`, `az devops invoke`). If an `azure-devops` MCP server is available, its pull-request
tools are the fallback when a CLI call hangs — and the CLI is the fallback when an MCP call hangs.
Never block waiting on either; after one hang, switch routes.

## Rules for every operation

- One simple command per call. No loops, arrays, pipes or `&&` chains.
- Always add `--output json`.
- Load text with `@<path>`; in PowerShell quote it (`"@C:\tmp\pr.md"`).
- **PR descriptions and comments are Markdown** (unlike Boards work items, which are HTML).
- **PR descriptions are capped at 4000 characters.** Over the cap, the call fails — report it.
- JSON bodies for `az devops invoke` go through `--in-file`, never inline, so quoting survives
  PowerShell and bash alike. Write the JSON file with a file-writing tool, not `echo`.
- `{project}` and `{repo}` come from `detect_context`; `repositoryId` accepts the repo name.
- Web URL of a PR: `https://dev.azure.com/{org}/{project}/_git/{repo}/pullrequest/{pr_id}`.

## create_draft_pr

```
az repos pr create --draft true --source-branch "{source_branch}" --target-branch "{target_branch}" --title "{title}" --description "@{description_file}" --work-items {item_ids} --output json
```
Returns `pr_id` (`pullRequestId`) and the web `url`. `{item_ids}` is space-separated.
`--work-items` only links Azure Boards items. With another work-items adapter, omit the flag; the
description file carries the item keys instead.

## get_pr_description

Tier: standard (copies text verbatim).
```
az repos pr show --id {pr_id} --query description --output tsv
```
Write the command's output to `{out_file}` exactly as printed, with a file-writing tool. `chars` =
its length. Nothing printed → empty file.

## update_pr_description

```
az repos pr update --id {pr_id} --description "@{description_file}" --output json
```

## set_pr_ready

```
az repos pr update --id {pr_id} --draft false --output json
```

## get_pr_status

```
az repos pr show --id {pr_id} --output json
az repos pr reviewer list --id {pr_id} --output json
```
- `draft` = `isDraft`; `state` = `status` (`active` → `open`, `completed`, `abandoned`).
- Reviewer votes: `10` approved, `5` approved with suggestions, `0` no vote, `-5` waiting for
  author, `-10` rejected. `approved` = yes when no vote is below `0`, every reviewer with
  `isRequired: true` voted `5` or `10`, and at least one reviewer did.
- `changes_requested` = yes when any vote is `-5` or `-10`. `approvers` = `displayName` of
  reviewers who voted `5` or `10`.

## list_threads

Tier: standard (filters a large JSON reply).

```
az devops invoke --area git --resource pullRequestThreads --route-parameters project={project} repositoryId={repo} pullRequestId={pr_id} --http-method GET --api-version 7.1 --output json
```
Keep a thread only if it has at least one non-deleted comment with `commentType` = `text` whose
author is a person (not a build service or bot). Per kept thread report:
`thread_id` (`id`), `status` (`active`, `pending`, `fixed`, `wontFix`, `closed`, `byDesign`),
`file` (`threadContext.filePath`, or `-` for general comments), `line`
(`threadContext.rightFileStart.line`, else `leftFileStart.line`, else `-`), `last_comment_id`
(highest non-deleted comment id), `last_author`, `last_date`, `excerpt` (first 200 chars of the
last comment).

## reply_thread

Write `{reply_json}` from the caller's Markdown `body_file`:
`{"parentCommentId": 1, "content": "<markdown, JSON-escaped>", "commentType": 1}`
```
az devops invoke --area git --resource pullRequestThreadComments --route-parameters project={project} repositoryId={repo} pullRequestId={pr_id} threadId={thread_id} --http-method POST --in-file "{reply_json}" --api-version 7.1 --output json
```
Returns `comment_id` (`id`).

## resolve_thread

Write `{status_json}`: `{"status": "fixed"}`
```
az devops invoke --area git --resource pullRequestThreads --route-parameters project={project} repositoryId={repo} pullRequestId={pr_id} threadId={thread_id} --http-method PATCH --in-file "{status_json}" --api-version 7.1 --output json
```
`fixed` shows as "Resolved" in the UI.

## complete_pr

`merge_strategy`: `squash` → `--squash true`, `merge` → `--squash false`. Other strategies are
not supported by this CLI; report `STATUS: ERROR` instead of picking one.
```
az repos pr update --id {pr_id} --status completed --squash {true|false} --delete-source-branch {true|false} --output json
```
Gotchas: branch policies (required reviewers, builds) can block completion — report the policy
message. **Never pass `--bypass-policy`.** A completed status may take a moment to show a merge
commit; read `lastMergeCommit.commitId` from a follow-up
`az repos pr show --id {pr_id} --output json`.
