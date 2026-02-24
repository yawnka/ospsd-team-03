# Python Application: A Component-Based Issue Tracker Client

[![CircleCI](https://circleci.com/gh/yawnka/ospsd-team-03.svg?style=shield)](https://circleci.com/gh/yawnka/ospsd-team-03)
<!-- [![Coverage](https://img.shields.io/badge/coverage-85%2B%25-brightgreen)](https://circleci.com/gh/ivanearisty/oss-taapp) -->
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://python.org)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

## Team Members
- `ys4780`  Yanka Sikder `@yawnka`
- `fas6488` Farhen Shefa `@farhen-shefa`
- `zz10803` Zunyu Zhang `@zhangyushao0`
- `yk3183`  Yusuke Katsuki `@katsukii`
- `hr2712`  Hyun Sang (Hayden) Ryu `@hayden-hs`

## TAs:
- `@adithyab-20`
- `@ivanearisty`
- `@AranyaAryaman`

## Architectural Philosophy

This project is built on the principle of "programming integrated over time." The architecture is designed to combat complexity and ensure the system is maintainable and evolvable.

-   **Component-Based Design:** The system is broken down into two distinct, self-contained components. Each component has a single responsibility and can be reused elsewhere.
-   **Interface-Implementation Separation:** Every piece of functionality is defined by an abstract **contract** implemented as an ABC (the "what") and fulfilled by a concrete **implementation** (the "how"). This decouples our business logic from specific technologies (like Trello).
-   **Dependency Injection:** Implementations are "injected" into the abstract contracts at runtime. This means consumers of the API only ever depend on the stable interface, not the volatile implementation details.

## Core Components

The project is a `uv` workspace containing two primary packages:

1.  **`issue_tracker_client_api`**: Defines the abstract `Client` base class (ABC). This is the contract for what actions an issue tracker client can perform (e.g., `list_issues`, `get_issue`, etc.).
4.  **`issue_tracker_client_impl`**: Provides the `DefaultIssueTrackerClient` class, a concrete implementation that uses the Trello API to perform the actions defined in the `Client` abstraction 


## Project Structure

```text
ospsd-team-03
├── .circleci           
│    └── config.yml                        # CI pipeline: runs linting, type-checking, tests, coverage
│  
├── .github
│   ├── ISSUE_TEMPLATE/                    # GitHub issue templates for bug reports & feature requests
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   │
│   ├── PULL_REQUEST.md                    # Pull request template for structured submissions
│
├── components
│   ├── issue_tracker_client_api/          # Interface component (provider-agnostic contract)
│   │   ├── src/
│   │   │   ├── __init__.py
│   │   │   └── client.py                  # Abstract Base Classes + DI factory (get_client)
│   │   ├── pyproject.toml                 # Package metadata and dependencies
│   │   ├── README.md                      # Interface-specific documentation
│   │   └── tests/                         # Unit tests for interface behavior
│   │       └── test_client_api.py
│   │
│   └── issue_tracker_client_impl/         # Trello implementation component
│       ├── src/
│       │   └── __init__.py                # Registers implementation via Dependency Injection
│       │   └── client.py                  # Concrete Trello client implementation
│       ├── pyproject.toml                 # Package metadata and provider dependencies
│       ├── README.md                      # Implementation-specific documentation
│       └── tests/                         # Unit tests (mocking Trello API where applicable)
│           └── test_impl.py                
│
├── tests/
│   ├── integration/                       # Integration tests (verifies DI wiring works correctly)
│   │   └── test_di_wiring.py
│   │
│   └── e2e/                               # End-to-end tests using real Trello credentials
│       └── test_main_application.py
│
├── docs/                                   
│   ├── components     
│   │   ├── issue_tracker_client_api.md
│   │   └── issue_tracker_client_impl.md 
│   └── index.md                        
├── mkdocs.yml                            # MkDocs configuration
├── pyproject.toml                        # Shared tooling config (ruff, mypy, pytest, coverage)
├── README.md                             # Root project documentation
├── uv.lock                               # Locked dependency versions
└── LICENSE
```

## Project Setup

### 1. Prerequisites

-   Python 3.12 or higher
-   `uv` – A fast, all-in-one Python package manager.

### 2. Initial Setup

1.  **Install `uv`:**
    ```bash
    # macOS / Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Windows (PowerShell)
    irm https://astral.sh/uv/install.ps1 | iex
    ```

2.  **Clone the Repository:**
    ```bash
    git clone https://github.com/yawnka/ospsd-team-03.git
    cd ospsd-team-03
    ```

3.  **Set Up Trello Credentials:**
    -   Follow the [Atlassian instructions](https://developer.atlassian.com/cloud/trello/guides/rest-api/api-introduction/) to API Key and Token.
    -   Create an `.env` file in the root of this project and set `TRELLO_API_KEY="your_api_key"`
    `TRELLO_API_TOKEN="your_api_token"` .
    -   **Alternative**: For CI/CD environments, you can use environment variables instead:
        ```bash
        export TRELLO_API_KEY="your_api_key"
        export TRELLO_API_TOKEN="your_api_token"
        ```
    -   **Important:** Credential files contain secrets and are ignored by `.gitignore`.

4.  **Create and Sync the Virtual Environment:**
    This command creates a `.venv` folder and installs all packages (including workspace members and development tools) defined in `uv.lock`.
    ```bash
    uv sync --all-packages --extra dev
    ```

5.  **Activate the Virtual Environment:**
    ```bash
    # macOS / Linux
    source .venv/bin/activate
    # Windows (PowerShell)
    .venv\Scripts\Activate.ps1
    ```

## Development Workflow

All commands should be run from the project root with the virtual environment activated.

### Running the Application


### Running the Toolchain

-   **Linting & Formatting (Ruff):**
    The project uses Ruff with comprehensive rules configured in `pyproject.toml`.
    ```bash
    # Check for issues
    uv run ruff check .
    # Automatically fix issues
    uv run ruff check . --fix
    # Check formatting
    uv run ruff format --check .
    # Apply formatting
    uv run ruff format .
    ```

-   **Static Type Checking (MyPy):**
    <!-- ```bash
    uv run mypy src tests
    ``` -->

-   **Testing (Pytest):**

    <!-- I'd recommend only running: `uv run pytest src/ tests/ -m "not local_credentials" -v` for simplicity.

    The project uses a comprehensive testing strategy with different test categories.
    ```bash
    # Run all tests (includes unit, integration, and e2e tests)
    uv run pytest

    # Run only unit tests (fast, no external dependencies - from src/ directories)
    uv run pytest components/

    # Run all tests except those requiring local credential files
    uv run pytest components/ tests/ -m "not local_credentials"

    # Run only integration tests (requires environment variables or credentials)
    uv run pytest -m integration

    # Run only end-to-end tests (requires credentials)
    uv run pytest -m e2e

    # Run only CircleCI-compatible tests (CI/CD environment)
    uv run pytest -m circleci

    # Run tests with coverage reporting
    uv run pytest --cov=src --cov-report=term-missing
    ``` -->

### Viewing Documentation

This project uses MkDocs for documentation.
```bash
# Start the live-reloading documentation server
uv run mkdocs serve
```
Open your browser to `http://127.0.0.1:8000` to view the site.

## Testing Infrastructure

The project implements a sophisticated testing strategy designed for both local development and CI/CD environments:

### Test Categories

- **Unit Tests** (`src/*/tests/`): Fast, isolated tests with mocked dependencies
- **Integration Tests** (`tests/integration/`): Tests that verify component interactions
- **End-to-End Tests** (`tests/e2e/`): Full application workflow tests
<!-- - **CircleCI Tests**: CI/CD-compatible tests that handle missing credentials gracefully
- **Local Credentials Tests**: Tests that require `credentials.json` or `token.json` files -->

### Test Markers

<!-- The project uses pytest markers to categorize tests:
```bash
@pytest.mark.unit              # Fast unit tests
@pytest.mark.integration       # Integration tests
@pytest.mark.e2e              # End-to-end tests
@pytest.mark.circleci         # CI/CD compatible
@pytest.mark.local_credentials # Requires local auth files
``` -->

### Authentication in Tests

The testing infrastructure handles different authentication scenarios:
- **Local Development**: Uses `.env` file or set `TRELLO_API_KEY` and `TRELLO_API_TOKEN` 
<!-- - **CI/CD Environment**: Uses environment variables (`GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`)
- **Missing Credentials**: Tests fail fast with clear error messages (no hanging) -->

## Continuous Integration

The project includes a comprehensive CircleCI configuration (`.circleci/config.yml`) with:

<!-- - **All Branches**: Unit tests, linting, and CI-compatible tests
- **Main/Develop**: Additional integration tests with real Gmail API calls
- **Artifacts**: Coverage reports, test results, and build summaries

See `docs/circleci-setup.md` for detailed CI/CD setup instructions. -->


## Quick Start
1. **Install dependencies**: `uv sync --all-packages --extra dev`
2. **Run tests**: `uv run pytest tests/ -v` or `uv run pytest components/ tests/ -m "not local_credentials" -v`
3. **Check code quality**: `uv run ruff check . && uv run ruff format --check .`
4. **Fix formatting**: `uv run ruff format .`
5. **View documentation**: `uv run mkdocs serve`

### Best Practices
- Run unit tests (`uv run pytest components/`) during development for fast feedback
- Use integration tests (`uv run pytest -m integration`) to verify component interactions
- Run full test suite (`uv run pytest`) before pushing to ensure CI compatibility
- The CircleCI pipeline provides automated validation on every push


<!-- ## What This Repo Provides

Two installable Python components under ` \components ` using a `uv` workspace:

| Package | Purpose |
|---------|---------|
| `issue_tracker_client_api` | Provider-agnostic abstract interface (ABC) + DI hooks |
| `issue_tracker_client_impl` | Concrete implementation; reads token from `ISSUE_TRACKER_TOKEN` env var |

Consumers should depend only on the interface component. 
The implementation component is imported only to register itself via Dependency Injection. -->



<!-- 
## Quickstart

```sh
uv sync             # install workspace + dev deps
uv run ruff check . # lint  (select = ALL)
uv run mypy .       # type-check (strict = true)
uv run pytest       # test + coverage
```

## API Concepts

All client methods accept a `board` parameter as the primary scope identifier:

- In **Trello**, `board` maps to a Trello board ID.
- Other providers may map it differently (e.g. a project key, workspace slug).

Issue types (`Issue`, `Comment`) remain provider-agnostic in the API layer.

## How DI Works

Importing `issue_tracker_client_impl` auto-registers its factory into the API package:

```python
import issue_tracker_client_impl          # side-effect: registers DefaultIssueTrackerClient
from issue_tracker_client_api.client import get_client

client = get_client()                     # returns a DefaultIssueTrackerClient
client.list_issues("my-trello-board-id")  # board = Trello board identifier
```
## Recent Changes (HW1)

### E2E Tests - Hyun Sang Ryu
- Added end-to-end test suite (`tests/e2e/test_main_application.py`)
- Validates full application workflow with Trello integration
- Registered e2e pytest marker in `pyproject.toml`

## Features

- Provider-agnostic Issue Tracker interface using Abstract Base Classes
- Trello-based concrete implementation
- Dependency Injection via factory registration
- Unit tests for each component
- Integration tests verifying DI wiring
- End-to-end (E2E) tests for full Trello workflow
- Strict static analysis (Ruff + Mypy strict mode)
- Coverage reporting with threshold enforcement
- uv-based workspace dependency management -->

