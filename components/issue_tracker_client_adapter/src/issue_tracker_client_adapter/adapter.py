"""Service client adapter implementing the shared issue-tracker API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

import httpx
from api.board import Board as SharedBoard  # type: ignore[import-untyped]
from api.client import Client as SharedClient  # type: ignore[import-untyped]
from api.issue import Issue as SharedIssue  # type: ignore[import-untyped]
from api.issue import Status as SharedStatus
from issue_tracker_client_api.client import (
    BoardNotFoundError,
    IssueCreateError,
    IssueNotFoundError,
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


@dataclass(frozen=True)
class _BoardModel(SharedBoard):  # type: ignore[misc]
    """Concrete shared board returned by the adapter."""

    _id: str
    _board_name: str

    @property
    def id(self) -> str:
        """Return the board ID."""
        return self._id

    @property
    def board_name(self) -> str:
        """Return the board name."""
        return self._board_name


@dataclass(frozen=True)
class _IssueModel(SharedIssue):  # type: ignore[misc]
    """Concrete shared issue returned by the adapter."""

    _id: str
    _title: str
    _desc: str
    _members: list[str] | None
    _due_date: str | None
    _status: SharedStatus
    _board_id: str

    @property
    def id(self) -> str:
        """Return the issue ID."""
        return self._id

    @property
    def title(self) -> str:
        """Return the issue title."""
        return self._title

    @property
    def desc(self) -> str:
        """Return the issue description."""
        return self._desc

    @property
    def members(self) -> list[str] | None:
        """Return the issue members."""
        return self._members

    @property
    def due_date(self) -> str | None:
        """Return the issue due date."""
        return self._due_date

    @property
    def status(self) -> SharedStatus:
        """Return the issue status."""
        return self._status

    @property
    def board_id(self) -> str:
        """Return the owning board ID."""
        return self._board_id


def _status_to_value(status: SharedStatus | None) -> str | None:
    """Return the wire value for a shared status enum."""
    if status is None:
        return None
    return cast("str", status.value)


def _to_board(board: BoardOut) -> SharedBoard:
    """Convert a wire-format BoardOut into a shared board."""
    return _BoardModel(_id=board.id, _board_name=board.board_name)


def _to_issue(issue: IssueOut) -> SharedIssue:
    """Convert a wire-format IssueOut into a shared issue."""
    return _IssueModel(
        _id=issue.id,
        _board_id=issue.board_id,
        _title=issue.title,
        _desc=issue.desc,
        _status=SharedStatus(issue.status),
        _members=issue.members,
        _due_date=issue.due_date,
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


class ServiceClientAdapter(SharedClient):  # type: ignore[misc]
    """Adapter that delegates shared-API calls to the remote FastAPI service."""

    def __init__(self, base_url: str, session_id: str | None = None) -> None:
        """Initialize the adapter with the base URL of the remote service."""
        self.base_url = base_url
        self._session_id: str | Unset = session_id if session_id is not None else UNSET
        self._client = Client(base_url=base_url, raise_on_unexpected_status=True)

    def get_boards(self) -> Iterator[SharedBoard]:
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

    def get_board(self, board_id: str) -> SharedBoard:
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
        status: SharedStatus | None = None,
    ) -> Iterator[SharedIssue]:
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

    def get_issue(self, issue_id: str) -> SharedIssue:
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
        status: SharedStatus = SharedStatus.TO_DO,
    ) -> SharedIssue:
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
        status: SharedStatus | None = None,
        board_id: str | None = None,
    ) -> SharedIssue:
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

    def create_board(self, name: str) -> SharedBoard:
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

    def update_board(self, board_id: str, name: str | None = None) -> SharedBoard:
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
