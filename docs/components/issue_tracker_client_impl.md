# issue_tracker_client_impl

# DRAFT VERSION of what we might do

## Overview

This package provides the default implementation of `IssueTrackerClient`.

It currently targets Trello and treats Trello cards as issues.

---

## Authentication

Requires the environment variable:

- `ISSUE_TRACKER_TOKEN`

If missing, client creation may fail.

---

## Dependency Injection Wiring

Importing this package automatically registers the default implementation.

Example:

```python
import issue_tracker_client_api.client as api
import issue_tracker_client_impl

client = api.get_client()
