#!/usr/bin/env bash
# PreToolUse hook — blocks destructive and dangerous commands before they run.
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

[[ -z "$cmd" ]] && exit 0

blocked=""

# ── Dangerous filesystem commands ─────────────────────────────────────────────
case "$cmd" in
  *"rm -rf /"* | *"rm -rf ~"* | *"rm -rf $HOME"*)
    blocked="rm -rf on root/home — would destroy the filesystem" ;;
  *"rm -rf"*)
    # Allow only clearly scoped temp/build directories
    if ! printf '%s' "$cmd" | grep -qE 'rm -rf .*(tmp|temp|build|dist|\.pyc|__pycache__|node_modules)'; then
      blocked="rm -rf on a non-temporary directory — confirm with the user first"
    fi ;;
esac

# ── Secret file staging ────────────────────────────────────────────────────────
if [[ -z "$blocked" ]]; then
  case "$cmd" in
    *"git add"* | *"git stage"*)
      if printf '%s' "$cmd" | grep -qiE '\.(env|key|pem|pfx|p12|secret|credentials|token)(\s|$|")'; then
        blocked="staging a secret/credential file — these must never be committed"
      fi ;;
  esac
fi

# ── Direct push to protected branches ─────────────────────────────────────────
if [[ -z "$blocked" ]]; then
  case "$cmd" in
    *"git push"*":main"* | *"git push"*" main"* | \
    *"git push"*":master"* | *"git push"*" master"* | \
    *"git push"*":develop"* | *"git push"*" develop"*)
      if printf '%s' "$cmd" | grep -qE 'push --force|push -f'; then
        blocked="force-push to a protected branch (main/master/develop)"
      fi ;;
  esac
fi

# ── Destructive git commands ───────────────────────────────────────────────────
if [[ -z "$blocked" ]]; then
  case "$cmd" in
    *"git push --force"* | *"git push -f "* | *"git push -f"*)
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
fi

# ── Exploit and attack tools ───────────────────────────────────────────────────
if [[ -z "$blocked" ]]; then
  case "$cmd" in
    *"sqlmap"* | *"nmap "* | *"hydra "* | *"hashcat"* | \
    *"metasploit"* | *"msfconsole"* | *"msfvenom"*)
      blocked="exploit/attack tool detected — not permitted in this workspace" ;;
  esac
fi

# ── Reverse shell / code execution patterns ───────────────────────────────────
if [[ -z "$blocked" ]]; then
  if printf '%s' "$cmd" | grep -qE '(curl|wget).*(https?://).+\|\s*(bash|sh|python|perl)'; then
    blocked="curl/wget piped to shell — remote code execution pattern"
  fi
  if printf '%s' "$cmd" | grep -qE 'bash\s+-i\s+>&|/dev/tcp/|nc\s+-e\s+/bin/(bash|sh)'; then
    blocked="reverse shell pattern detected"
  fi
  if printf '%s' "$cmd" | grep -qE 'base64\s+-d.*\|\s*(bash|sh|python)'; then
    blocked="base64-decoded execution pattern — potential obfuscated payload"
  fi
fi

if [[ -n "$blocked" ]]; then
    printf 'Blocked: %s\nAsk the user before running this command.\n' "$blocked" >&2
    exit 2
fi