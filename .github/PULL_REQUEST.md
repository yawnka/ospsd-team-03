## Summary

This PR completes the HW1 first-draft. We will be working on an issue tracker client based on Trello using uv.

Additions/Changes Made:
- Abstract API package  
- Default implementation package  
- Dependency injection wiring  
- Repository restructure under `components/`  
- CircleCI CI/CD configuration  
- Integration and E2E tests  
- MkDocs documentation  

All checks pass locally and in CircleCI.

---

## Architecture

The project is structured as two installable workspace packages:

- `issue_tracker_client_api`
  - Defines the abstract interface  
  - Provides data models  
  - Implements dependency injection registry  

- `issue_tracker_client_impl`
  - Implements the interface (stubbed for draft)  
  - Auto-registers itself on import  

Both packages use the layout:

```
components/<package>/src/<package>/
```

---

## Dependency Injection

- The API package defines:
  - `register(factory)`
  - `get_client()`

- The implementation registers `DefaultIssueTrackerClient` in `__init__.py`.

- Importing `issue_tracker_client_impl` activates the implementation.

Callers only depend on the API package:

```python
import issue_tracker_client_api.client as api
import issue_tracker_client_impl

client = api.get_client()
```

---

## Testing

- Unit tests validate DI behavior.  
- Integration test verifies implementation auto-registration.  
- E2E tests validate:
  - Required repository structure (`components/`)
  - Python syntax validity of source files
  - Import behavior in a subprocess
  - Token-required behavior for client instantiation

Coverage is approximately 85% and enforced in CI.

---

## CI/CD

`.circleci/config.yml` includes:

- Build step using `uv sync`
- Linting with `ruff`
- Static analysis with `mypy --strict`
- Test execution with coverage threshold
- Coverage report artifact generation

All pipeline jobs pass.

---

## Documentation

Added MkDocs setup:

- `docs/` directory
- `mkdocs.yml`
- Component documentation pages:
  - `docs/components/issue_tracker_client_api.md`
  - `docs/components/issue_tracker_client_impl.md`
- Updated root `README.md` with:
  - Project structure
  - Features section
  - Setup instructions

Documentation builds successfully using:

```bash
uv run mkdocs build
```

---

## Local Verification

```bash
uv sync --all-packages --group dev
uv run ruff check .
uv run mypy -p issue_tracker_client_api -p issue_tracker_client_impl --explicit-package-bases
uv run pytest
uv run mkdocs build
```

All commands complete successfully.
