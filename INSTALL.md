# Installation Guide

## Prerequisites

- Git
- [Claude Code](https://claude.ai/code) CLI installed

Verify Claude Code is installed:

```sh
claude --version
```

If not installed, follow the official setup at https://claude.ai/code.

## Setup

### 1. Clone the repository

```sh
git clone <repo-url>
```

### 2. Open a terminal in the `.claude` folder

```sh
cd PromptCraft/.claude
```

### 3. Launch Claude Code

```sh
claude
```

### 4. Run the init command

Inside Claude Code, type:

```
/init
```

This checks that all required files are in place and your `settings.json` is valid.

### 5. Set your API key (if not already set)

If `/init` reports `ANTHROPIC_API_KEY` is missing, add it to your shell profile:

```sh
# ~/.bashrc or ~/.zshrc
export ANTHROPIC_API_KEY="sk-ant-..."
```

Then reload your shell:

```sh
source ~/.bashrc   # or source ~/.zshrc
```

## Verify

After setup, run a quick test:

```
/craft add a hello world endpoint to src/server.ts
```

Claude Code should return a well-structured prompt. If it does, everything is working.

## Troubleshooting

**`/craft` or `/init` not found**
Make sure you launched `claude` from inside the `.claude` directory, or from the repo root — Claude Code looks for `.claude/commands/` relative to the working directory.

**`ANTHROPIC_API_KEY` not recognized after adding to profile**
Run `source ~/.bashrc` (or `~/.zshrc`) in your current terminal, then relaunch `claude`.
