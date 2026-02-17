"""issue_tracker_client_impl — default implementation of IssueTrackerClient.

Importing this package automatically registers DefaultIssueTrackerClient
as the active factory in issue_tracker_client_api.
"""

import issue_tracker_client_api.client as _api

from issue_tracker_client_impl.client import DefaultIssueTrackerClient

_api.register(DefaultIssueTrackerClient)
