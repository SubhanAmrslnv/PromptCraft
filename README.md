# PromptCraft

A toolkit for writing precise, effective prompts for Claude Code.

## What's inside

| Command | What it does |
|---|---|
| `/craft <idea>` | Turns a rough request into an optimized Claude Code prompt |
| `/init` | Verifies your Claude Code setup is wired correctly |

## Quick start

```sh
git clone <repo-url>
cd PromptCraft/.claude
claude
```

Then in Claude Code:

```
/init
```

Run `/init` once to verify everything is set up. After that, use `/craft` to generate prompts:

```
/craft fix the bug where the login form submits with empty fields
/craft add pagination to the user list endpoint
/craft explain what the middleware chain in src/auth does
```

## Requirements

- [Claude Code](https://claude.ai/code) installed and authenticated

## Prompts library

`prompts/` contains reusable prompt templates. Every template follows the structured XML format:

```
<context> → <rule> → <input> → <output>
```

See [`prompts/index.md`](prompts/index.md) for the full catalog.

## See also

- `INSTALL.md` — step-by-step setup guide
- `.claude/CLAUDE.md` — project conventions and file layout
