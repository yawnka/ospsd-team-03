# OSPSD Team 03 Issue Tracker

This repository provides a component-based Python workspace for an AI-integrated issue tracker application. The issue tracker abstraction is provider-agnostic, the default implementation is backed by **Trello**, and the deployed FastAPI service exposes both standard issue operations and AI-assisted workflows.

Conceptually, Trello **cards** are treated as **issues**. The AI layer can translate natural-language requests into typed tool calls, execute issue tracker actions, and notify a Discord channel through the shared Chat API.

## Overview

This project implements a provider-agnostic issue tracker system using:

- a clean abstract issue tracker API package,
- a concrete Trello implementation,
- a FastAPI service for HTTP access,
- a generated Python service client,
- an adapter that preserves the local interface while delegating to the service,
- an abstract AI client API,
- an OpenAI-backed AI client implementation,
- cross-vertical Chat integration through Discord,
- strict typing, linting, CI, tests, deployment, and documentation.

The system separates contracts from implementations so providers can be swapped without changing consumer code. Business logic depends on stable interfaces, while provider-specific packages handle Trello, OpenAI, and Discord details behind those interfaces.


## Project Structure

```text
ospsd-team-03
├── .circleci
│    └── config.yml                      
│
├── .github
│   ├── ISSUE_TEMPLATE/                    
│   └── PULL_REQUEST.md                   
│
├── components
│   ├── issue_tracker_client_api/         
│   │   ├── src/
│   │   │   └── issue_tracker_client_api/
│   │   │       └── client.py             
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── tests/
│   │       └── test_client_api.py
│   │
│   ├── issue_tracker_client_impl/         
│   │   ├── src/
│   │   │   └── issue_tracker_client_impl/
│   │   │       ├── client.py              
│   │   │       └── oauth.py               
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── tests/
│   │       ├── test_impl.py
│   │       └── test_oauth.py
│   │
│   ├── issue_tracker_client_service/     
│   │   ├── src/
│   │   │   ├── issue_tracker_client_service/
│   │   │   │   ├── app.py                 
│   │   │   │   ├── auth.py                
│   │   │   │   ├── schemas.py             
│   │   │   │   └── session.py             
│   │   │   └── main.py                    
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── tests/
│   │       └── test_service.py
│   │
│   ├── issue_tracker_client_service_client/  
│   │   ├── src/
│   │   │   └── issue_tracker_client_service_client/
│   │   │       ├── api/                   
│   │   │       ├── models/               
│   │   │       └── client.py             
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   ├── issue_tracker_client_adapter/     
│   │   ├── src/
│   │   │   └── issue_tracker_client_adapter/
│   │   │       ├── __init__.py           
│   │   │       └── adapter.py             
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── tests/
│   │       └── test_adapter.py
│   │
│   ├── ai_client_api/                     
│   │   ├── src/
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── tests/
│   │       └── test_ai_client_api.py
│   │
│   └── ai_client_impl/                    
│       ├── src/
│       ├── pyproject.toml
│       ├── README.md
│       └── tests/
│           └── test_ai_client_impl.py
│   
├── tests/
│   ├── integration/                       
│   │   ├── test_client_integration.py
│   │   ├── test_discord_integration.py
│   │   └── test_real_discord_cross_vertical.py
│   │
│   └── e2e/                               
│       ├── test_ai_discord_flow.py
│       └── test_main_application.py                   
│
├── docs/
│   ├── components/
│   ├── circleci-setup.md
│   ├── component.md
│   ├── design.md
│   ├── infrastructure.md
│   ├── observability.md
│   ├── testing.md
│   └── index.md
│
├── infrastructure/
│   ├── grafana/
│   └── terraform/
├── Dockerfile                              
├── DESIGN.md
├── mkdocs.yml                              
├── pyproject.toml                         
├── README.md                              
├── uv.lock                                
└── LICENSE
```

## Core Components

1. **`issue_tracker_client_api`** — Provider-agnostic issue tracker contract, domain models, and dependency injection registry.
2. **`issue_tracker_client_impl`** — Trello-backed implementation that maps Trello boards, lists, and cards into issue tracker concepts.
3. **`issue_tracker_client_service`** — FastAPI service exposing issue tracker operations, health checks, telemetry, AI-assisted workflows, and cross-vertical notifications.
4. **`issue_tracker_client_service_client`** — Generated type-safe Python client created from the service's OpenAPI schema.
5. **`issue_tracker_client_adapter`** — Adapter that implements the issue tracker contract while delegating to the generated service client.
6. **`ai_client_api`** — Provider-agnostic AI client contract for chat completions and tool-calling workflows.
7. **`ai_client_impl`** — OpenAI-backed implementation of the AI client contract.

## Dependency Injection Flow

The project uses dependency injection so consumers depend on interfaces instead of concrete providers.

Issue tracker example:

```python
import issue_tracker_client_impl
from issue_tracker_client_api import get_client

client = get_client()
issues = client.list_issues("your_board_id")
print(len(issues))
```

AI client example:

```python
import ai_client_impl
from ai_client_api import get_client

client = get_client()
response = client.send_message("Summarize the open issues")
print(response)
```
Cross-vertical Chat configuration is loaded from environment variables:
```bash
export CHAT_CLIENT_IMPL_MODULE="discord_client_impl"
export DISCORD_BOT_TOKEN="your_discord_bot_token"
export DISCORD_GUILD_ID="your_discord_server_id"
export DISCORD_NOTIFY_CHANNEL_ID="your_sandbox_channel_id"
```
The implementation package registers itself at import time, and `get_client()` returns the registered provider. This keeps the system loosely coupled and extensible.

## AI and Cross-Vertical Flow

The service exposes an AI-assisted endpoint that can turn natural-language requests into typed tool calls. A typical flow is:

1. A user sends a request to the AI chat endpoint.
2. The AI client returns a tool call such as `create_issue`.
3. The service validates the tool arguments.
4. The issue tracker action is executed through the Trello-backed implementation.
5. The service sends a notification through the shared Chat API using the configured Discord provider.
6. The API returns a structured response containing the model reply and executed actions.

This keeps the AI provider, issue tracker provider, and Chat provider behind explicit interfaces.

## Quickstart

### 1. Create a virtual environment and install dependencies

```bash
uv venv
source .venv/bin/activate
uv sync --all-packages --group dev
```

### 2. Set credentials
Set the following environment variables locally or in CI:
```bash
export TRELLO_API_KEY="your_trello_api_key"
export TRELLO_API_TOKEN="your_trello_api_token"
export TRELLO_BOARD_ID="your_trello_board_id"

export OPENAI_API_KEY="your_openai_api_key"

export CHAT_CLIENT_IMPL_MODULE="discord_client_impl"
export DISCORD_BOT_TOKEN="your_discord_bot_token"
export DISCORD_GUILD_ID="your_discord_server_id"
export DISCORD_NOTIFY_CHANNEL_ID="your_sandbox_channel_id"
```

### 3. Run tests
```bash
# all CI-safe tests
uv run pytest components/ tests/ -m "not local_credentials"

# unit tests only
uv run pytest components/

# integration tests
uv run pytest tests/integration/ -m integration
```

### 4. Run the service locally

```bash
uv run uvicorn issue_tracker_client_service.app:app --reload
```

Open the local API docs at [http://localhost:8000/docs](http://localhost:8000/docs).

## Deployment and Observability

The FastAPI service is deployed on Google Cloud Run.

- **Service URL:** <https://issue-tracker-service-793028870171.us-central1.run.app>
- **Health Check:** <https://issue-tracker-service-793028870171.us-central1.run.app/health>
- **API Docs:** <https://issue-tracker-service-793028870171.us-central1.run.app/docs>
- **Telemetry Dashboard:** <https://ospsd.grafana.net/public-dashboards/52c2cccce06f4adebe654c2763b12603>

The service records telemetry for request latency, successful requests, and failed requests. The Grafana dashboard visualizes deployed-service metrics rather than only local output.

## Documentation

Project documentation is organized as follows:

- [Component Guide](component.md)  
  Explains component structure, package responsibilities, and dependency rules.

- [Design & Decisions](design.md)  
  Documents architecture, AI integration, cross-vertical integration, and observability choices.

- [Testing Strategy](testing.md)  
  Describes unit, integration, end-to-end, and real-provider test boundaries.

- [Infrastructure](infrastructure.md)  
  Documents deployment, infrastructure, and cloud configuration.

- [Observability](observability.md)  
  Documents telemetry, metrics, and dashboard expectations.

- [CircleCI Setup](circleci-setup.md)  
  Documents the CI/CD pipeline configuration and automation workflow.

- [Issue Tracker API](components/issue_tracker_client_api.md)  
  Documents the provider-agnostic issue tracker contract.

- [Trello Implementation](components/issue_tracker_client_impl.md)  
  Documents the Trello-backed provider implementation.

- [FastAPI Service](components/issue_tracker_client_service.md)  
  Documents the deployed service package.

- [AI Client API](components/ai_client_api.md)  
  Documents the provider-agnostic AI client contract.

- [AI Client Implementation](components/ai_client_impl.md)  
  Documents the OpenAI-backed AI provider.

To run the documentation locally:

```bash
uv run mkdocs serve
```
