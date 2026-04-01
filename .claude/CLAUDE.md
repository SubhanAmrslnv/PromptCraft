# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

PromptCraft — a toolkit for writing and iterating on effective Claude Code prompts.
The repository currently contains Claude Code configuration only; no application source code exists yet.

## Repository Layout

```
.claude/                  Claude Code configuration root
.claude/CLAUDE.md         This file — project guidance for Claude Code
.claude/commands/         Custom slash commands (Markdown files)
  craft.md                /craft — transforms a raw idea into an optimized Claude Code prompt
  init.md                 /init  — verifies project setup on a new machine
.claude/hooks/            Event-driven shell hooks (empty — none defined yet)
.claude/settings.json     Project-level Claude Code permissions and settings
.claude/keybindings.json  Project-level keyboard shortcut overrides
```

## Slash Commands

| Command | File | Purpose |
|---|---|---|
| `/craft <idea>` | `commands/craft.md` | Generate a precise Claude Code prompt from a rough request |
| `/init` | `commands/init.md` | Verify and repair Claude Code setup on this machine |

## Claude Code Configuration

- **Settings:** `.claude/settings.json` — controls allowed/denied tool permissions for this project.
- **Commands:** `.claude/commands/` — each `.md` file becomes a `/slash-command`. The filename (without extension) is the command name.
- **Hooks:** `.claude/hooks/` — shell scripts triggered on Claude Code lifecycle events (PreToolUse, PostToolUse, Stop, etc.). None are active yet.
- **Keybindings:** `.claude/keybindings.json` — project-level key overrides.

## Conventions

- All slash command files live in `.claude/commands/` as plain Markdown.
- Hooks, when added, must be shell scripts and referenced in `.claude/settings.json` under the `hooks` key.
- Do not add application source code to the `.claude/` directory.