# Set `SECOND_BRAIN_PATH`

Use an absolute path to the second-brain root (the folder that contains `AGENTS.md` and/or `CLAUDE.md`).

## Windows

Sets a persistent user-level `SECOND_BRAIN_PATH`:

```powershell
# From this skill directory, or copy the script
.\scripts\set-second-brain-path.ps1 -Path "D:\path\to\second-brain"
```

Or manually:

```powershell
[Environment]::SetEnvironmentVariable("SECOND_BRAIN_PATH", "D:\path\to\second-brain", "User")
$env:SECOND_BRAIN_PATH = "D:\path\to\second-brain"
```

Restart Cursor (or open a new shell) so agents see the user env var.

## Unix

Appends `export SECOND_BRAIN_PATH=...` to your shell profile:

```bash
./scripts/set-second-brain-path.sh "/path/to/second-brain"
```

Or manually (zsh example):

```bash
echo 'export SECOND_BRAIN_PATH="/path/to/second-brain"' >> ~/.zshrc
source ~/.zshrc
```

Prefer `~/.zshrc` when the default shell is zsh; otherwise `~/.bashrc` / `~/.profile`.

## Claude

Also writes to `$CLAUDE_ENV_FILE` when present (session env for Bash tools).

In a Claude Code **SessionStart** hook (or any setup that runs while `CLAUDE_ENV_FILE` is set):

```bash
if [ -n "$CLAUDE_ENV_FILE" ]; then
  echo 'export SECOND_BRAIN_PATH="/path/to/second-brain"' >> "$CLAUDE_ENV_FILE"
fi
```

The set-path scripts do this automatically when `CLAUDE_ENV_FILE` is already in the environment.

## Cursor

Injects `env.SECOND_BRAIN_PATH` into the agent session so the skill can resolve the vault without relying only on the parent shell.

User-level `~/.cursor/hooks.json` (merge with existing hooks):

```json
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
```

Example `~/.cursor/hooks/inject-second-brain-path.sh`:

```bash
#!/usr/bin/env bash
# Reads the OS user/machine SECOND_BRAIN_PATH and injects it into the agent session.
path="${SECOND_BRAIN_PATH:-}"
if [ -z "$path" ] && command -v powershell.exe >/dev/null 2>&1; then
  path="$(powershell.exe -NoProfile -Command "[Environment]::GetEnvironmentVariable('SECOND_BRAIN_PATH','User')" 2>/dev/null | tr -d '\r')"
fi
if [ -z "$path" ]; then
  echo '{}'
  exit 0
fi
# JSON-escape minimal path
escaped="${path//\\/\\\\}"
escaped="${escaped//\"/\\\"}"
printf '{"env":{"SECOND_BRAIN_PATH":"%s"}}\n' "$escaped"
exit 0
```

On Windows without bash hooks, a PowerShell hook that prints the same JSON `env` object is fine. After setting the user env var, restart Cursor once so `sessionStart` can pick it up.
