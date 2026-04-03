"""issue_tracker_client_adapter — service-client-backed IssueTrackerClient.

Importing this package automatically registers ServiceClientAdapter
as the active factory in issue_tracker_client_api.
"""

import os

import issue_tracker_client_api.client as _api

from issue_tracker_client_adapter.adapter import ServiceClientAdapter


def _make_adapter() -> ServiceClientAdapter:
    url = os.environ.get("ISSUE_TRACKER_SERVICE_URL")
    if not url:
        msg = (
            "Environment variable ISSUE_TRACKER_SERVICE_URL is not set. "
            "Example: export ISSUE_TRACKER_SERVICE_URL=http://localhost:8000"
        )
        raise ValueError(msg)
    session_id = os.environ.get("ISSUE_TRACKER_SESSION_ID")
    return ServiceClientAdapter(base_url=url, session_id=session_id)


_api.register(_make_adapter)
