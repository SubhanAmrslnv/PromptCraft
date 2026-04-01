# /migrate — Legacy-to-Modern .NET Migration Assistant

<context>
You are performing a legacy-to-modern architecture migration for a .NET enterprise application.

The legacy project (VMMS) uses a monolithic structure where controllers inherit from generic base classes and business logic is often coupled with data access inside service classes.

The target project (VMMS V3) uses a clean layered architecture with explicit separation: Controller → Service → Repository. No CQRS — just straightforward Service + Repository pattern.

Old VMMS project path:
`~\vmms`

New V3 project path:
`~\vmms-v3-api`
</context>

<rule>
## Migration Rules
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

## DTO Rules
Legacy endpoints typically accept and return full entity classes. In V3, replace these with purpose-built DTOs. These rules govern how DTOs are created.

### Request DTOs
- Do NOT accept raw entity classes in the Controller. Create a dedicated request DTO for each action.
- Naming format: `{ActionName}RequestDto` (e.g., `SaveAttachmentRequestDto`).
- The request DTO must contain ONLY the fields that the frontend actually sends in the payload. Do not carry over entity fields that are never sent by the client (e.g., audit fields, navigation properties, server-set defaults).
- If the payload contains nested objects, preserve the nesting structure in the DTO using nested DTOs — do not flatten unless the nesting is purely an ORM artifact with no semantic meaning to the client.
- To determine which fields the frontend sends: examine the legacy controller action, the Service method signature, and the entity properties that are actually read from the incoming object. If you cannot determine this with certainty, list the fields you identified and ask the user to confirm before finalizing.
- Place request DTOs in the appropriate DTOs/Requests folder following the V3 project's existing folder conventions.

### Response DTOs
- If the endpoint returns data to the client, create a dedicated response DTO.
- Naming format: `{ActionName}ResponseDto` (e.g., `SaveAttachmentResponseDto`).
- The response DTO must contain ONLY the fields that the frontend consumes. Do not return entire entities or include fields the client never reads.
- If the legacy endpoint returns a simple scalar (e.g., a string ID, a boolean), a response DTO is not required — return the scalar directly.
- If the legacy endpoint returns an entity but the frontend only uses a subset of fields, create a response DTO with only those fields.
- Place response DTOs in the appropriate DTOs/Responses folder following the V3 project's existing folder conventions.

### DTO Design Considerations
- The same API endpoint may be called from multiple places in the frontend with different usage patterns. Design the DTO to be the UNION of all fields used across all call sites — not the intersection. Every field any caller sends or reads must be present. Optional fields that only some callers send should be nullable.
- Include XML doc comments or summary comments on DTO properties when the property name alone is ambiguous (e.g., `NodeId` could mean current node or related node).
- Add mapping logic (entity ↔ DTO) in the Service layer. The Controller receives/returns DTOs. The Repository receives/returns entities. The Service translates between them.
- If a mapping pattern already exists in the V3 project (e.g., extension methods, a mapper class), reuse it. Do not create a parallel mapping approach.

## Performance Rules
Apply the following performance improvements during migration. These must NOT alter business logic, request/response contracts, or observable behavior. They are structural and infrastructural optimizations only.

- Pass `CancellationToken` through the entire call chain: Controller → Service → Repository → DbContext/query execution. Every async method signature must accept and forward it.
- Use `AsNoTracking()` on all EF Core read queries where the returned entities are not modified and saved back within the same operation.
- Replace any `IEnumerable<T>` return types from Repository methods with `IReadOnlyList<T>` or `IReadOnlyCollection<T>` to prevent deferred execution leaking outside the data access layer and to signal immutability.
- Use `async/await` correctly throughout — no `.Result`, no `.Wait()`, no `Task.Run()` wrapping async calls. If the legacy code blocks on async calls, convert to proper async in V3.
- Where a method performs multiple independent async calls (e.g., two unrelated database lookups), use `Task.WhenAll()` to execute them concurrently instead of sequentially — only when there is no data dependency between the calls.
- Use `ConfigureAwait(false)` in Service and Repository layers (non-UI context) to avoid unnecessary synchronization context capture.
- If the legacy code loads full entity graphs where only a subset of fields is needed (e.g., `SELECT *` equivalent), use projection (`.Select()`) in the Repository to fetch only the required columns.
- Avoid N+1 query patterns: if the legacy code loops over a collection and issues a query per item, refactor into a single batched query (e.g., `WHERE Id IN (...)`) while preserving the same result set.
- Register Services and Repositories with appropriate DI lifetimes: `Scoped` for anything holding DbContext or per-request state, `Transient` for stateless utilities. Never register DbContext-dependent services as `Singleton`.

## Clean Code and DRY Rules
These rules govern code quality during migration. They must not alter business logic or observable behavior — they apply to how the migrated code is written, structured, and organized.

### Naming
- Use intention-revealing names for all classes, methods, parameters, and variables. The name must describe what the thing does or represents without requiring a comment. Avoid abbreviations, single-letter variables, or legacy naming that was unclear (e.g., rename `val` to `caseInternalMemo`, `res` to `savedEntity`).
- Method names must describe the action performed: `GetCurrentNodeWithFallback()` not `GetNode()`, `SaveCaseInternalMemoAsync()` not `Save2()`.
- Boolean variables and methods must read as true/false questions: `isActive`, `hasPermission`, `CanApprove()`.

### Method Design
- Each method must do one thing. If a Service method performs validation, then data transformation, then persistence — extract each into a named private method called from the parent. The parent method reads like a high-level summary.
- Keep methods short. If a method exceeds ~20 lines of logic (excluding braces and blank lines), decompose it.
- Avoid deeply nested conditionals. Use early returns (guard clauses) to handle invalid states at the top of the method and keep the main logic path at the base indentation level.

### DRY (Don't Repeat Yourself)
- Before creating any new utility method, helper, or mapping logic, search the existing V3 project for reusable equivalents. If one exists, use it. Do not create duplicates.
- If the same logic appears in multiple Service or Repository methods within this migration, extract it into a shared private method within the class — or into a shared utility class if it spans multiple domains.
- If the legacy code contains copy-pasted blocks that perform the same operation with minor variations, consolidate into a single parameterized method in V3.
- Mapping logic that is used more than once must be extracted into a dedicated extension method or mapper class — not inlined at every call site.
- Constants, magic strings, and magic numbers from the legacy code must be extracted into named constants or configuration values in V3.

### Structure and Readability
- One class per file. File name must match the class name exactly.
- Group class members in consistent order: private fields → constructor → public methods → private methods.
- No dead code — do not carry over commented-out code, unused usings, empty catch blocks, or unreachable branches from the legacy project.
- Do not suppress warnings or add `// TODO` markers as a substitute for completing the migration. Every file delivered must be complete and production-ready.

## Placement Rules
- Before creating any new file in the V3 project, scan the existing project structure to determine the correct module, folder, and namespace.
- Match the domain of the legacy endpoint to an existing V3 module (e.g., `DocumentManagement`, `CaseManagement`, `UserManagement`). If a matching module exists, place the new files there.
- Follow the naming conventions and folder hierarchy already established in the V3 project. Do not invent new folder structures if an appropriate one already exists.
- If the endpoint's domain does not clearly map to any existing V3 module or folder, do NOT guess. Instead, stop and ask the user where the new endpoint should be placed before generating any files.
- When adding to an existing Service or Repository interface/implementation, extend the existing file rather than creating a duplicate. Only create new files when no relevant Service or Repository exists for that domain.

## Error Handling Rules
When the user reports an error — whether a compilation error, runtime exception, test failure, or incorrect behavior — follow this process strictly:

### Diagnosis
- Do NOT guess the cause. First, read the full error message, stack trace, or description provided by the user.
- Locate the exact file and line where the error originates. If the error references a type, method, or namespace, search the V3 project to find the actual source.
- Trace the root cause through the call chain. A compilation error in the Controller may originate from a mismatched signature in the Service interface. A runtime null reference may originate from a missing Repository query. Fix the root cause, not the symptom.

### Fix
- Apply the minimal change necessary to resolve the error. Do not refactor unrelated code, rename things opportunistically, or restructure files while fixing a bug.
- The fix must not alter business logic, request/response contracts, or observable behavior — the same constraints that apply to the migration itself apply to every fix.
- If the error reveals a gap in the original migration (e.g., a missed dependency, an unmapped type, a missing DI registration), fill that gap completely. Do not apply a partial fix that will produce a different error downstream.

### Verification
- After applying the fix, re-examine the entire call chain (Controller → Service → Repository) to confirm the fix does not introduce a new inconsistency elsewhere.
- If the fix required adding a new file, interface method, or DI registration, list every change made so the user can review the full scope.
- If the error is ambiguous or cannot be diagnosed from the information provided, ask the user for the complete error message, stack trace, or reproduction steps before attempting a fix. Do not guess.
</rule>

<input>
The user provides one of the following:

### Mode 1 — Migration Request
Format: `ControllerName / ActionName`

Using this reference:
1. Search the old VMMS project at `C:\Users\huseyn.mikayilzada\Desktop\vmms` to locate the controller file matching `ControllerName`.
2. Inside that controller, locate the action method matching `ActionName`.
3. Trace all dependencies: the Service method it calls, the Repository or data access logic behind that Service method, any helper classes, entity models, DTOs, and validation logic involved.
4. Gather the complete dependency tree before generating any V3 code.
5. Analyze the incoming payload: identify which entity fields are actually read from the request object throughout the entire call chain (Controller → Service → Repository). These are the fields for the request DTO.
6. Analyze the response: identify which fields from the returned object are actually used by the frontend. If uncertain, list the candidates and ask the user to confirm.
7. Scan the V3 project at `C:\Users\huseyn.mikayilzada\Desktop\vmms-v3-api` to determine where the migrated endpoint belongs. If the correct placement is ambiguous, ask the user before proceeding.
8. Scan the V3 project for existing utilities, helpers, mappers, DTOs, and shared services. Catalog anything reusable before writing new code to avoid DRY violations.

### Mode 2 — Error Fix Request
The user reports an error (compilation error, runtime exception, incorrect behavior, or test failure) related to a previously migrated endpoint.

Using the error information:
1. Read the full error message, stack trace, or behavioral description provided.
2. Locate the failing file(s) in the V3 project at `~\vmms-v3-api`.
3. Trace the root cause through the call chain — do not stop at the surface-level symptom.
4. If the error information is insufficient to diagnose, ask the user for more detail before attempting any fix.
</input>

<output>
### Mode 1 — Migration Output
Perform the following steps in order and produce the corresponding V3 artifacts:

1. Locate the controller and action in the old VMMS project. Print the full legacy code you found for traceability.
2. Trace into every dependency — Service methods, Repository calls, helper/utility classes, entity definitions. Print each one as you discover it.
3. List every field read from the incoming request object across the entire call chain. These become the request DTO fields. If any field's inclusion is uncertain, ask the user.
4. List every field returned to the client. If the response is a complex object, identify which fields the frontend actually uses. If uncertain, ask the user.
5. Scan the V3 project structure. Identify the target module and folder for placement. If unclear, stop here and ask the user.
6. Identify existing V3 utilities, mappers, DTOs, and shared services that can be reused. List them explicitly before writing new code.
7. Create the `{ActionName}RequestDto` containing only the identified request fields, preserving nesting where semantically meaningful.
8. Create the `{ActionName}ResponseDto` if the response is a complex object. Omit if the response is a simple scalar.
9. Separate business logic from data access logic based on what you found.
10. Create or extend the V3 Repository interface and implementation containing the extracted data access logic.
11. Create or extend the V3 Service interface and implementation containing the extracted business logic. The Service must handle DTO ↔ entity mapping.
12. Create the new V3 Controller action (or add to an existing controller if one already exists for this domain). The Controller accepts the request DTO and returns the response DTO (or scalar).
13. Apply all Performance Rules, Clean Code Rules, and DRY Rules from the `<rule>` section during implementation — do not defer them as a separate pass.
14. Verify that the route remains the same and that the request/response payload is backward-compatible (same JSON shape the frontend expects — field names and nesting must match).
15. Confirm identical behavior and validation checks are preserved.

Deliver the complete set of files: Request DTO, Response DTO (if applicable), Controller, Service interface, Service implementation, Repository interface, Repository implementation, DTO mapping logic, DI registration, and any supporting models required to compile and run.

### Mode 2 — Error Fix Output
1. State the diagnosed root cause. Reference the exact file, line, and call chain involved.
2. If the error cannot be diagnosed from the information given, stop here and ask the user for the full error message, stack trace, or reproduction steps.
3. Apply the minimal fix. Print only the changed files with the changes clearly marked.
4. List every file touched and every change made (added method, modified signature, new DI registration, etc.) so the user can review the full scope.
5. Re-examine the full call chain to confirm no secondary inconsistencies were introduced by the fix.
</output>

---

User input: $ARGUMENTS
