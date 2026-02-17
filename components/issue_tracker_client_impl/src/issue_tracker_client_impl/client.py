"""Default implementation of IssueTrackerClient."""

import os

from issue_tracker_client_api.client import Comment, Issue, IssueTrackerClient


class DefaultIssueTrackerClient(IssueTrackerClient):
    """Default concrete implementation of IssueTrackerClient."""

    def __init__(self) -> None:
        """Read credentials from environment variables.

        Raises:
            KeyError: If ISSUE_TRACKER_TOKEN is not set in the environment.

        """
        self._token: str = os.environ["ISSUE_TRACKER_TOKEN"]

    def list_issues(self, board: str) -> list[Issue]:
        """Return all open issues for *board*."""
        raise NotImplementedError

    def get_issue(self, board: str, issue_id: int) -> Issue:
        """Return the issue identified by *issue_id* in *board*."""
        raise NotImplementedError

    def create_issue(self, board: str, title: str, body: str) -> Issue:
        """Open a new issue in *board* and return the created record."""
        raise NotImplementedError

    def close_issue(self, board: str, issue_id: int) -> None:
        """Close the issue identified by *issue_id* in *board*."""
        raise NotImplementedError

    def add_comment(self, board: str, issue_id: int, body: str) -> Comment:
        """Post a comment on *issue_id* in *board* and return the created record."""
        raise NotImplementedError
