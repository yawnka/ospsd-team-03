## CI/CD

- **`.circleci/config.yml`** — full pipeline: build, lint (`ruff`),
  unit tests with coverage (`pytest` + `coverage`), static analysis (`mypy`),
  integration test placeholder, and HTML coverage report artifact


## Documentation Updates

- Reorganized repository structure: moved packages from src/ into components/ directory
- Relocated corresponding test files into their respective component folders
- Updated root README.md to reflect new project structure
    - Added detailed project structure tree in root README.md
    - Added `Features` section to root `README.md` outlining the main project functionalities
- Added README.md for issue_tracker_client_api component
- Added README.md for issue_tracker_client_impl component
