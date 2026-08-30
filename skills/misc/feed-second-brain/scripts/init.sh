#!/usr/bin/env bash
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REMINDER_TEMPLATE="$SKILL_ROOT/templates/reminder-block.md"
USER_RULE_TEMPLATE="$SKILL_ROOT/templates/cursor-user-rule.txt"

resolve_brain_path() {
  local override="${1:-}"
  if [[ -n "$override" ]]; then
    echo "$override"
    return
  fi
  if [[ -n "${SECOND_BRAIN_PATH:-}" ]]; then
    echo "$SECOND_BRAIN_PATH"
    return
  fi
  echo "SECOND_BRAIN_PATH not set. Pass path as first argument or run set-second-brain-path.sh." >&2
  exit 1
}

merge_marked_block() {
  local file_path="$1"
  local block_content="$2"
  local dir
  dir="$(dirname "$file_path")"
  mkdir -p "$dir"

  if [[ -f "$file_path" ]] && grep -q 'feed-second-brain:begin' "$file_path"; then
    local tmp
    tmp="$(mktemp)"
    awk '
      /<!-- feed-second-brain:begin -->/ { skip=1; print block; next }
      /<!-- feed-second-brain:end -->/ { skip=0; next }
      !skip { print }
    ' block="$block_content" "$file_path" > "$tmp"
    mv "$tmp" "$file_path"
    echo "Updated markers in $file_path"
  elif [[ -f "$file_path" ]]; then
    printf '\n%s\n' "$block_content" >> "$file_path"
    echo "Appended block to $file_path"
  else
    printf '%s\n' "$block_content" > "$file_path"
    echo "Created $file_path"
  fi
}

BRAIN_PATH="$(resolve_brain_path "${1:-}")"
if [[ ! -d "$BRAIN_PATH" ]]; then
  echo "Directory does not exist: $BRAIN_PATH" >&2
  exit 1
fi

if command -v realpath >/dev/null 2>&1; then
  BRAIN_PATH="$(realpath "$BRAIN_PATH")"
fi

REMINDER="$(cat "$REMINDER_TEMPLATE")"
USER_RULE="$(cat "$USER_RULE_TEMPLATE")"

# Claude
CLAUDE_MD="${HOME}/.claude/CLAUDE.md"
merge_marked_block "$CLAUDE_MD" "$REMINDER"

# Cursor support files
CURSOR_DIR="${HOME}/.cursor/feed-second-brain"
mkdir -p "$CURSOR_DIR"
printf '%s\n' "$REMINDER" > "$CURSOR_DIR/reminder.md"
printf '%s\n' "$USER_RULE" > "$CURSOR_DIR/user-rule.txt"
echo "Wrote $CURSOR_DIR/reminder.md and user-rule.txt"

# Cursor sessionStart hook
CURSOR_ROOT="${HOME}/.cursor"
HOOKS_DIR="${CURSOR_ROOT}/hooks"
mkdir -p "$HOOKS_DIR"
HOOK_SCRIPT="${HOOKS_DIR}/inject-second-brain-path.sh"
cat > "$HOOK_SCRIPT" << 'HOOK'
#!/usr/bin/env bash
path="${SECOND_BRAIN_PATH:-}"
if [[ -z "$path" ]] && command -v powershell.exe >/dev/null 2>&1; then
  path="$(powershell.exe -NoProfile -Command "[Environment]::GetEnvironmentVariable('SECOND_BRAIN_PATH','User')" 2>/dev/null | tr -d '\r')"
fi
if [[ -z "$path" ]]; then
  echo '{}'
  exit 0
fi
escaped="${path//\\/\\\\}"
escaped="${escaped//\"/\\\"}"
printf '{"env":{"SECOND_BRAIN_PATH":"%s"}}\n' "$escaped"
exit 0
HOOK
chmod +x "$HOOK_SCRIPT"

HOOKS_JSON="${CURSOR_ROOT}/hooks.json"
if [[ -f "$HOOKS_JSON" ]] && grep -q 'inject-second-brain-path' "$HOOKS_JSON"; then
  echo "sessionStart hook already present in hooks.json"
elif [[ -f "$HOOKS_JSON" ]]; then
  echo "hooks.json exists; merge sessionStart hook manually from init.md (JSON merge is fragile in shell)."
else
  cat > "$HOOKS_JSON" << EOF
{
  "version": 1,
  "hooks": {
    "sessionStart": [
      {
        "command": "./hooks/inject-second-brain-path.sh"
      }
    ]
  }
}
EOF
  echo "Created $HOOKS_JSON"
fi

INSTALLED_AT="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
cat > "$CURSOR_DIR/installed.json" << EOF
{
  "skill": "feed-second-brain",
  "version": "0.2.1",
  "secondBrainPath": "$BRAIN_PATH",
  "installedAt": "$INSTALLED_AT",
  "targets": ["claude-claude.md", "cursor-reminder", "cursor-user-rule-snippet", "cursor-sessionStart-hook"]
}
EOF

echo ""
echo "feed-second-brain init complete."
echo "  SECOND_BRAIN_PATH=$BRAIN_PATH"
echo "  Claude: $CLAUDE_MD"
echo "  Cursor: paste ~/.cursor/feed-second-brain/user-rule.txt into Settings -> Rules -> User Rules (once)."
echo "  Restart Cursor so sessionStart hook and user env apply."
