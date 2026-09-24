# Adapter: work-items / github-issues

Implements every work-items operation in [CONTRACT.md](../CONTRACT.md) with the GitHub CLI
(`gh`). Parent/child uses GitHub **sub-issues**; an organization's **issue types**, when it has
them, stand in for parent/task types.

## Rules for every operation

- One simple command per call. No loops, arrays, pipes or `&&` chains. `--jq` is a flag, not a
  pipe, and is allowed.
- `{owner}` / `{repo}` come from `detect_context`. Pass `-R {owner}/{repo}` to every `gh issue`
  command so nothing depends on the current directory.
- **Bodies are Markdown.** Load them with `--body-file {file}`.
- **Assignees are logins, not display names.** `@me` means the authenticated user.
- An issue has a **number** (`#42`, used in URLs and most commands) and an **id** (large integer,
  used by the sub-issues API). Never swap them.
- GitHub has no area paths and no acceptance-criteria field. Return `-` for `area_path`, and put
  acceptance criteria in the body.

## detect_context

```
gh auth status
gh repo view --json owner,name,url
```
Returns `org` = `owner.login`, `project` = `-`, `repo` = `name`, `configured` = yes only if
`gh auth status` succeeded. If no, the user must run `gh auth login`.

## discover_conventions

Tier: standard.
```
gh api orgs/{owner}/issue-types
gh issue view {sample_item_id} -R {owner}/{repo} --json number,title,labels,milestone,assignees
gh api repos/{owner}/{repo}/issues/{sample_item_id} --jq .type.name
gh api repos/{owner}/{repo}/issues/{sample_item_id}/sub_issues --jq ".[0].number"
```
1. Issue types: the first call fails (404) for a user-owned repo or an org without types. Then
   `parent_type` = `task_type` = `-`. Otherwise `parent_type` = the sample's type name;
   `task_type` = the type of its first sub-issue (view that number like the sample), else
   `Task` if that type exists, else `-`.
2. If the project marks types with labels instead, return `-` and add to `ERRORS:`
   `types may be labels: <sample's label names>` — the orchestrator asks the user.
3. `area_path` = `-`. `assign_format` = `login`.
4. States: `states_parent` = `states_task` =
   `not-started=open;active=open;done=closed:completed;removed=closed:not planned`.
   If the sample (or its sub-issue) carries a label meaning "in progress", use
   `active=open+label:<that label>` instead.

No sample id given → run only step 1 and use the defaults above.

## current_iteration

GitHub's nearest equivalent is a milestone.
```
gh api "repos/{owner}/{repo}/milestones?state=open&sort=due_on&direction=asc"
```
Pick the first milestone whose `due_on` is today or later; `iteration_path` = `iteration_name` =
its `title`. None → `-`. (GitHub Projects iteration fields are not handled; report that if the
user says the project uses them.)

## get_item

```
gh issue view {item_id} -R {owner}/{repo} --json number,title,state,stateReason,url,milestone
gh api repos/{owner}/{repo}/issues/{item_id} --jq .type.name
gh api repos/{owner}/{repo}/issues/{item_id}/sub_issues --jq "[.[].number]"
```
`id` = `number`. `state` = `open` or `closed:<stateReason lowercased>`. `iteration_path` =
milestone title or `-`. `children` = the sub-issue numbers.

## create_parent_item

GitHub has one body field. Write `{body_file}` into `temp_dir`: the content of
`description_file`, a blank line, `## Acceptance criteria`, the content of `acceptance_file`.
```
gh issue create -R {owner}/{repo} --title "{title}" --body-file "{body_file}" --assignee "{assignee}" --milestone "{iteration_path}"
gh api -X PATCH repos/{owner}/{repo}/issues/{new_number} -f type="{parent_type}"
```
- Omit `--milestone` when `iteration_path` is `-`. Skip the `PATCH` when `parent_type` is `-`.
- `gh issue create` prints the issue URL, not JSON. `{new_number}` = its last path segment.
  Returns `id` = that number, `url`.
- If setting the type fails, keep the issue and report the error.

## create_child_item

```
gh issue create -R {owner}/{repo} --title "{title}" --body-file "{description_file}" --assignee "{assignee}" --milestone "{iteration_path}"
gh api -X PATCH repos/{owner}/{repo}/issues/{new_number} -f type="{task_type}"
gh api repos/{owner}/{repo}/issues/{new_number} --jq .id
gh api -X POST repos/{owner}/{repo}/issues/{parent_id}/sub_issues -F sub_issue_id={new_issue_id}
```
- Same omission rules as above. `{new_issue_id}` is the **id** from the third command; `-F`
  sends it as an integer (`-f` would send a string and fail).
- `linked` = yes only if the last call succeeded. Sub-issues missing on older GitHub Enterprise
  servers → `linked: no` with the error; don't try another linking method.
- Several tickets in one dispatch: run the four commands once per ticket, one command at a time,
  one `- operation:` group per ticket.

## update_item

```
gh issue edit {item_id} -R {owner}/{repo} --title "{title}" --body-file "{body_file}"
```
Pass only the flags for fields given. If `acceptance_file` is given, build `{body_file}` as in
`create_parent_item`.

## set_item_state

Read the target from `state_map` for the neutral `state`, then run only the commands it needs:

| Target | Commands |
|---|---|
| `open` | `gh issue reopen {item_id} -R {owner}/{repo}` (only if closed) |
| `open+label:<l>` | reopen if closed, then `gh issue edit {item_id} -R {owner}/{repo} --add-label "<l>"` |
| `closed:completed` | `gh issue close {item_id} -R {owner}/{repo} --reason completed` |
| `closed:not planned` | `gh issue close {item_id} -R {owner}/{repo} --reason "not planned"` |

When the map has an in-progress label and the target is a `closed:*` state, also remove it:
`gh issue edit {item_id} -R {owner}/{repo} --remove-label "<l>"`. Returns `state` = the target.
Check the current state first with `gh issue view {item_id} -R {owner}/{repo} --json state`.
