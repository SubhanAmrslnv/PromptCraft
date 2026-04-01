# Prompts Library

A collection of reusable prompt templates. Every prompt and every response follows the structured XML format: `<context>` → `<rule>` → `<input>` → `<output>`.

## How to use

Copy a template's `<input>` block, fill in your specific request, and paste the full prompt into the chat.

## Templates

| Name | Domain | File | What it does |
|---|---|---|---|
| Code migration | .NET / any | [See example below](#example-code-migration) | Migrate a function from one codebase / version to another |

---

## Prompt structure

```xml
<context>
  Background — what system, codebase, or domain is involved.
  What already exists and what the goal is.
</context>

<rule>
  Constraints and conventions Claude must follow.
  Grouped into named sections (### Name) when more than three rules apply.
</rule>

<input>
  The specific request.
  Modes, variants, or examples of valid inputs.
</input>

<output>
  The exact format Claude must respond with.
  Step-by-step order, required sections, and what to omit.
</output>
```

---

## Example: Code migration

Use this template when you want to migrate a function from an old project to a new one without changing any logic.

```xml
<context>
  Old project: C:\1-Projects\vmms  (.NET 4.6.2, Oracle 19c, legacy service pattern)
  New project: C:\1-Projects\vmms-v3-api  (.NET 8, Oracle 19c, Controller → Service → Repository with Dapper)
</context>

<rule>
  ### Migration
  - Do NOT change business logic or observable behavior.
  - Refactor structure only: Controller → Service → Repository.
  - Use Dapper for all data access — no Entity Framework.
  - Keep SQL identical to the original; only adjust parameter binding for Dapper.

  ### DTO Structure
  - Always public record with { get; set; } properties.
  - Naming: {ActionName}RequestDto / {ActionName}ResponseDto.

  ### Performance
  - Pass CancellationToken through the full call chain.
  - Use async/await correctly — no .Result or .Wait().

  ### Placement
  - Match the domain to an existing V3 module before creating new files.
  - Extend existing Service/Repository files when a relevant one exists.
</rule>

<input>
  Migrate: CaseController / UpdateCaseStatus

  Paste below:
  1. The controller action
  2. The service method(s) it calls
  3. The repository / data access method(s) those call
  4. Any entity or model classes involved
  5. One example from vmms-v3-api showing an existing Controller + Service + Repository
</input>

<output>
  Respond in this order:
  1. Legacy code — full action + every dependency found
  2. Dependency trace — every class and method in the call chain
  3. Request fields — every field read from the request; ask if uncertain
  4. Response fields — every field returned to the client; ask if uncertain
  5. V3 placement — target module and folder; stop and ask if ambiguous
  6. Reusable V3 assets — existing utilities or DTOs to reuse
  7. Request DTO
  8. Response DTO (omit if scalar)
  9. Repository interface + implementation (Dapper SQL)
  10. Service interface + implementation
  11. Controller action
  12. DI registration
  13. Verification — route unchanged, behavior identical
</output>
```
