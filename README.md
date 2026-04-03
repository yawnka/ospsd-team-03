# Python Application: A Component-Based Issue Tracker Client

[![CircleCI](https://circleci.com/gh/yawnka/ospsd-team-03.svg?style=shield)](https://circleci.com/gh/yawnka/ospsd-team-03)
[![Coverage](https://img.shields.io/badge/coverage-85%2B%25-brightgreen)](https://circleci.com/gh/yawnka/ospsd-team-03)
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

-   **Component-Based Design:** The system is broken down into five distinct, self-contained components. Each component has a single responsibility and can be reused elsewhere.
-   **Interface-Implementation Separation:** Every piece of functionality is defined by an abstract **contract** implemented as an ABC (the "what") and fulfilled by a concrete **implementation** (the "how"). This decouples our business logic from specific technologies (like Trello).
-   **Dependency Injection:** Implementations are "injected" into the abstract contracts at runtime. This means consumers of the API only ever depend on the stable interface, not the volatile implementation details.
-   **Location Transparency:** Whether the implementation runs locally or as a remote service is transparent to the consumer — the same interface is used in both cases via the Adapter Pattern.

## Core Components

The project is a `uv` workspace containing five packages:

1.  **`issue_tracker_client_api`**: Defines the abstract `IssueTrackerClient` base class (ABC). This is the contract for what actions an issue tracker client can perform (e.g., `list_issues`, `get_issue`, etc.).
2.  **`issue_tracker_client_impl`**: Provides the `DefaultIssueTrackerClient` class, a concrete implementation that uses the Trello API. Trello does not support the standard OAuth 2.0 authorization code grant — it returns tokens via the URL fragment, making server-side code exchange impossible. With the professor's approval, we use Trello's redirect-based token flow (OAuth 1.0 style) instead.
3.  **`issue_tracker_client_service`**: A FastAPI service that exposes the implementation over HTTP endpoints, including Trello authorization login/callback flow and session-based multi-user support.
4.  **`issue_tracker_client_service_client`**: An auto-generated type-safe HTTP client created from the service's OpenAPI spec using `openapi-python-client`.
5.  **`issue_tracker_client_adapter`**: An adapter implementing `IssueTrackerClient` that delegates to the remote service via the auto-generated client, achieving location transparency.

## Project Structure

```text
ospsd-team-03
├── .circleci
│    └── config.yml                        # CI pipeline: lint, type-check, test, coverage, deploy
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
│   │   │   └── issue_tracker_client_api/
│   │   │       └── client.py              # ABC + DI factory (register / get_client)
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── tests/
│   │       └── test_client_api.py
│   │
│   ├── issue_tracker_client_impl/         # Trello implementation component
│   │   ├── src/
│   │   │   └── issue_tracker_client_impl/
│   │   │       ├── client.py              # Concrete Trello client implementation
│   │   │       └── oauth.py               # Trello authorization helpers
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── tests/
│   │       ├── test_impl.py
│   │       └── test_oauth.py
│   │
│   ├── issue_tracker_client_service/      # FastAPI service (deployment unit)
│   │   ├── src/
│   │   │   ├── issue_tracker_client_service/
│   │   │   │   ├── app.py                 # FastAPI app with all endpoints
│   │   │   │   ├── auth.py                # CSRF state management
│   │   │   │   ├── schemas.py             # Pydantic request/response models
│   │   │   │   └── session.py             # In-memory session store
│   │   │   └── main.py                    # Local dev runner
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── tests/
│   │       └── test_service.py
│   │
│   ├── issue_tracker_client_service_client/  # Auto-generated HTTP client
│   │   ├── src/
│   │   │   └── issue_tracker_client_service_client/
│   │   │       ├── api/                   # Generated endpoint modules
│   │   │       ├── models/                # Generated Pydantic models
│   │   │       └── client.py              # Client / AuthenticatedClient
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   └── issue_tracker_client_adapter/      # Service client adapter
│       ├── src/
│       │   └── issue_tracker_client_adapter/
│       │       ├── __init__.py            # Auto-registers via DI on import
│       │       └── adapter.py             # ServiceClientAdapter implementation
│       ├── pyproject.toml
│       ├── README.md
│       └── tests/
│           └── test_adapter.py
│
├── tests/
│   ├── integration/                       # Integration tests (DI wiring, client contract)
│   │   └── test_client_integration.py
│   │
│   └── e2e/                               # End-to-end tests using real Trello credentials
│       └── test_main_application.py
│
├── docs/
│   ├── components/
│   │   ├── issue_tracker_client_api.md
│   │   ├── issue_tracker_client_impl.md
│   │   ├── issue_tracker_client_service.md
│   │   ├── issue_tracker_client_service_client.md
│   │   └── issue_tracker_client_adapter.md
│   ├── circleci-setup.md
│   ├── component.md
│   ├── testing.md
│   └── index.md
├── Dockerfile                              # Multi-stage Docker build for deployment
├── render.yaml                             # Render deployment configuration
├── mkdocs.yml                              # MkDocs configuration
├── pyproject.toml                          # Shared tooling config (ruff, mypy, pytest, coverage)
├── README.md                               # Root project documentation
├── uv.lock                                 # Locked dependency versions
└── LICENSE
```

## Project Setup

### 1. Prerequisites

-   Python 3.12 or higher
-   `uv` - A fast, all-in-one Python package manager.

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
    -  Follow the [Atlassian instructions](https://developer.atlassian.com/cloud/trello/guides/rest-api/api-introduction/) to API Key and Token.
    - Create an `.env` file in the root of this project:
        `TRELLO_API_KEY="your_api_key"`
        `TRELLO_API_TOKEN="your_api_token"`
        `TRELLO_BOARD_ID="your_board_id"`

    - Load the `.env` file:
        ``` bash
        set -a && source .env && set +a
        ```
    -   **Alternative**: Export manually:
        ```bash
        export TRELLO_API_KEY="your_api_key"
        export TRELLO_API_TOKEN="your_api_token"
        export TRELLO_BOARD_ID="your_board_id"
        ```
    - **CI/CD**: Configure TRELLO_API_KEY and TRELLO_API_TOKEN in CircleCI project settings.
    - **Important:**
        - `TRELLO_BOARD_ID` is required for End-to-End (E2E) tests. This should be the ID of a Trello board that your API key/token has access to.
        - Credential and `.env` files may contain secrets and are ignored by `.gitignore`.


4.  **Create and Sync the Virtual Environment:**
    This command creates a `.venv` folder and installs all packages (including workspace members and development tools) defined in `uv.lock`.
    ```bash
    uv sync --all-packages --group dev
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
    ```bash
    uv run mypy -p issue_tracker_client_api -p issue_tracker_client_impl -p issue_tracker_client_service -p issue_tracker_client_adapter --explicit-package-bases
    ```

-   **Testing (Pytest):**

    The project uses a comprehensive testing strategy.

    ```bash
    # Run all tests (includes unit, integration, and e2e tests)
    uv run pytest

    # Run only unit tests (fast, no external dependencies)
    uv run pytest components/

    # Run all tests except those requiring local credential files
    uv run pytest components/ tests/ -m "not local_credentials"

    # Run only integration tests (requires environment variables or credentials)
    uv run pytest -m integration

    # Run only end-to-end tests (requires credentials)
    uv run pytest -m e2e

    # Run tests with coverage reporting
    uv run pytest --cov=components --cov-report=term-missing
    ```

### Running the Service Locally

```bash
uv run uvicorn issue_tracker_client_service.app:app --reload
```

Visit `http://localhost:8000/docs` for the Swagger UI.

### Viewing Documentation

This project uses MkDocs for documentation.
```bash
# Start the live-reloading documentation server
uv run mkdocs serve
```
Open your browser to `http://127.0.0.1:8000` to view the site.

## Deployment

The FastAPI service is deployed to **Render** using Docker.

### Platform Details

- **Provider:** [Render](https://render.com)
- **Live URL:** <https://ospsd-team-03.onrender.com>
- **Runtime:** Docker (multi-stage build)
- **Branch:** `hw-2` (auto-deploys on push)
- **Health Check:** `GET /health` returns HTTP 200

### Environment Variables (Render Dashboard)

| Variable | Description |
|----------|-------------|
| `TRELLO_API_KEY` | Trello API key |
| `TRELLO_API_TOKEN` | Trello API token |
| `REDIRECT_URI` | Trello authorization callback URL for deployed service |

All secrets are stored via Render's native secrets manager. No secrets are committed to source control.

### CI/CD Pipeline

CircleCI is configured to run on every push:

1. **build** - Install dependencies with `uv sync`
2. **lint** - Run `ruff check`
3. **type_check** - Run `mypy` in strict mode
4. **unit_test** - Run pytest with coverage (threshold: 85%)
5. **integration_test** - Run integration tests with real Trello credentials
6. **coverage_report** - Generate HTML coverage report
7. **deploy** - Trigger Render deployment and verify health check (hw-2 branch only)

### Dockerfile

The project uses a multi-stage Docker build:
- **Stage 1 (builder):** Installs dependencies with `uv sync --all-packages --no-dev`
- **Stage 2 (runtime):** Copies the built environment and runs `uvicorn`

## Testing Infrastructure

The project implements a comprehensive testing strategy designed for both local development and CI/CD environments:

### Test Categories

- **Unit Tests** (`components/*/tests/`): Fast, isolated tests with mocked dependencies
- **Integration Tests** (`tests/integration/`): Tests that verify component interactions
- **End-to-End Tests** (`tests/e2e/`): Full application workflow tests

### Test Markers

The project uses pytest markers to categorize tests:
```bash
@pytest.mark.unit              # Fast unit tests
@pytest.mark.integration       # Integration tests
@pytest.mark.e2e               # End-to-end tests
```

### Authentication in Tests

The testing infrastructure handles different authentication scenarios:
- **Local Development**:  Requires `TRELLO_API_KEY`, `TRELLO_API_TOKEN` and `TRELLO_BOARD_ID` set via environment variables or in a `.env` file
- **CI/CD Environment**: Set environment variables (`TRELLO_API_KEY`, `TRELLO_API_TOKEN`) in CircleCI project settings
- **Missing Credentials**: Tests fail fast with clear error messages (no hanging)
- If `TRELLO_BOARD_ID` is not set, some E2E tests will be skipped.

## Continuous Integration

The project includes a comprehensive CircleCI configuration (`.circleci/config.yml`) with:

- Runs Ruff (linting)
- Runs MyPy (strict mode)
- Runs all tests (unit, integration, E2E)
- Stores test results in CircleCI dashboard
- Uploads coverage reports
- Deploys to Render on the hw-2 branch

See `docs/circleci-setup.md` for detailed CI/CD setup instructions.


## Quick Start
1. **Install dependencies**: `uv sync --all-packages --group dev`
2. **Run tests**: `uv run pytest -v`
3. **Check code quality**: `uv run ruff check . && uv run ruff format --check .`
4. **Run the service**: `uv run uvicorn issue_tracker_client_service.app:app --reload`
5. **View documentation**: `uv run mkdocs serve`
