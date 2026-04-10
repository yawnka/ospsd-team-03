"""Service client adapter implementing the shared issue-tracker API."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
from issue_tracker_client_api.client import (
    Board,
    BoardNotFoundError,
    Issue,
    IssueCreateError,
    IssueNotFoundError,
    IssueTrackerClient,
    Status,
)
from issue_tracker_client_service_client.api.default import (
    create_board_boards_post,
    create_issue_boards_board_id_issues_post,
    delete_board_boards_board_id_delete,
    delete_issue_issues_issue_id_delete,
    get_board_boards_board_id_get,
    get_boards_boards_get,
    get_issue_issues_issue_id_get,
    get_issues_boards_board_id_issues_get,
    update_board_boards_board_id_patch,
    update_issue_issues_issue_id_patch,
)
from issue_tracker_client_service_client.client import Client
from issue_tracker_client_service_client.models import (
    BoardOut,
    CreateBoardIn,
    CreateIssueIn,
    CreateIssueInStatus,
    IssueOut,
    SuccessOut,
    UpdateBoardIn,
    UpdateIssueIn,
    UpdateIssueInStatusType0,
)
from issue_tracker_client_service_client.types import UNSET, Unset

from issue_tracker_client_service_client import errors

if TYPE_CHECKING:
    from collections.abc import Iterator

NOT_FOUND = 404


def _status_to_value(status: Status | str | None) -> str | None:
    """Normalize a status enum or string to the wire-format string."""
    if status is None:
        return None
    if isinstance(status, Status):
        return status.value
    return status


def _to_board(board: BoardOut) -> Board:
    """Convert a wire-format BoardOut into the local API Board."""
    return Board(id=board.id, name=board.board_name)


def _to_issue(issue: IssueOut) -> Issue:
    """Convert a wire-format IssueOut into the local API Issue."""
    return Issue(
        id=issue.id,
        board_id=issue.board_id,
        title=issue.title,
        desc=issue.desc,
        status=Status(issue.status),
        members=issue.members,
        due_date=issue.due_date,
    )


def _raise_unexpected_issue_error(issue_id: str, exc: errors.UnexpectedStatus) -> None:
    """Raise the appropriate issue-layer error for an unexpected status."""
    if exc.status_code == NOT_FOUND:
        msg = f"Issue {issue_id!r} not found"
        raise IssueNotFoundError(msg) from exc
    msg = f"Unexpected service response while handling issue {issue_id!r}"
    raise RuntimeError(msg) from exc


def _raise_unexpected_board_error(board_id: str, exc: errors.UnexpectedStatus) -> None:
    """Raise the appropriate board-layer error for an unexpected status."""
    if exc.status_code == NOT_FOUND:
        msg = f"Board {board_id!r} not found"
        raise BoardNotFoundError(msg) from exc
    msg = f"Unexpected service response while handling board {board_id!r}"
    raise RuntimeError(msg) from exc


class ServiceClientAdapter(IssueTrackerClient):
    """Adapter that delegates shared-API calls to the remote FastAPI service."""

    def __init__(self, base_url: str, session_id: str | None = None) -> None:
        """Initialize the adapter with the base URL of the remote service."""
        self.base_url = base_url
        self._session_id: str | Unset = session_id if session_id is not None else UNSET
        self._client = Client(base_url=base_url, raise_on_unexpected_status=True)

    def get_boards(self) -> Iterator[Board]:
        """Return an iterator of boards from the remote service."""
        try:
            response = get_boards_boards_get.sync(
                client=self._client,
                session_id=self._session_id,
            )
        except httpx.HTTPError as exc:
            msg = "Failed to list boards"
            raise RuntimeError(msg) from exc

        if not isinstance(response, list):
            msg = "Invalid response when listing boards"
            raise TypeError(msg)

        return iter(_to_board(board) for board in response)

    def get_board(self, board_id: str) -> Board:
        """Return the board identified by *board_id*."""
        try:
            response = get_board_boards_board_id_get.sync(
                board_id=board_id,
                client=self._client,
                session_id=self._session_id,
            )
        except errors.UnexpectedStatus as exc:
            _raise_unexpected_board_error(board_id, exc)
        except httpx.HTTPError as exc:
            msg = f"Failed to get board {board_id!r}"
            raise RuntimeError(msg) from exc

        if not isinstance(response, BoardOut):
            msg = f"Invalid response when getting board {board_id!r}"
            raise TypeError(msg)

        return _to_board(response)

    def get_issues(
        self,
        board_id: str,
        status: Status | None = None,
    ) -> Iterator[Issue]:
        """Return issues on *board_id*, optionally filtered by *status*."""
        try:
            response = get_issues_boards_board_id_issues_get.sync(
                board_id=board_id,
                client=self._client,
                session_id=self._session_id,
            )
        except errors.UnexpectedStatus as exc:
            _raise_unexpected_board_error(board_id, exc)
        except httpx.HTTPError as exc:
            msg = f"Failed to list issues for board {board_id!r}"
            raise RuntimeError(msg) from exc

        if not isinstance(response, list):
            msg = f"Invalid response when listing issues for board {board_id!r}"
            raise TypeError(msg)

        issues = [_to_issue(issue) for issue in response]
        if status is not None:
            issues = [issue for issue in issues if issue.status == status]
        return iter(issues)

    def get_issue(self, issue_id: str) -> Issue:
        """Return the issue identified by *issue_id*."""
        try:
            response = get_issue_issues_issue_id_get.sync(
                issue_id=issue_id,
                client=self._client,
                session_id=self._session_id,
            )
        except errors.UnexpectedStatus as exc:
            _raise_unexpected_issue_error(issue_id, exc)
        except httpx.HTTPError as exc:
            msg = f"Failed to get issue {issue_id!r}"
            raise RuntimeError(msg) from exc

        if not isinstance(response, IssueOut):
            msg = f"Invalid response when getting issue {issue_id!r}"
            raise TypeError(msg)

        return _to_issue(response)

    def create_issue(  # noqa: PLR0913
        self,
        title: str,
        board_id: str,
        desc: str | None = None,
        members: list[str] | None = None,
        due_date: str | None = None,
        status: Status = Status.TO_DO,
    ) -> Issue:
        """Create a new issue in the given board."""
        payload = CreateIssueIn(
            title=title,
            desc=desc if desc is not None else UNSET,
            members=members if members is not None else UNSET,
            due_date=due_date if due_date is not None else UNSET,
            status=CreateIssueInStatus(_status_to_value(status)),
        )
        try:
            response = create_issue_boards_board_id_issues_post.sync(
                board_id=board_id,
                body=payload,
                client=self._client,
                session_id=self._session_id,
            )
        except errors.UnexpectedStatus as exc:
            if exc.status_code == NOT_FOUND:
                msg = f"Board {board_id!r} not found"
                raise IssueCreateError(msg) from exc
            msg = (
                "Unexpected service response while creating issue "
                f"in board {board_id!r}"
            )
            raise IssueCreateError(msg) from exc
        except httpx.HTTPError as exc:
            msg = f"Failed to create issue in board {board_id!r}"
            raise IssueCreateError(msg) from exc

        if not isinstance(response, IssueOut):
            msg = f"Invalid response when creating issue in board {board_id!r}"
            raise IssueCreateError(msg)

        return _to_issue(response)

    def update_issue(  # noqa: PLR0913
        self,
        issue_id: str,
        title: str | None = None,
        desc: str | None = None,
        members: list[str] | None = None,
        due_date: str | None = None,
        status: Status | None = None,
        board_id: str | None = None,
    ) -> Issue:
        """Update the issue identified by *issue_id*."""
        status_value = _status_to_value(status)
        payload = UpdateIssueIn(
            title=title if title is not None else UNSET,
            desc=desc if desc is not None else UNSET,
            members=members if members is not None else UNSET,
            due_date=due_date if due_date is not None else UNSET,
            status=(
                UpdateIssueInStatusType0(status_value)
                if status_value is not None
                else UNSET
            ),
            board_id=board_id if board_id is not None else UNSET,
        )
        try:
            response = update_issue_issues_issue_id_patch.sync(
                issue_id=issue_id,
                body=payload,
                client=self._client,
                session_id=self._session_id,
            )
        except errors.UnexpectedStatus as exc:
            _raise_unexpected_issue_error(issue_id, exc)
        except httpx.HTTPError as exc:
            msg = f"Failed to update issue {issue_id!r}"
            raise RuntimeError(msg) from exc

        if not isinstance(response, IssueOut):
            msg = f"Invalid response when updating issue {issue_id!r}"
            raise TypeError(msg)

        return _to_issue(response)

    def create_board(self, name: str) -> Board:
        """Create a new board and return it."""
        payload = CreateBoardIn(name=name)
        try:
            response = create_board_boards_post.sync(
                body=payload,
                client=self._client,
                session_id=self._session_id,
            )
        except httpx.HTTPError as exc:
            msg = f"Failed to create board {name!r}"
            raise RuntimeError(msg) from exc

        if not isinstance(response, BoardOut):
            msg = f"Invalid response when creating board {name!r}"
            raise TypeError(msg)

        return _to_board(response)

    def update_board(self, board_id: str, name: str | None = None) -> Board:
        """Update the board identified by *board_id*."""
        payload = UpdateBoardIn(name=name if name is not None else UNSET)
        try:
            response = update_board_boards_board_id_patch.sync(
                board_id=board_id,
                body=payload,
                client=self._client,
                session_id=self._session_id,
            )
        except errors.UnexpectedStatus as exc:
            _raise_unexpected_board_error(board_id, exc)
        except httpx.HTTPError as exc:
            msg = f"Failed to update board {board_id!r}"
            raise RuntimeError(msg) from exc

        if not isinstance(response, BoardOut):
            msg = f"Invalid response when updating board {board_id!r}"
            raise TypeError(msg)

        return _to_board(response)

    def delete_issue(self, issue_id: str) -> bool:
        """Delete the issue identified by *issue_id*."""
        try:
            response = delete_issue_issues_issue_id_delete.sync(
                issue_id=issue_id,
                client=self._client,
                session_id=self._session_id,
            )
        except errors.UnexpectedStatus as exc:
            _raise_unexpected_issue_error(issue_id, exc)
        except httpx.HTTPError as exc:
            msg = f"Failed to delete issue {issue_id!r}"
            raise RuntimeError(msg) from exc

        if not isinstance(response, SuccessOut):
            msg = f"Invalid response when deleting issue {issue_id!r}"
            raise TypeError(msg)

        return response.success

    def delete_board(self, board_id: str) -> bool:
        """Delete the board identified by *board_id*."""
        try:
            response = delete_board_boards_board_id_delete.sync(
                board_id=board_id,
                client=self._client,
                session_id=self._session_id,
            )
        except errors.UnexpectedStatus as exc:
            _raise_unexpected_board_error(board_id, exc)
        except httpx.HTTPError as exc:
            msg = f"Failed to delete board {board_id!r}"
            raise RuntimeError(msg) from exc

        if not isinstance(response, SuccessOut):
            msg = f"Invalid response when deleting board {board_id!r}"
            raise TypeError(msg)

        return response.success
