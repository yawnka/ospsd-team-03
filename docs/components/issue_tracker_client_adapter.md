# Issue Tracker Client Adapter (Service Client)

## Overview

`issue_tracker_client_adapter` implements the `IssueTrackerClient` interface by delegating calls to the remote FastAPI service through the auto-generated client.

This is the **Adapter Pattern** in action: consumers use the same abstract interface regardless of whether the implementation runs locally or as a remote service.

## Purpose

- Achieves **location transparency** between local and remote usage
- Wraps the auto-generated HTTP client with the `IssueTrackerClient` ABC
- Registers itself via dependency injection on import

## Architecture

```text
Consumer Code
     |
     v
get_client()  --->  ServiceClientAdapter (this package)
                         |
                         v
              issue_tracker_client_service_client (HTTP calls)
                         |
                         v
              issue_tracker_client_service (FastAPI)
                         |
                         v
              issue_tracker_client_impl (Trello API)
```

## Dependency Injection

Importing the package auto-registers the adapter:

```python
import issue_tracker_client_adapter  # triggers registration
from issue_tracker_client_api.client import get_client

client = get_client()  # returns ServiceClientAdapter
issues = client.list_issues("my_board")
```

Requires `ISSUE_TRACKER_SERVICE_URL` to be set:

```bash
export ISSUE_TRACKER_SERVICE_URL="http://localhost:8000"
```

## Sanity Check

If `main.py` works by injecting the local implementation (`issue_tracker_client_impl`), it should also work by injecting this adapter (`issue_tracker_client_adapter`) with the service running remotely. The consumer code does not change.

## Testing

```bash
uv run pytest components/issue_tracker_client_adapter/tests/ -q
```
