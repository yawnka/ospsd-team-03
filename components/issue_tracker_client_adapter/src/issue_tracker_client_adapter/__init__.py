"""issue_tracker_client_adapter — service-client-backed IssueTrackerClient.

Importing this package automatically registers ServiceClientAdapter
as the active factory in issue_tracker_client_api.
"""

import os

import issue_tracker_client_api.client as _api

from issue_tracker_client_adapter.adapter import ServiceClientAdapter

_api.register(lambda: ServiceClientAdapter(
    base_url=os.environ["ISSUE_TRACKER_SERVICE_URL"],
))

__all__ = ["ServiceClientAdapter"]
