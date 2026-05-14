# OSPSD Team 03 — AI-Integrated Issue Tracker Client

[![CircleCI](https://circleci.com/gh/yawnka/ospsd-team-03.svg?style=shield)](https://circleci.com/gh/yawnka/ospsd-team-03)
[![Coverage](https://img.shields.io/badge/coverage-85%2B%25-brightgreen)](https://circleci.com/gh/yawnka/ospsd-team-03)
[![Python](https://img.shields.io/badge/python-3.13%2B-blue)](https://python.org)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Deployed Service](https://img.shields.io/badge/deployed-Google%20Cloud%20Run-brightgreen)](https://issue-tracker-service-793028870171.us-central1.run.app)
[![Telemetry](https://img.shields.io/badge/telemetry-Grafana-brightgreen)](https://ospsd.grafana.net/public-dashboards/52c2cccce06f4adebe654c2763b12603)

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

## Project Summary

This repository contains Team 03's issue tracker application. The project uses a component-based Python workspace to provide a Trello-backed issue tracker client, a FastAPI service, an AI client integration, and a cross-vertical Chat integration through Discord.

The service can manage issues directly through API endpoints and through AI-assisted workflows. The AI layer supports tool calling, so a model response can trigger typed domain actions such as creating an issue. After an AI tool action succeeds, the service can notify a Discord channel through the shared Chat vertical API.

## Architectural Philosophy

This project is built on the principle of "programming integrated over time." The architecture is designed to combat complexity and ensure the system is maintainable and evolvable.

-   **Component-Based Design:** The system is broken down into distinct, self-contained components. Each component has a single responsibility and can be reused elsewhere.
-   **Interface-Implementation Separation:** Every piece of functionality is defined by an abstract **contract** implemented as an ABC (the "what") and fulfilled by a concrete **implementation** (the "how"). This decouples our business logic from specific technologies (like Trello).
-   **Dependency Injection:** Implementations are "injected" into the abstract contracts at runtime. This means consumers of the API only ever depend on the stable interface, not the volatile implementation details.
-   **Location Transparency:** Whether the implementation runs locally or as a remote service is transparent to the consumer — the same interface is used in both cases via the Adapter Pattern.


## Core Components

The project is a `uv` workspace containing the following packages:

1. **`issue_tracker_client_api`**: Defines the abstract `IssueTrackerClient` base class. This is the provider-agnostic contract for issue tracker operations.
2. **`issue_tracker_client_impl`**: Provides the Trello-backed implementation of the issue tracker contract.
3. **`issue_tracker_client_service`**: Provides the FastAPI service. It exposes issue tracker endpoints, health checks, AI-assisted issue workflows, and telemetry.
4. **`issue_tracker_client_service_client`**: Provides the generated Python HTTP client created from the service's OpenAPI schema.
5. **`issue_tracker_client_adapter`**: Implements the issue tracker interface by delegating to the remote service client.
6. **`ai_client_api`**: Defines the abstract AI client interface used by the service.
7. **`ai_client_impl`**: Provides the OpenAI-backed implementation of the AI client interface.

## Authentication Model

Authentication is implemented using a session-based flow.

After login, the service creates a session and sets an HTTP-only `session_id` cookie. This cookie is automatically included in all subsequent requests and is used by the service to resolve the authenticated user.

The system does not use bearer tokens or `Authorization` headers. Authentication is handled transparently via cookies, and the adapter layer ensures requests include the session information.

## AI and Cross-Vertical Integration

The service includes an AI-assisted chat endpoint that can translate natural-language requests into typed tool calls. For example, a user can ask the system to create an issue, and the AI layer can return a `create_issue` tool call. The service validates the tool arguments, executes the issue tracker action, and returns a structured response.

The project also integrates with the shared Chat vertical through the published `chat-client-api` package and Team 8's Discord implementation. The Chat provider is loaded through dependency injection using the `CHAT_CLIENT_IMPL_MODULE` environment variable.

Typical Discord configuration:

```bash
export CHAT_CLIENT_IMPL_MODULE="discord_client_impl"
export DISCORD_BOT_TOKEN="your_discord_bot_token"
export DISCORD_GUILD_ID="your_discord_server_id"
export DISCORD_NOTIFY_CHANNEL_ID="your_sandbox_channel_id"
```

When an AI tool call successfully performs an issue tracker action, the service can send a notification to the configured Discord channel. This verifies that the issue tracker service can call into another vertical through a shared API instead of directly depending on provider-specific code.

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
│   └── PULL_REQUEST.md                    # Pull request template for structured submissions
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
│   ├── issue_tracker_client_adapter/      # Service client adapter
│   │   ├── src/
│   │   │   └── issue_tracker_client_adapter/
│   │   │       ├── __init__.py            # Auto-registers via DI on import
│   │   │       └── adapter.py             # ServiceClientAdapter implementation
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── tests/
│   │       └── test_adapter.py
│   │
│   ├── ai_client_api/                     # AI interface component
│   │   ├── src/
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── tests/
│   │       └── test_ai_client_api.py
│   │
│   └── ai_client_impl/                    # OpenAI implementation component
│       ├── src/
│       ├── pyproject.toml
│       ├── README.md
│       └── tests/
│           └── test_ai_client_impl.py
│   
├── tests/
│   ├── integration/                       # Integration tests
│   │   ├── test_client_integration.py
│   │   ├── test_discord_integration.py
│   │   └── test_real_discord_cross_vertical.py
│   │
│   └── e2e/                               # End-to-end tests using real Trello credentials
│       ├── test_ai_discord_flow.py
│       └── test_main_application.py
│
├── docs/
│   ├── components/
│   │   ├── ai_client_api.md
│   │   ├── ai_client_impl.md
│   │   ├── issue_tracker_client_api.md
│   │   ├── issue_tracker_client_impl.md
│   │   ├── issue_tracker_client_service.md
│   │   ├── issue_tracker_client_service_client.md
│   │   └── issue_tracker_client_adapter.md
│   ├── circleci-setup.md
│   ├── component.md
│   ├── design.md
│   ├── infrastructure.md
│   ├── observability.md
│   ├── testing.md
│   └── index.md
|
├── infrastructure/
│   ├── grafana/
│   └── terraform/
├── Dockerfile                              # Multi-stage Docker build for deployment
├── DESIGN.md
├── mkdocs.yml                              # MkDocs configuration
├── pyproject.toml                          # Shared tooling config (ruff, mypy, pytest, coverage)
├── README.md                               # Root project documentation
├── uv.lock                                 # Locked dependency versions
└── LICENSE
```

## Project Setup

### 1. Prerequisites

-   Python 3.13 or higher
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
        `OPENAI_API_KEY="your_openai_api_key"`
        `CHAT_CLIENT_IMPL_MODULE="discord_client_impl"`
        `DISCORD_BOT_TOKEN="your_discord_bot_token"`
        `DISCORD_GUILD_ID="your_discord_server_id"`
        `DISCORD_NOTIFY_CHANNEL_ID="your_sandbox_channel_id"`

    - Load the `.env` file:
        ``` bash
        set -a && source .env && set +a
        ```
    -   **Alternative**: Export manually:
        ```bash
        export TRELLO_API_KEY="your_api_key"
        export TRELLO_API_TOKEN="your_api_token"
        export TRELLO_BOARD_ID="your_board_id"
        export OPENAI_API_KEY="your_openai_api_key"
        export CHAT_CLIENT_IMPL_MODULE="discord_client_impl"
        export DISCORD_BOT_TOKEN="your_discord_bot_token"
        export DISCORD_GUILD_ID="your_discord_server_id"
        export DISCORD_NOTIFY_CHANNEL_ID="your_sandbox_channel_id"
        ```
    - **CI/CD**: Configure Trello, OpenAI, Discord, and deployment credentials in CircleCI project settings or contexts.
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
    uv run mypy \
    -p ai_client_api \
    -p ai_client_impl \
    -p issue_tracker_client_api \
    -p issue_tracker_client_impl \
    -p issue_tracker_client_service \
    -p issue_tracker_client_adapter \
    --explicit-package-bases
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

The FastAPI service is deployed to **Google Cloud Run** using Docker.

### Platform Details

- **Provider:** [Google Cloud Run](https://cloud.google.com/run)
- **Live URL:** <https://issue-tracker-service-793028870171.us-central1.run.app/>
- **Runtime:** Docker (multi-stage build)
- **Branch:** `hw-3` / final submission branch
- **Health Check:** `GET /health` returns HTTP 200
- **API Docs:** <https://issue-tracker-service-793028870171.us-central1.run.app/docs>
- **Telemetry Dashboard:** <https://ospsd.grafana.net/public-dashboards/52c2cccce06f4adebe654c2763b12603>
- **Video Demo:** TODO: add video demo link

### Environment Variables (Google Cloud Run Dashboard)

| Variable | Description |
|----------|-------------|
| `TRELLO_API_KEY` | Trello API key |
| `TRELLO_API_TOKEN` | Trello API token |
| `TRELLO_BOARD_ID` | Trello board used by service demos and tests |
| `OPENAI_API_KEY` | OpenAI API key used by the AI client implementation |
| `CHAT_CLIENT_IMPL_MODULE` | Chat provider module, usually `discord_client_impl` |
| `DISCORD_BOT_TOKEN` | Discord bot token |
| `DISCORD_GUILD_ID` | Discord server ID |
| `DISCORD_NOTIFY_CHANNEL_ID` | Discord channel used for issue notifications |
| `REDIRECT_URI` | Trello authorization callback URL for deployed service |

All secrets are stored via Google Cloud Run's native secrets manager. No secrets are committed to source control.

### CI/CD Pipeline

CircleCI is configured to run on every push:

1. **build** - Install dependencies with `uv sync`
2. **lint** - Run `ruff check`
3. **format_check** - Run `ruff format --check`
4. **type_check** - Run `mypy` in strict mode
5. **unit_test** - Run pytest with coverage
6. **integration_test** - Run CI-safe integration tests
7. **e2e_test** - Run end-to-end tests where credentials are available
8. **coverage_report** - Generate coverage report
9. **deploy** - Trigger Google Cloud Run deployment and verify the public health check

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

### Real Discord Cross-Vertical Test

Most CI-safe integration tests use deterministic fakes so the test suite remains fast and does not require live third-party credentials. The project also includes a credential-gated integration test that uses the real shared Chat API and Team 8's Discord implementation:

```text
tests/integration/test_real_discord_cross_vertical.py
```
This test uses real Discord for the Chat vertical boundary while keeping OpenAI and Trello deterministic. It verifies that the service can process an AI tool call, execute an issue tracker action, send a Discord notification, and read the notification back through the shared Chat API.

Run it manually with:
```bash
DISCORD_INTEGRATION_TESTS=1 \
DISCORD_BOT_TOKEN="your_discord_bot_token" \
DISCORD_GUILD_ID="your_discord_server_id" \
DISCORD_NOTIFY_CHANNEL_ID="your_sandbox_channel_id" \
uv run pytest tests/integration/test_real_discord_cross_vertical.py \
-m local_credentials -rs
```

`DISCORD_INTEGRATION_TESTS=1` is a safety switch so real Discord messages are not sent during normal local or CI test runs.

### Test Markers

The project uses pytest markers to categorize tests:
```python
@pytest.mark.unit              # Fast unit tests
@pytest.mark.integration       # Integration tests
@pytest.mark.e2e               # End-to-end tests
@pytest.mark.local_credentials # Tests requiring real local credentials
```

### Authentication in Tests

The testing infrastructure handles different authentication scenarios:
- **Local Development**:  Requires `TRELLO_API_KEY`, `TRELLO_API_TOKEN` and `TRELLO_BOARD_ID` set via environment variables or in a `.env` file
- **CI/CD Environment**: Set environment variables (`TRELLO_API_KEY`, `TRELLO_API_TOKEN`) in CircleCI project settings
- **Missing Credentials**: Tests fail fast with clear error messages (no hanging)
- If `TRELLO_BOARD_ID` is not set, some E2E tests will be skipped.

## Observability

The service records telemetry for public API calls and user-facing workflows. The telemetry focuses on:

- request latency,
- successful requests,
- failed requests,
- route labels,
- method labels,
- status labels.

The deployed service is intended to be monitored through a dashboard that shows latency and success/failure rates.

Telemetry dashboard: <https://ospsd.grafana.net/public-dashboards/52c2cccce06f4adebe654c2763b12603>

## Continuous Integration

The project includes a comprehensive CircleCI configuration (`.circleci/config.yml`) with:

- Runs Ruff (linting)
- Runs MyPy (strict mode)
- Runs all tests (unit, integration, E2E)
- Stores test results in CircleCI dashboard
- Uploads coverage reports
- Deploys to Google Cloud Run from the configured submission branch

See `docs/circleci-setup.md` for detailed CI/CD setup instructions.


## Quick Start

1. **Install dependencies:** `uv sync --all-packages --group dev`
2. **Load environment variables:** `set -a && source .env && set +a`
3. **Run linting:** `uv run ruff check .`
4. **Run formatting check:** `uv run ruff format --check .`
5. **Run type checks:** `uv run mypy -p ai_client_api -p ai_client_impl -p issue_tracker_client_api -p issue_tracker_client_impl -p issue_tracker_client_service -p issue_tracker_client_adapter --explicit-package-bases`
6. **Run CI-safe tests:** `uv run pytest components/ tests/ -m "not local_credentials"`
7. **Run the service:** `uv run uvicorn issue_tracker_client_service.app:app --reload`
8. **View documentation:** `uv run mkdocs serve`
