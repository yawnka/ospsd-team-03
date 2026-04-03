"""Service client adapter implementing the IssueTrackerClient interface."""

import httpx
from issue_tracker_client_api.client import (
    Comment,
    CommentAddError,
    Issue,
    IssueCloseError,
    IssueCreateError,
    IssueListError,
    IssueNotFoundError,
    IssueState,
    IssueTrackerClient,
)
from issue_tracker_client_service_client.api.default import (
    add_comment_boards_board_issues_issue_id_comments_post,
    close_issue_boards_board_issues_issue_id_close_post,
    create_issue_boards_board_issues_post,
    get_issue_boards_board_issues_issue_id_get,
    list_issues_boards_board_issues_get,
)
from issue_tracker_client_service_client.client import Client
from issue_tracker_client_service_client.models import (
    AddCommentIn,
    CommentOut,
    CreateIssueIn,
    IssueOut,
)

NOT_FOUND = 404


def _to_issue(issue: IssueOut) -> Issue:
    """Convert an IssueOut model to a domain Issue."""
    return Issue(
        id=issue.id,
        title=issue.title,
        body=issue.body,
        state=IssueState(issue.state),
    )


class ServiceClientAdapter(IssueTrackerClient):
    """Adapter that delegates calls to the remote FastAPI service."""

    def __init__(self, base_url: str) -> None:
        """Initialize the adapter with the base URL of the remote service."""
        self.base_url = base_url
        self._client = Client(base_url=base_url)

    def list_issues(self, board: str) -> list[Issue]:
        """Return all open issues for the given board."""
        try:
            response = list_issues_boards_board_issues_get.sync(
                board=board, client=self._client
            )
        except httpx.HTTPError as exc:
            msg = f"Failed to list issues for board {board}"
            raise IssueListError(msg) from exc

        if response is None:
            msg = f"Failed to list issues for board {board}"
            raise IssueListError(msg)

        if not isinstance(response, list):
            msg = f"Failed to list issues for board {board}"
            raise IssueListError(msg)

        return [_to_issue(issue) for issue in response]

    def get_issue(self, board: str, issue_id: int) -> Issue:
        """Return the issue identified by issue_id on board."""
        try:
            response = get_issue_boards_board_issues_issue_id_get.sync(
                board=board, issue_id=issue_id, client=self._client
            )
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == NOT_FOUND:
                msg = f"Issue {issue_id} not found"
                raise IssueNotFoundError(msg) from exc
            msg = f"Failed to get issue {issue_id}"
            raise IssueListError(msg) from exc
        except httpx.HTTPError as exc:
            msg = f"Failed to get issue {issue_id}"
            raise IssueListError(msg) from exc

        if response is None:
            msg = f"Issue {issue_id} not found"
            raise IssueNotFoundError(msg)

        if not isinstance(response, IssueOut):
            msg = f"Failed to get issue {issue_id}"
            raise IssueListError(msg)

        return _to_issue(response)

    def create_issue(self, board: str, title: str, body: str) -> Issue:
        """Open a new issue on board and return the created record."""
        payload = CreateIssueIn(title=title, body=body)
        try:
            response = create_issue_boards_board_issues_post.sync(
                board=board, body=payload, client=self._client
            )
        except httpx.HTTPError as exc:
            msg = "Failed to create issue"
            raise IssueCreateError(msg) from exc

        if not isinstance(response, IssueOut):
            msg = "Failed to create issue"
            raise IssueCreateError(msg)
        return _to_issue(response)

    def close_issue(self, board: str, issue_id: int) -> bool:
        """Close the issue identified by issue_id on board."""
        try:
            response = close_issue_boards_board_issues_issue_id_close_post.sync(
                board=board, issue_id=issue_id, client=self._client
            )
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == NOT_FOUND:
                msg = f"Issue {issue_id} not found"
                raise IssueNotFoundError(msg) from exc
            msg = f"Failed to close issue {issue_id}"
            raise IssueCloseError(msg) from exc
        except httpx.HTTPError as exc:
            msg = f"Failed to close issue {issue_id}"
            raise IssueCloseError(msg) from exc

        if response is None:
            msg = f"Failed to close issue {issue_id}"
            raise IssueCloseError(msg)
        return bool(response.additional_properties.get("success", False))

    def add_comment(self, board: str, issue_id: int, body: str) -> Comment:
        """Post a comment on issue_id on board and return the created record."""
        payload = AddCommentIn(body=body)
        try:
            response = add_comment_boards_board_issues_issue_id_comments_post.sync(
                board=board, issue_id=issue_id, body=payload, client=self._client
            )
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == NOT_FOUND:
                msg = f"Issue {issue_id} not found"
                raise IssueNotFoundError(msg) from exc
            msg = "Failed to add comment"
            raise CommentAddError(msg) from exc
        except httpx.HTTPError as exc:
            msg = "Failed to add comment"
            raise CommentAddError(msg) from exc

        if not isinstance(response, CommentOut):
            msg = "Failed to add comment"
            raise CommentAddError(msg)
        return Comment(id=response.id, body=response.body)
