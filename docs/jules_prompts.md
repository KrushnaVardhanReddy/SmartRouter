# Jules Prompt Templates (SmartRouter)

When invoking `scripts/jules_submit.py` to delegate a task to Jules (Tier 2), use the templates below. Always include the Mandatory Rules block at the top of the prompt.

## 🔴 MANDATORY RULES BLOCK
Copy and paste this at the top of every Jules prompt:

```text
MANDATORY RULES — VIOLATION = REJECTED PR:
1. NEVER comment out or stub existing implementation code.
2. NEVER replace a working function body with # TODO or pass.
3. All modified files must pass: `ruff check .` && `mypy .`
4. If a test fails, FIX the code — do NOT delete or skip tests.
5. Do NOT modify contracts/openapi.yaml unless explicitly told to.
6. All new modules must include a corresponding test file in tests/.
7. Commit message must start with "jules: " prefix.
```

---

## Template: Pydantic Model Generation
Use this when we've updated `contracts/openapi.yaml` and need the Python models to match.

```text
<PASTE MANDATORY RULES BLOCK>

Update the Pydantic models in `smartrouter/api/models.py` to match the latest schemas defined in `contracts/openapi.yaml` and `contracts/config_schema.json`.

Requirements:
- Ensure all fields, types, and validation logic match the OpenAPI spec.
- Use `pydantic.Field` for descriptions and default values.
- Do NOT touch the routing logic in `smartrouter/router/`.
- Run `ruff check .` and `mypy .` to ensure typing is correct.

Commit: "jules: update pydantic models from openapi spec"
```

## Template: Unit Test Task
Use this to delegate test coverage for a specific module.

```text
<PASTE MANDATORY RULES BLOCK>

Write comprehensive `pytest` unit tests for [FILE_PATH].
Create or update the test file at [TEST_PATH].

Project context:
- Python FastAPI project using async HTTP clients (`httpx`)
- Run tests with: `pytest [TEST_PATH] -v`

Test coverage required:
1. Happy path: [DESCRIBE EXPECTED BEHAVIOR]
2. Error handling: [DESCRIBE EXCEPTIONS OR FAILURES TO MOCK]
3. Edge cases (empty payloads, missing optional fields)
4. [ADD SPECIFIC METHODS TO TEST]

Do NOT modify any business logic in `smartrouter/` unless fixing a bug exposed by the tests.
Run `pytest` and confirm ALL tests pass.
Commit: "jules: add tests for [component]"
```

## Template: Lint & Formatting Fixes
Use this to keep the codebase clean without burning our time.

```text
<PASTE MANDATORY RULES BLOCK>

Fix all linting and typing warnings across the repository.

Instructions:
1. Run `ruff format .` to fix formatting.
2. Run `ruff check . --fix` to auto-fix linting issues.
3. Run `mypy .` and manually fix any remaining type hinting errors.
4. Do NOT change any core business logic, API contracts, or routing thresholds.

Run the tests (`pytest`) to ensure your formatting didn't break anything.
Commit: "jules: fix formatting and type hints"
```

## Template: Boilerplate & Config Setup
Use this when we need standard Python/Docker boilerplate files.

```text
<PASTE MANDATORY RULES BLOCK>

Create the initial boilerplate for [COMPONENT/FILE e.g., Dockerfile].

Requirements:
- [DESCRIBE SPECIFIC REQUIREMENTS, e.g., "Multi-stage Docker build for FastAPI"]
- [MENTION DEPENDENCIES OR PORTS e.g., "Expose port 8080"]

Do NOT modify existing application code.
Commit: "jules: add [file/component] boilerplate"
```
