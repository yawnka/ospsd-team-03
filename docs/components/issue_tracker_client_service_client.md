# Issue Tracker Service Client (Auto-Generated)

## Overview

`issue_tracker_client_service_client` is a **type-safe HTTP client** auto-generated from the FastAPI service's OpenAPI specification using `openapi-python-client`.

It provides Python modules for every API endpoint, with both synchronous and asynchronous variants.

## Purpose

- Provides a thin, generated networking layer for calling the service
- Ensures type safety by generating models from the OpenAPI schema
- Used internally by the `ServiceClientAdapter` to bridge network calls

This package should **not** be edited manually. Regenerate it when the service API changes.

## Usage

```python
from issue_tracker_client_service_client import AuthenticatedClient
from issue_tracker_client_service_client.api.default import list_issues_boards_board_issues_get

client = AuthenticatedClient(base_url="http://localhost:8000", token="")

# Synchronous call
issues = list_issues_boards_board_issues_get.sync(board="my_board", client=client)

# Async call
issues = await list_issues_boards_board_issues_get.asyncio(board="my_board", client=client)
```

## Generated Structure

Each endpoint produces a Python module with four functions:

| Function | Description |
|----------|-------------|
| `sync` | Blocking request, returns parsed data or `None` |
| `sync_detailed` | Blocking request, returns full `Response` object |
| `asyncio` | Async version of `sync` |
| `asyncio_detailed` | Async version of `sync_detailed` |

## Regenerating

When the FastAPI service endpoints change:

```bash
# Start the service locally
uv run uvicorn issue_tracker_client_service.app:app

# Regenerate the client from the OpenAPI spec
openapi-python-client update --url http://localhost:8000/openapi.json
```

## Testing

This package is auto-generated and excluded from ruff/mypy checks. It is tested indirectly through the adapter tests.
