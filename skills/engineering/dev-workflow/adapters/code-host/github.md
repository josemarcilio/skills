# Adapter: code-host / github

Implements every code-host operation in [CONTRACT.md](../CONTRACT.md) with the GitHub CLI
(`gh`), using GraphQL through `gh api graphql` where the REST commands can't reach (review
threads).

## Rules for every operation

- One simple command per call. No loops, arrays, pipes or `&&` chains. `--jq` is allowed.
- Pass `-R {owner}/{repo}` to every `gh pr` command. `{owner}` = `org` from `detect_context`,
  `{repo}` = `repo`.
- **Descriptions and comments are Markdown.** Load them with `--body-file`, or `-F body=@{file}`
  for GraphQL.
- GraphQL queries go in a file written into `temp_dir`, passed as `-F query=@{query_file}`, so
  quoting survives every shell.
- `{pr_id}` is the PR **number**.

## Linking work items

GitHub links a PR to issues through its description text, not a flag. Every id in `item_ids`
must appear in `description_file`: for GitHub Issues as `Refs #<n>` (not `Closes`/`Fixes` — this
skill closes items itself), for Azure Boards as `AB#<n>`, for other trackers the item key. Missing
reference → `STATUS: ERROR`, don't edit the file.

## create_draft_pr

```
gh pr create -R {owner}/{repo} --draft --base "{target_branch}" --head "{source_branch}" --title "{title}" --body-file "{description_file}"
```
Prints the PR URL, not JSON. `pr_id` = its last path segment; `url` = the printed URL.

## get_pr_description

Tier: standard (copies text verbatim).
```
gh pr view {pr_id} -R {owner}/{repo} --json body --jq .body
```
Write the command's output to `{out_file}` exactly as printed, with a file-writing tool. `chars` =
its length. Nothing printed → empty file.

## update_pr_description

```
gh pr edit {pr_id} -R {owner}/{repo} --body-file "{description_file}"
```

## set_pr_ready

```
gh pr ready {pr_id} -R {owner}/{repo}
```

## get_pr_status

```
gh pr view {pr_id} -R {owner}/{repo} --json isDraft,state,reviewDecision,latestReviews
```
- `draft` = `isDraft`; `state`: `OPEN` → `open`, `MERGED` → `completed`, `CLOSED` → `abandoned`.
- `approved` = yes when `reviewDecision` is `APPROVED`. When `reviewDecision` is empty (the repo
  requires no reviews): yes when at least one `latestReviews` entry is `APPROVED` and none is
  `CHANGES_REQUESTED`.
- `changes_requested` = yes when `reviewDecision` is `CHANGES_REQUESTED` or any latest review is.
  `approvers` = `author.login` of `APPROVED` latest reviews.

## list_threads

Tier: standard (merges three kinds of feedback from one large reply).

Write `{query_file}`:
```graphql
query($owner: String!, $repo: String!, $n: Int!) {
  viewer { login }
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $n) {
      reviewThreads(first: 100) {
        nodes { id isResolved path line originalLine
          comments(last: 1) { nodes { databaseId createdAt body author { login __typename } } } }
      }
      reviews(last: 100) {
        nodes { id databaseId state body submittedAt author { login __typename } }
      }
      comments(last: 100) {
        nodes { id databaseId createdAt body author { login __typename } }
      }
    }
  }
}
```
```
gh api graphql -F query=@{query_file} -F owner={owner} -F repo={repo} -F n={pr_id}
```
Report one block per item below, and drop anything whose author `__typename` is `Bot`:

- **Review threads** (inline, resolvable): `thread_id` = `id` (starts `PRRT_`), `status` =
  `resolved` / `active` from `isResolved`, `file` = `path`, `line` = `line` (else
  `originalLine`, else `-`), `last_comment_id` = `databaseId` of the last comment, `last_author`,
  `last_date`, `excerpt`.
- **Review summaries** with a non-empty `body`: `thread_id` = `id` (starts `PRR_`), `status` =
  `open`, `file` = `-`, `line` = `-`, `last_comment_id` = `databaseId`.
- **General comments**: `thread_id` = `id` (starts `IC_`), `status` = `open`, `file` = `-`,
  `line` = `-`. **Skip comments whose author is `viewer.login`** — those are this skill's own
  replies (general comments have no threading, so a reply would otherwise look like a new thread).

More than 100 of any kind → add `truncated: <kind>` to `ERRORS:` (still `STATUS: OK`).

## reply_thread

**Review thread** (`thread_id` starts `PRRT_`). Write `{query_file}`:
```graphql
mutation($id: ID!, $body: String!) {
  addPullRequestReviewThreadReply(input: { pullRequestReviewThreadId: $id, body: $body }) {
    comment { databaseId }
  }
}
```
```
gh api graphql -F query=@{query_file} -f id={thread_id} -F body=@{body_file}
```
`comment_id` = the returned `databaseId`.

**Review summary or general comment** (`PRR_` / `IC_`): no threading exists. Write
`{reply_file}` into `temp_dir`: `@{last_author}`, a line `> ` + the first line of the excerpt, a
blank line, then the content of `body_file`.
```
gh pr comment {pr_id} -R {owner}/{repo} --body-file "{reply_file}"
```
Prints the comment URL ending in `#issuecomment-<n>`; `comment_id` = `<n>`.

## resolve_thread

**Review thread** only. Write `{query_file}`:
```graphql
mutation($id: ID!) { resolveReviewThread(input: { threadId: $id }) { thread { isResolved } } }
```
```
gh api graphql -F query=@{query_file} -f id={thread_id}
```
Returns `status` = `resolved`. For `PRR_` / `IC_` ids return `status: unsupported` with
`STATUS: OK` — GitHub can't resolve those.

## complete_pr

`{strategy_flag}` from `merge_strategy`: `squash` → `--squash`, `merge` → `--merge`, `rebase` →
`--rebase`.
```
gh pr merge {pr_id} -R {owner}/{repo} {strategy_flag}
gh api -X DELETE repos/{owner}/{repo}/git/refs/heads/{source_branch}
gh pr view {pr_id} -R {owner}/{repo} --json state,mergeCommit
```
- Run the `DELETE` only when `delete_source_branch` is true. **Don't use `--delete-branch` on
  `gh pr merge`**: it also deletes the local branch and switches branches in the current
  directory, which fails inside a worktree.
- Required checks or reviews block the merge — report the message. **Never pass `--admin`.**
- Returns `status` = `state` (`MERGED`), `merge_commit` = `mergeCommit.oid`.
