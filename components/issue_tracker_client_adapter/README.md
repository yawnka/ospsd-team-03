# Issue Tracker Client Adapter

`issue_tracker_client_adapter` implements the `IssueTrackerClient` interface by delegating calls to the remote FastAPI issue tracker service.

This component provides location transparency: consumer code can use the same issue tracker contract whether the implementation is local or remote.

## Purpose

This component is responsible for:

- implementing the shared `IssueTrackerClient` interface,
- calling the generated service client,
- hiding HTTP details from consumers,
- preserving the same dependency injection pattern as the local implementation,
- allowing consumers to switch from an in-process provider to the deployed service.

## Configuration

Set `ISSUE_TRACKER_SERVICE_URL` to the base URL of the running issue tracker service.

```bash
export ISSUE_TRACKER_SERVICE_URL="http://localhost:8000"
```

For the deployed service, use:

```bash
export ISSUE_TRACKER_SERVICE_URL="https://issue-tracker-service-793028870171.us-central1.run.app"
```

## Dependency Injection Usage

Importing the adapter package registers `ServiceClientAdapter` as the active issue tracker client.

```python
import issue_tracker_client_adapter
from issue_tracker_client_api import get_client

client = get_client()
issues = client.list_issues("my-board")
print(issues)
```



## Direct Usage

You can also construct the adapter directly when explicit configuration is preferred.

```python
from issue_tracker_client_adapter import ServiceClientAdapter

adapter = ServiceClientAdapter(base_url="http://localhost:8000")
issues = adapter.list_issues("my-board")
print(issues)
```

## Dependencies

This component depends on:

- `issue_tracker_client_api` for the shared contract,
- `issue_tracker_client_service_client` for generated HTTP calls,
- the FastAPI service being reachable at the configured base URL.


## Testing 

Run this component's tests with:

```bash
uv run pytest components/issue_tracker_client_adapter/tests/
```

The tests should mock the generated HTTP client boundary. Unit tests should not require the deployed service to be running.