"""issue_tracker_client_adapter — service-client-backed IssueTrackerClient.

Importing this package automatically registers ServiceClientAdapter
as the active factory in issue_tracker_client_api.
"""

import os

import issue_tracker_client_api.client as _api

from issue_tracker_client_adapter.adapter import ServiceClientAdapter

_url = os.environ.get("ISSUE_TRACKER_SERVICE_URL")
if not _url:
    msg = (
        "Environment variable ISSUE_TRACKER_SERVICE_URL is not set. "
        "Example: export ISSUE_TRACKER_SERVICE_URL=http://localhost:8000"
    )
    raise ValueError(msg)

_url_str: str = _url
_api.register(lambda: ServiceClientAdapter(base_url=_url_str))

__all__ = ["ServiceClientAdapter"]
