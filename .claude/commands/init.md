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
    "deny": [
      "Bash(git push --force*)",
      "Bash(git push -f*)",
      "Bash(git reset --hard*)",
      "Bash(git clean -f*)",
      "Bash(git clean -fd*)",
      "Bash(git checkout -- *)",
      "Bash(git restore .)",
      "Bash(git branch -D*)",
      "Bash(git rebase -i*)",
      "Bash(git commit --amend*)",
      "Bash(git reflog delete*)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/ensure-git-hooks.sh"
          }
        ]
      }
    ]
  }
}
```

Do not overwrite an existing non-empty `settings.json`.

## 4. Install git hooks

Check if `.git/hooks/prepare-commit-msg` exists.
If it does not, copy `.claude/hooks/prepare-commit-msg` to `.git/hooks/prepare-commit-msg` and make it executable:

```sh
cp .claude/hooks/prepare-commit-msg .git/hooks/prepare-commit-msg
chmod +x .git/hooks/prepare-commit-msg
```

## 5. Report

Print a concise summary table:

| Item | Status |
|---|---|
| `.claude/commands/` | ✓ exists / ✗ created |
| `.claude/hooks/` | ✓ exists / ✗ created |
| `.claude/commands/craft.md` | ✓ exists / ✗ missing |
| `.claude/settings.json` | ✓ valid / ✗ written default / ✗ missing |
| `.git/hooks/prepare-commit-msg` | ✓ installed / ✗ installed now |

List any manual steps the user still needs to take.
