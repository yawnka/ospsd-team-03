"""Abstract contract for an issue-tracker client."""

import abc
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from enum import Enum


class Status(Enum):
    """Status values for an issue."""

    TO_DO = "to_do"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass(frozen=True)
class Board:
    """Immutable snapshot of a single board."""

    id: str
    name: str


@dataclass(frozen=True)
class Issue:
    """Immutable snapshot of a single issue."""

    id: str
    board_id: str
    title: str
    desc: str
    status: Status
    members: list[str] | None = field(default=None)
    due_date: str | None = None


class IssueNotFoundError(Exception):
    """Raised when a requested issue does not exist."""


class BoardNotFoundError(Exception):
    """Raised when a requested board does not exist."""


class IssueCreateError(Exception):
    """Raised when an issue could not be created."""


class IssueTrackerClient(abc.ABC):
    """Abstract contract for interacting with an issue tracker."""

    @abc.abstractmethod
    def get_issue(self, issue_id: str) -> Issue:
        """Return a single issue by its ID.

        Raises:
            IssueNotFoundError: If *issue_id* does not exist.

        """

    @abc.abstractmethod
    def get_board(self, board_id: str) -> Board:
        """Return a single board by its ID.

        Raises:
            BoardNotFoundError: If *board_id* does not exist.

        """

    @abc.abstractmethod
    def get_issues(
        self, board_id: str, status: Status | None = None
    ) -> Iterator[Issue]:
        """Return issues on *board_id*, optionally filtered by *status*."""

    @abc.abstractmethod
    def get_boards(self) -> Iterator[Board]:
        """Return an iterator of boards accessible to the authenticated user."""

    @abc.abstractmethod
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
        """Update an issue's fields.

        Raises:
            IssueNotFoundError: If *issue_id* does not exist.

        """

    @abc.abstractmethod
    def update_board(self, board_id: str, name: str | None = None) -> Board:
        """Update a board's fields.

        Raises:
            BoardNotFoundError: If *board_id* does not exist.

        """

    @abc.abstractmethod
    def delete_issue(self, issue_id: str) -> bool:
        """Archive the issue identified by *issue_id*.

        Returns True if successfully archived.

        Raises:
            IssueNotFoundError: If *issue_id* does not exist.

        """

    @abc.abstractmethod
    def delete_board(self, board_id: str) -> bool:
        """Delete a board by its ID.

        Returns True if successfully deleted.

        Raises:
            BoardNotFoundError: If *board_id* does not exist.

        """

    @abc.abstractmethod
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

    @abc.abstractmethod
    def create_board(self, name: str) -> Board:
        """Create a new board and return it."""


_factories: list[Callable[[], IssueTrackerClient]] = []


def register(factory: Callable[[], IssueTrackerClient]) -> None:
    """Register a no-arg callable that produces an IssueTrackerClient.

    *factory* may be a plain function or a class with a no-arg constructor
    (i.e. one that reads config from the environment rather than __init__
    parameters). Replaces any previously registered factory.
    """
    _factories.clear()
    _factories.append(factory)


def get_client(*, interactive: bool = False) -> IssueTrackerClient:  # noqa: ARG001
    """Return an IssueTrackerClient from the registered factory.

    Raises:
        RuntimeError: If no factory has been registered yet.

    """
    if not _factories:
        msg = "No IssueTrackerClient factory has been registered."
        raise RuntimeError(msg)
    return _factories[0]()
