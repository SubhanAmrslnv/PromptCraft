#!/usr/bin/env bash
# PreToolUse hook — blocks destructive git commands before they run.
# Receives Claude Code tool event JSON on stdin.

input=$(cat)

cmd=$(printf '%s' "$input" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('command', ''))
except Exception:
    pass
" 2>/dev/null || true)

# Only inspect git commands
printf '%s\n' "$cmd" | grep -q 'git ' || exit 0

blocked=""

case "$cmd" in
  *"git push --force"* | *"git push -f "* | *"git push -f"$'\n'*)
    blocked="git push --force — rewrites remote history and can destroy others' work" ;;
  *"git reset --hard"*)
    blocked="git reset --hard — permanently discards uncommitted changes" ;;
  *"git clean -f"* | *"git clean -fd"* | *"git clean -fx"*)
    blocked="git clean -f — permanently deletes untracked files" ;;
  *"git checkout -- "* | *"git restore ."*)
    blocked="git checkout --/restore . — silently discards local changes" ;;
  *"git branch -D"*)
    blocked="git branch -D — force-deletes a branch without a merge check" ;;
  *"git rebase -i"*)
    blocked="git rebase -i — interactive rebase rewrites commit history" ;;
  *"git commit --amend"*)
    blocked="git commit --amend — rewrites an existing commit (dangerous on published branches)" ;;
  *"git reflog delete"*)
    blocked="git reflog delete — destroys recovery history" ;;
esac

if [[ -n "$blocked" ]]; then
    printf 'Blocked: %s\nAsk the user before running this command.\n' "$blocked" >&2
    exit 2
fi