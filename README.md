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

-   **Component-Based Design:** The system is broken down into two distinct, self-contained components. Each component has a single responsibility and can be reused elsewhere.
-   **Interface-Implementation Separation:** Every piece of functionality is defined by an abstract **contract** implemented as an ABC (the "what") and fulfilled by a concrete **implementation** (the "how"). This decouples our business logic from specific technologies (like Trello).
-   **Dependency Injection:** Implementations are "injected" into the abstract contracts at runtime. This means consumers of the API only ever depend on the stable interface, not the volatile implementation details.

## Core Components

The project is a `uv` workspace containing two primary packages:

1.  **`issue_tracker_client_api`**: Defines the abstract `IssueTrackerClient` base class (ABC). This is the contract for what actions an issue tracker client can perform (e.g., `list_issues`, `get_issue`, etc.).
2.  **`issue_tracker_client_impl`**: Provides the `DefaultIssueTrackerClient` class, a concrete implementation that uses the Trello API to perform the actions defined in the `Client` abstraction 


## Project Structure

```text
ospsd-team-03
├── .circleci/
│   └── config.yml                        # CI pipeline: lint, type-check, test, deploy
│
├── .github/
│   ├── ISSUE_TEMPLATE/                   # GitHub issue templates
│   └── PULL_REQUEST.md                   # Pull request template
│
├── components/
│   ├── issue_tracker_client_api/         # Interface (provider-agnostic ABC contract)
│   ├── issue_tracker_client_impl/        # Trello implementation
│   ├── issue_tracker_client_service/     # FastAPI service (deployed on Cloud Run)
│   ├── issue_tracker_client_service_client/  # Auto-generated HTTP client
│   └── issue_tracker_client_adapter/     # Adapter (ABC → generated client)
│
├── infrastructure/
│   ├── terraform/                        # IaC: Cloud Run, Artifact Registry, Secret Manager
│   │   ├── main.tf                       # Provider + GCS backend
│   │   ├── cloudrun.tf                   # Cloud Run service, secrets, IAM
│   │   ├── variables.tf                  # Input variables
│   │   └── outputs.tf                    # Service URL output
│   └── grafana/
│       └── dashboard.json                # Grafana dashboard (Latency, Success, Failure)
│
├── tests/
│   ├── integration/                      # DI wiring tests
│   └── e2e/                              # End-to-end tests
│
├── docs/                                 # MkDocs documentation source
├── Dockerfile                            # Multi-stage Docker build
├── mkdocs.yml                            # MkDocs configuration
├── pyproject.toml                        # Shared tooling config (ruff, mypy, pytest, coverage)
├── DESIGN.md                             # Architecture and design decisions
├── uv.lock                               # Locked dependency versions
└── README.md
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
    uv run mypy .
    ```

-   **Testing (Pytest):**

    The project uses a comprehensive testing strategy.

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

    # Run tests with coverage reporting
    uv run pytest --cov=components --cov-report=term-missing
    ```

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
- - If `TRELLO_BOARD_ID` is not set, some E2E tests will be skipped.

## Deployment

The service is deployed on **GCP Cloud Run** with infrastructure managed by **Terraform**.

### Cloud Run

- Docker image is built and pushed to GCP Artifact Registry
- Cloud Run serves the FastAPI application with auto-scaling (0–1 instances)
- Sensitive credentials (Trello keys, OTLP headers) are stored in GCP Secret Manager

### Infrastructure as Code

All cloud resources are defined in `infrastructure/terraform/`:

- Artifact Registry repository
- Secret Manager secrets + IAM bindings
- Cloud Run service with environment variables
- Public access (allUsers invoker)

Terraform state is stored in a GCS bucket (`ospsd-team-03-tfstate`).

### Observability

The service emits telemetry data via OpenTelemetry to Grafana Cloud:

- **Request Latency** — p50, p95, p99 percentiles
- **Success Rate** — percentage of 2xx responses
- **Failure Rate** — percentage of 4xx/5xx responses

Telemetry is opt-in: when `OTEL_EXPORTER_OTLP_ENDPOINT` is unset, the service runs without any observability overhead. The Grafana dashboard definition is committed at `infrastructure/grafana/dashboard.json`.

## Continuous Integration

The project includes a comprehensive CircleCI configuration (`.circleci/config.yml`):

**`build_and_test`** (all branches):
- Ruff (linting), MyPy (strict mode), unit tests, integration tests, coverage reports

**`deploy_to_cloud_run`** (`hw-3` branch):
- Build + push Docker image → Terraform plan → Terraform apply → Health check verification

See `docs/circleci-setup.md` for detailed CI/CD setup instructions.


## Quick Start
1. **Install dependencies**: `uv sync --all-packages --group dev`
2. **Run tests**: `uv run pytest tests/ -v` or `uv run pytest components/ tests/ -m "not local_credentials" -v`
3. **Check code quality**: `uv run ruff check . && uv run ruff format --check .`
4. **Fix formatting**: `uv run ruff format .`
5. **View documentation**: `uv run mkdocs serve`

### Best Practices
- Run unit tests (`uv run pytest components/`) during development for fast feedback
- Use integration tests (`uv run pytest -m integration`) to verify component interactions
- Run full test suite (`uv run pytest`) before pushing to ensure CI compatibility
- The CircleCI pipeline provides automated validation on every push
