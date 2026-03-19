# issue-tracker-client-adapter

An adapter that implements the `IssueTrackerClient` interface by delegating calls to the remote FastAPI issue tracker service.

## Usage

```python
from issue_tracker_client_adapter import ServiceClientAdapter

adapter = ServiceClientAdapter(base_url="http://localhost:8000")

# List all open issues on a board
issues = adapter.list_issues("my-board")

# Get a single issue
issue = adapter.get_issue("my-board", issue_id=1)

# Create a new issue
new_issue = adapter.create_issue("my-board", title="Bug report", body="Something broke")

# Close an issue (returns True on success)
closed = adapter.close_issue("my-board", issue_id=1)

# Add a comment
comment = adapter.add_comment("my-board", issue_id=1, body="Looking into this")
```

## Configuration

Set the `ISSUE_TRACKER_SERVICE_URL` environment variable to the base URL of the running issue tracker service:

```bash
export ISSUE_TRACKER_SERVICE_URL="http://localhost:8000"
```

Importing the package automatically registers `ServiceClientAdapter` as the active factory in `issue_tracker_client_api`, so you can use the standard DI interface:

```python
import issue_tracker_client_adapter  # triggers registration
from issue_tracker_client_api.client import get_client

client = get_client()
```

You can also construct the adapter directly if needed:

```python
adapter = ServiceClientAdapter(base_url="http://localhost:8000")
```

## Running tests

```bash
uv run pytest components/issue_tracker_client_adapter
```
