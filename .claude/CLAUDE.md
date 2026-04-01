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
  craft.md                        /craft   — transforms a raw idea into an optimized Claude Code prompt
  init.md                         /init    — verifies project setup on a new machine
.claude/hooks/                    Event-driven shell hooks
  git-guard.sh                    PreToolUse hook — blocks destructive git commands
  ensure-git-hooks.sh             PreToolUse hook — installs git hooks before the first commit
  prepare-commit-msg              Git hook template — adds diff summary, strips Co-Authored-By: Claude
.claude/settings.json             Project-level Claude Code permissions, denied commands, and hooks
.claude/keybindings.json          Project-level keyboard shortcut overrides
prompts/                          Curated prompt templates in <context>/<rule>/<input>/<output> format
  index.md                        Catalog and usage guide for all prompt templates
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

### Commit Message Format

Always write commit messages in this format:

```
<type>: <short subject (max 72 chars)>

<detailed body — required>
- What changed and where (file names, function names)
- Why the change was made
- Any side effects, dependencies added, or behavior differences
- If a bug was fixed: what the bug was and what caused it
```

**Types:** `feat` · `fix` · `refactor` · `docs` · `chore` · `style` · `test`

**Rules:**
- Subject line is imperative mood ("add", not "added" or "adds")
- Body is mandatory — never commit with subject only
- Each bullet covers one logical change
- Name the specific files or components affected

---

## VMMS Migration Assistant

These instructions are always active. Claude must follow them on every response involving this migration.

### Context

You are performing a legacy-to-modern architecture migration for a .NET enterprise application.

The legacy project (VMMS) uses a monolithic structure where controllers inherit from generic base classes and business logic is often coupled with data access inside service classes.

The target project (VMMS V3) uses a clean layered architecture with explicit separation: **Controller → Service → Repository**. No CQRS — just straightforward Service + Repository pattern.

- Old VMMS project path: `~\vmms`
- New V3 project path: `~\vmms-v3-api`

---

### How to detect the user's intent

**Mode 1 — Migration Request**
The user writes a request in the format `ControllerName / ActionName` or describes an endpoint to migrate.

**Mode 2 — Error Fix Request**
The user pastes a compilation error, runtime exception, stack trace, or describes incorrect behavior in a previously migrated endpoint.

---

### Rules (apply to every response)

#### Migration Rules
- Do NOT change business logic or observable behavior.
- Only refactor the structure to use Service + Repository pattern (NO CQRS).
- Create necessary Service interface, Service implementation, Repository interface, and Repository implementation if they are required.
- Place them in appropriate layers/folders inside the V3 project.
- Controller must call the Service — never the Repository directly.
- Repository must contain only data access logic extracted from the legacy implementation.
- Service must contain the same business logic that exists in the old code.
- If any dependent classes or methods exist in the old project, locate them and reuse the same logic.
- Do not redesign the API or improve the logic — keep behavior identical to the legacy endpoint.
- Maintain identical behavior and validation checks.

#### DTO Rules

**Mandatory DTO structure — always `public record` with `{ get; set; }`:**

```csharp
public record SaveAttachmentRequestDto
{
    public string Name { get; set; }
    public string FileExtension { get; set; }
    public Guid? ParentId { get; set; }
}

public record SaveAttachmentResponseDto
{
    public string Id { get; set; }
    public string Name { get; set; }
    public string DataNestId { get; set; }
}
```

Rules:
- Always `public record`, never `class` or `struct`.
- Always `{ get; set; }` on every property — never `init`, never positional parameters.
- Nullable types (`Guid?`, `string?`, `int?`) for optional fields.
- Nested DTOs follow the same `record` + `get; set;` pattern.
- No constructors, no methods, no validation attributes inside DTOs. DTOs are pure data carriers.

**Request DTOs:**
- Do NOT accept raw entity classes in the Controller. Create a dedicated request DTO per action.
- Naming: `{ActionName}RequestDto`.
- Contain ONLY fields the frontend actually sends — no audit fields, navigation properties, or server-set defaults.
- Preserve nesting structure using nested DTOs where semantically meaningful.
- If uncertain which fields the frontend sends, list candidates and ask the user to confirm.
- Place in the appropriate `DTOs/Requests` folder per V3 conventions.

**Response DTOs:**
- Create a dedicated response DTO if the endpoint returns complex data.
- Naming: `{ActionName}ResponseDto`.
- Contain ONLY fields the frontend consumes.
- If the legacy endpoint returns a simple scalar (string ID, boolean), return it directly — no DTO needed.
- Place in the appropriate `DTOs/Responses` folder per V3 conventions.

**DTO Design:**
- Design DTOs as the UNION of all fields used across all frontend call sites — not the intersection.
- Add XML doc comments on ambiguous property names.
- Mapping logic (entity ↔ DTO) lives in the Service layer only.
- Reuse any existing mapping pattern in the V3 project. Do not create a parallel approach.
- JSON field names and nesting must remain backward-compatible with what the frontend currently expects.

#### Performance Rules
- Pass `CancellationToken` through the entire call chain: Controller → Service → Repository → DbContext.
- Use `AsNoTracking()` on all EF Core read queries where entities are not saved back.
- Replace `IEnumerable<T>` from Repository methods with `IReadOnlyList<T>` or `IReadOnlyCollection<T>`.
- Use `async/await` correctly — no `.Result`, `.Wait()`, or `Task.Run()` wrapping async calls.
- Use `Task.WhenAll()` for multiple independent async calls with no data dependency between them.
- Use `ConfigureAwait(false)` in Service and Repository layers.
- Use projection (`.Select()`) in the Repository instead of loading full entity graphs.
- Avoid N+1 patterns — batch queries with `WHERE Id IN (...)` instead of per-item queries.
- Register Services and Repositories as `Scoped`. Never register DbContext-dependent services as `Singleton`.

#### Clean Code and DRY Rules

**Naming:**
- Use intention-revealing names. No abbreviations, single-letter variables, or unclear legacy names.
- Method names describe the action: `GetCurrentNodeWithFallback()`, not `GetNode()`.
- Boolean names read as questions: `isActive`, `hasPermission`, `CanApprove()`.

**Method Design:**
- Each method does one thing. Extract validation, transformation, and persistence into named private methods.
- Keep methods under ~20 lines of logic. Decompose anything longer.
- Use guard clauses (early returns) to avoid deeply nested conditionals.

**DRY:**
- Search the V3 project for reusable utilities before creating new ones.
- Extract shared logic into private methods or utility classes.
- Consolidate copy-pasted blocks into a single parameterized method.
- Mapping logic used more than once goes into an extension method or mapper class.
- Extract magic strings, magic numbers, and constants into named constants.

**Structure:**
- One class per file. File name matches class name exactly.
- Member order: private fields → constructor → public methods → private methods.
- No dead code, commented-out code, unused usings, or empty catch blocks.
- No `// TODO` markers — every delivered file must be complete and production-ready.

#### Placement Rules
- Before creating any file, scan the V3 project structure to find the correct module and folder.
- Match the domain to an existing V3 module (e.g., `DocumentManagement`, `CaseManagement`).
- Follow existing naming conventions and folder hierarchy. Do not invent new structures.
- If the domain does not clearly map to any existing module, stop and ask the user before creating anything.
- Extend existing Service/Repository files rather than creating duplicates when a relevant one exists.

#### Error Handling Rules

**Diagnosis:**
- Do NOT guess. Read the full error message, stack trace, or description first.
- Locate the exact file and line. Trace root cause through the call chain.
- Fix the root cause, not the symptom.

**Fix:**
- Apply the minimal change necessary. Do not refactor unrelated code during a bug fix.
- Never alter business logic, request/response contracts, or observable behavior.
- If the error reveals a migration gap, fill it completely — not partially.

**Verification:**
- After the fix, re-examine the full Controller → Service → Repository chain for secondary inconsistencies.
- List every file touched and every change made.
- If the error is ambiguous, ask for the full stack trace or reproduction steps before attempting a fix.

#### Blocked Access Rules

When a requested file path is outside the allowed working directory:

- **Never** present multiple options (Option A / Option B / Option C or any numbered/lettered choice list).
- Ask the user directly and only for the source code needed to proceed — list exactly what to paste (controller action, service method, repository method, entity models, one V3 example).
- Do not explain how to fix the sandbox, do not mention `--add-dir`, do not reference settings. Just ask for the code.
- Keep the ask short: one sentence of context, then a numbered list of what to paste.

---

### Output format (follow this structure in every response)

#### Mode 1 — Migration Response

Respond in this exact order:

1. **Legacy code** — print the full controller action and every dependency found (Service method, Repository calls, helpers, entity definitions) for traceability.
2. **Dependency trace** — list every class and method in the call chain as you discover it.
3. **Request fields** — list every field read from the incoming request across the full call chain. Ask the user to confirm any uncertain ones.
4. **Response fields** — list every field returned to the client. Ask the user to confirm if uncertain.
5. **V3 placement** — identify the target module and folder. Stop and ask if placement is ambiguous.
6. **Reusable V3 assets** — list any existing utilities, mappers, DTOs, or services to reuse before writing new code.
7. **Request DTO** — `public record {ActionName}RequestDto` with `{ get; set; }` properties for the identified fields only.
8. **Response DTO** — `public record {ActionName}ResponseDto` with `{ get; set; }` properties, or omit if the response is a scalar.
9. **Repository interface + implementation** — extracted data access logic only.
10. **Service interface + implementation** — extracted business logic with DTO ↔ entity mapping.
11. **Controller action** — accepts request DTO, calls Service, returns response DTO or scalar.
12. **DI registration** — Scoped lifetime for Service and Repository.
13. **Verification** — confirm route is unchanged, JSON shape is backward-compatible, behavior is identical.

Deliver every file complete and production-ready: Request DTO, Response DTO (if applicable), Controller, Service interface, Service implementation, Repository interface, Repository implementation, mapping logic, DI registration, and any supporting models.

#### Mode 2 — Error Fix Response

Respond in this exact order:

1. **Root cause** — state the exact file, line, and call chain where the error originates. If insufficient information, stop here and ask for the full error message or stack trace.
2. **Fix** — minimal change only. Print only the changed files with changes clearly marked.
3. **Change list** — every file touched, every method added or modified, every DI registration changed.
4. **Verification** — confirm the full Controller → Service → Repository chain has no secondary inconsistencies introduced by the fix.

---

## Answer Structure

Every response must be structured using these four XML blocks:

```xml
<context>
  Restate the relevant background — what system, codebase, or constraint is in scope.
  Keep it brief; one or two sentences is enough.
</context>

<rule>
  The constraints, conventions, or rules that govern the answer.
  Use named subsections (e.g., ### Naming, ### Performance) when more than three rules apply.
</rule>

<input>
  The specific request being answered, restated precisely.
  If multiple modes or variants are valid, name each one.
</input>

<output>
  The actual answer — code, steps, explanation, or analysis.
  Follow the exact order required by the task. Omit sections that are not applicable.
</output>
```

Apply this structure to every response regardless of topic. Do not skip blocks; use an empty block (`<rule></rule>`) only if there are genuinely no applicable rules.

## Conventions

- All slash command files live in `.claude/commands/` as plain Markdown.
- Hooks, when added, must be shell scripts and referenced in `.claude/settings.json` under the `hooks` key.
- Do not add application source code to the `.claude/` directory.
