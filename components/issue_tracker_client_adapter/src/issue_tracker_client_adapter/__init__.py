"""issue_tracker_client_adapter — service-client-backed IssueTrackerClient.

Importing this package automatically registers ServiceClientAdapter
as the active factory in issue_tracker_client_api.
"""

import os

import issue_tracker_client_api.client as _api

from issue_tracker_client_adapter.adapter import ServiceClientAdapter

_url = os.environ.get("ISSUE_TRACKER_SERVICE_URL")
if not _url:
    raise ValueError(
        "환경변수 ISSUE_TRACKER_SERVICE_URL이 설정되지 않았습니다. "
        "예: export ISSUE_TRACKER_SERVICE_URL=http://localhost:8000"
    )

_api.register(lambda: ServiceClientAdapter(base_url=_url))

__all__ = ["ServiceClientAdapter"]
