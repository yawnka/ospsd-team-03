# issue_tracker_client_impl

Default implementation package for `issue_tracker_client_api`.

Importing this package automatically registers `DefaultIssueTrackerClient as the active `IssueTrackerClient` factory.

This package is intended to provide the **concrete implementation layer** for the abstract contract defined in `issue_tracker_client_api`.

---

## What This Package Does

- Provides `DefaultIssueTrackerClient`
- Reads credentials from environment variables
- Automatically registers itself as the active client
- Implements the `IssueTrackerClient` interface

Once imported, application code can simply call:

```python
from issue_tracker_client_api.client import get_client

client = get_client()
```