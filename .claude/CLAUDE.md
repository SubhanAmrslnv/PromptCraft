# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

PromptCraft — a toolkit for writing and iterating on effective Claude Code prompts.
The repository currently contains Claude Code configuration only; no application source code exists yet.

## Repository Layout

```
.claude/                          Claude Code configuration root
.claude/CLAUDE.md                 This file — project guidance for Claude Code
.claude/commands/                 Custom slash commands (Markdown files)
  craft.md                        /craft — transforms a raw idea into an optimized Claude Code prompt
  init.md                         /init  — verifies project setup on a new machine
.claude/hooks/                    Event-driven shell hooks
  git-guard.sh                    PreToolUse hook — blocks destructive git commands
  ensure-git-hooks.sh             PreToolUse hook — installs git hooks before the first commit
  prepare-commit-msg              Git hook template — adds diff summary, strips Co-Authored-By: Claude
.claude/settings.json             Project-level Claude Code permissions, denied commands, and hooks
.claude/keybindings.json          Project-level keyboard shortcut overrides
```

## Slash Commands

| Command | File | Purpose |
|---|---|---|
| `/craft <idea>` | `commands/craft.md` | Generate a precise Claude Code prompt from a rough request |
| `/init` | `commands/init.md` | Verify and repair Claude Code setup on this machine |

## Claude Code Configuration

- **Settings:** `.claude/settings.json` — controls allowed/denied tool permissions and wires hooks.
- **Commands:** `.claude/commands/` — each `.md` file becomes a `/slash-command`. The filename (without extension) is the command name.
- **Hooks:** `.claude/hooks/` — shell scripts triggered on Claude Code lifecycle events. `ensure-git-hooks.sh` runs as a `PreToolUse` hook on every Bash call; when it detects a `git commit`, it installs `prepare-commit-msg` into `.git/hooks/` if not already present.
- **Keybindings:** `.claude/keybindings.json` — project-level key overrides.

## Git Restrictions

The following destructive git commands are blocked by `.claude/hooks/git-guard.sh` (a `PreToolUse` hook). Claude must not run them — the hook will block the call with exit code 2 and explain why:

| Blocked command | Reason |
|---|---|
| `git push --force` / `git push -f` | Overwrites remote history |
| `git reset --hard` | Discards uncommitted work |
| `git clean -f` / `git clean -fd` | Deletes untracked files permanently |
| `git checkout -- <file>` / `git restore .` | Silently discards local changes |
| `git branch -D` | Force-deletes branches without merge check |
| `git rebase -i` | Interactive rebase rewrites history |
| `git commit --amend` | Rewrites published commits |
| `git reflog delete` | Destroys recovery history |

## Git Commit Behavior

Every commit automatically runs `.git/hooks/prepare-commit-msg`, which:
1. Strips any `Co-Authored-By: Claude` line from the message
2. Appends a `git diff --cached --stat` summary as the commit body if no body was written

## Conventions

- All slash command files live in `.claude/commands/` as plain Markdown.
- Hooks, when added, must be shell scripts and referenced in `.claude/settings.json` under the `hooks` key.
- Do not add application source code to the `.claude/` directory.