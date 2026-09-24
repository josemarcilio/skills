# Adapter: work-items / azure-boards

Implements every work-items operation in [CONTRACT.md](../CONTRACT.md) with the Azure CLI
(`az` + `azure-devops` extension). If an `azure-devops` MCP server is available, its work-item
tools are an acceptable fallback when a CLI call hangs or fails on auth.

## Rules for every operation

- One simple command per call. No loops, arrays, pipes or `&&` chains.
- Always add `--output json` and read values from the JSON, never from table output.
- Load text from files with `@<path>`. In PowerShell, quote it: `"@C:\tmp\desc.html"` (a bare `@`
  is PowerShell's splat operator).
- **Descriptions are HTML, not Markdown.** Markdown bullets, `\n` and `%0A` render as literal
  text. Use `<p>`, `<ul><li>`, `<b>`, `<code>`. The caller's files are HTML.
- **Assign by display name** (`"Jane Doe"`), not email. Email lookups can fail with
  "unknown identity".
- REST calls use `az rest` with `--resource 499b84ac-1321-427f-aa17-267ca6975798` (the Azure
  DevOps resource id). `{org}` is the org name from `detect_context`.

## detect_context

```
az devops configure --list
git remote get-url origin
```
Returns `org`, `project` (from the defaults, else parsed from the remote URL
`https://dev.azure.com/{org}/{project}/_git/{repo}`), `repo`, `configured` = yes only if org and
project are both set. If `configured` is no, report it — the user must run
`az devops configure --defaults organization=https://dev.azure.com/{org} project={project}`.

## discover_conventions

Tier: standard. Types, area path and states vary per project, even inside one org. Discover,
never assume.

```
az boards work-item show --id {sample_item_id} --expand relations --output json
az boards work-item show --id {child_id_from_relations} --output json
az rest --method get --resource 499b84ac-1321-427f-aa17-267ca6975798 --uri "https://dev.azure.com/{org}/{project}/_apis/wit/workitemtypes/{type}/states?api-version=7.1"
```
1. `parent_type` / `area_path`: the sample's `fields."System.WorkItemType"` /
   `fields."System.AreaPath"`.
2. `child_id_from_relations`: in the sample's `relations`, take the first entry whose `rel` is
   `System.LinkTypes.Hierarchy-Forward`; the id is the last path segment of its `url`. Show that
   item; its `System.WorkItemType` is `task_type`. No such relation → `task_type` = `Task`.
3. `states_parent` / `states_task`: call the states URL once per type. URL-encode the type name
   (`Product Backlog Item` → `Product%20Backlog%20Item`). The reply lists states in workflow order,
   each with a `category`. For each neutral state take the **first** state of its category:
   `Proposed`→`not-started`, `InProgress`→`active`, `Completed`→`done`, `Removed`→`removed`.
   Ignore `Resolved`. Return as `not-started=New;active=Active;done=Closed;removed=Removed`.
- `assign_format`: `display-name`.

No sample id given → report `STATUS: ERROR` asking for one. Do not guess types.

## current_iteration

```
az boards iteration team list --team "{team}" --timeframe current --output json
```
Returns `iteration_path` (`path`) and `iteration_name` (`name`).

## get_item

```
az boards work-item show --id {item_id} --expand relations --output json
```
`children` = ids from `System.LinkTypes.Hierarchy-Forward` relation URLs. `url` = the
`_links.html.href` value.

## create_parent_item

```
az boards work-item create --type "{parent_type}" --title "{title}" --area "{area_path}" --iteration "{iteration_path}" --assigned-to "{assignee}" --description "@{description_file}" --output json
```
Then, if `acceptance_file` is given, write a JSON patch file (escape `"` `\` and newlines):
`[{"op":"add","path":"/fields/Microsoft.VSTS.Common.AcceptanceCriteria","value":"<html>"}]`
```
az rest --method patch --resource 499b84ac-1321-427f-aa17-267ca6975798 --headers "Content-Type=application/json-patch+json" --uri "https://dev.azure.com/{org}/{project}/_apis/wit/workitems/{id}?api-version=7.1" --body "@{patch_file}"
```
Fallback if the patch fails: report it; the caller appends the criteria to the description.

## create_child_item

Task types usually have no acceptance-criteria field, so the criteria arrive inside
`description_file`.
```
az boards work-item create --type "{task_type}" --title "{title}" --area "{area_path}" --iteration "{iteration_path}" --assigned-to "{assignee}" --description "@{description_file}" --output json
az boards work-item relation add --id {new_id} --relation-type parent --target-id {parent_id} --output json
```
`linked` = yes only if the relation call succeeded. `{new_id}` is the `id` the create command
returned. For several tickets in one dispatch, run the pair once per ticket, one command at a
time, and report one `- operation:` group per ticket.

## update_item

```
az boards work-item update --id {item_id} --title "{title}" --description "@{description_file}" --output json
```
Pass only the flags for fields given. Acceptance criteria: same `az rest` patch as above.

## set_item_state

Look up `{platform_state}` for the neutral `state` in `state_map` (for example
`active=Active` → `Active`).
```
az boards work-item update --id {item_id} --state "{platform_state}" --output json
```
Gotcha: an invalid state name fails loudly — never retry with a guessed name; report it.
