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




# AFTER FIRST DRAFT
## READMEs
- Cleaned up and clarified project documentation
- Improved README structure and formatting (root + component READMEs)
- Clarified dependency injection and client construction workflow
- Documented Trello authentication expectations
- Standardized testing and coverage command examples
- Minor spec/document consistency fixes

## Testing Improvements
- Aligned pytest markers across the codebase (unit, integration)
- Registered custom markers in pyproject.toml for marker validation
- Added assertion to ensure DI registry is populated before accessing factory
- Removed hardcoded Trello board ID in E2E tests
- E2E tests now rely on TRELLO_BOARD_ID environment variable

## Documentation Enhancements (MkDocs)
- Restructured docs/ to reflect component-based architecture
- Updated index.md with:
    -Project overview
    -Workspace structure
    -Navigation guidance
- Added structured components.md documenting:
    Interface vs implementation separation
    Dependency Injection design
    Workspace layout
- Added testing.md:
  - Marker strategy
  - Unit vs integration vs E2E breakdown
  - CI behavior
- Updated API and implementation documentation pages
- Standardized formatting and improved Markdown consistency
- Ensured documentation builds cleanly without warnings

## MkDocs Configuration Fixes
- Added mkdocstrings[python] to dev dependency group
- Synced uv workspace to install updated dev dependencies
- Fixed mkdocs.yml handler configuration for mkdocstrings
- Cleaned module directives to ensure proper rendering

## Ruff docstring violations and rule conflicts fixes
- Replace @pytest.fixture() with @pytest.fixture
- Fix D205 and D210 docstring formatting issues
- Remove magic number (PLR2004) in test assertion
- Ignore D203 and D213 to prevent D203/D211 and D212/D213 conflicts

