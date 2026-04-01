#!/usr/bin/env bash
# PreToolUse hook — when Claude runs a git commit, ensure project git hooks are installed.
# Receives Claude Code tool event JSON on stdin.

input=$(cat)

# Extract the bash command from the tool input
cmd=$(printf '%s' "$input" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('command', ''))
except Exception:
    pass
" 2>/dev/null || true)

# Only act on git commit commands
printf '%s\n' "$cmd" | grep -q 'git commit' || exit 0

repo=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0

src="$repo/.claude/hooks/prepare-commit-msg"
dest="$repo/.git/hooks/prepare-commit-msg"

if [[ -f "$src" && ! -f "$dest" ]]; then
    cp "$src" "$dest"
    chmod +x "$dest"
fi
