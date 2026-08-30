#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 /absolute/path/to/second-brain" >&2
  exit 1
fi

path="$1"
if [[ ! -d "$path" ]]; then
  echo "Directory does not exist: $path" >&2
  exit 1
fi

# Prefer realpath when available
if command -v realpath >/dev/null 2>&1; then
  path="$(realpath "$path")"
fi

export_line="export SECOND_BRAIN_PATH=\"$path\""

profile=""
if [[ -n "${ZSH_VERSION:-}" ]] || [[ "${SHELL:-}" == *zsh ]]; then
  profile="${HOME}/.zshrc"
elif [[ -n "${BASH_VERSION:-}" ]] || [[ "${SHELL:-}" == *bash ]]; then
  profile="${HOME}/.bashrc"
else
  profile="${HOME}/.profile"
fi

if [[ -f "$profile" ]] && grep -q 'SECOND_BRAIN_PATH=' "$profile" 2>/dev/null; then
  # Replace existing assignment lines for this var
  tmp="$(mktemp)"
  grep -v 'SECOND_BRAIN_PATH=' "$profile" > "$tmp" || true
  mv "$tmp" "$profile"
fi

echo "$export_line" >> "$profile"
export SECOND_BRAIN_PATH="$path"
echo "Appended to $profile"
echo "Current session: SECOND_BRAIN_PATH=$path"

if [[ -n "${CLAUDE_ENV_FILE:-}" ]]; then
  echo "$export_line" >> "$CLAUDE_ENV_FILE"
  echo "Appended export to CLAUDE_ENV_FILE=$CLAUDE_ENV_FILE"
fi

echo "Open a new shell (or source $profile). For Cursor session inject, see setup.md."
