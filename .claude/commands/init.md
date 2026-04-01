Initialize the Claude Code configuration for this PromptCraft project on this machine.

Perform the following steps in order:

## 1. Verify project structure

Check that the following directories exist under `.claude/`. Create any that are missing:
- `.claude/commands/`
- `.claude/hooks/`

## 2. Verify commands

Check that `.claude/commands/craft.md` exists.
If it is missing, tell the user — this file is the core `/craft` slash command and must be restored from version control.

## 3. Verify settings.json

Check that `.claude/settings.json` exists and is valid JSON.
If the file is missing or empty, write the following default content to it:

```json
{
  "permissions": {
    "allow": [],
    "deny": []
  }
}
```

Do not overwrite an existing non-empty `settings.json`.

## 4. Verify ANTHROPIC_API_KEY

Check if the `ANTHROPIC_API_KEY` environment variable is set.
If it is not set, remind the user to add it to their shell profile (`~/.bashrc` or `~/.zshrc`):

```sh
export ANTHROPIC_API_KEY="sk-ant-..."
```

This key is required when using Claude API features from within PromptCraft.

## 5. Report

Print a concise summary table:

| Item | Status |
|---|---|
| `.claude/commands/` | ✓ exists / ✗ created |
| `.claude/hooks/` | ✓ exists / ✗ created |
| `.claude/commands/craft.md` | ✓ exists / ✗ missing |
| `.claude/settings.json` | ✓ valid / ✗ written default / ✗ missing |
| `ANTHROPIC_API_KEY` | ✓ set / ✗ not set |

List any manual steps the user still needs to take.