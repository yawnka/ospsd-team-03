"""Service client adapter implementing the IssueTrackerClient interface."""

from issue_tracker_client_api.client import Comment, Issue, IssueState, IssueTrackerClient
from issue_tracker_client_service_client.client import AuthenticatedClient
from issue_tracker_client_service_client.api.default import (
    list_issues_boards_board_issues_get,
    get_issue_boards_board_issues_issue_id_get,
    create_issue_boards_board_issues_post,
    close_issue_boards_board_issues_issue_id_close_post,
    add_comment_boards_board_issues_issue_id_comments_post,
)
from issue_tracker_client_service_client.models import CreateIssueIn, AddCommentIn


class ServiceClientAdapter(IssueTrackerClient):
    """Adapter that delegates calls to the remote FastAPI service."""

    def __init__(self, base_url: str) -> None:
        self._client = AuthenticatedClient(base_url=base_url, token="")

    def list_issues(self, board: str) -> list[Issue]:
        response = list_issues_boards_board_issues_get.sync(board=board, client=self._client)
        if response is None:
            return []
        return [
            Issue(id=i.id, title=i.title, body=i.body, state=IssueState(i.state))
            for i in response
        ]

    def get_issue(self, board: str, issue_id: int) -> Issue:
        response = get_issue_boards_board_issues_issue_id_get.sync(
            board=board, issue_id=issue_id, client=self._client
        )
        if response is None:
            raise KeyError(f"Issue {issue_id} not found")
        return Issue(id=response.id, title=response.title, body=response.body, state=IssueState(response.state))

    def create_issue(self, board: str, title: str, body: str) -> Issue:
        payload = CreateIssueIn(title=title, body=body)
        response = create_issue_boards_board_issues_post.sync(
            board=board, body=payload, client=self._client
        )
        if response is None:
            raise RuntimeError("Failed to create issue")
        return Issue(id=response.id, title=response.title, body=response.body, state=IssueState(response.state))

    def close_issue(self, board: str, issue_id: int) -> bool:
        response = close_issue_boards_board_issues_issue_id_close_post.sync(
            board=board, issue_id=issue_id, client=self._client
        )
        if response is None:
            return False
        return bool(response.get("success", False))

    def add_comment(self, board: str, issue_id: int, body: str) -> Comment:
        payload = AddCommentIn(body=body)
        response = add_comment_boards_board_issues_issue_id_comments_post.sync(
            board=board, issue_id=issue_id, body=payload, client=self._client
        )
        if response is None:
            raise RuntimeError("Failed to add comment")
        return Comment(id=response.id, body=response.body)
