"""Abstract contract for an issue-tracker client."""

import abc
import enum
from collections.abc import Callable
from dataclasses import dataclass


class IssueState(enum.Enum):
    """Lifecycle states for an issue."""

    OPEN = "open"
    CLOSED = "closed"


@dataclass(frozen=True)
class Issue:
    """Immutable snapshot of a single issue."""

    id: int
    title: str
    body: str
    state: IssueState


@dataclass(frozen=True)
class Comment:
    """Immutable snapshot of a single comment."""

    id: int
    body: str


class IssueTrackerClient(abc.ABC):
    """Abstract contract for interacting with an issue tracker."""

    @abc.abstractmethod
    def list_issues(self, board: str) -> list[Issue]:
        """Return all open issues for *board*.

        *board* is a provider-specific string identifier (e.g. a project key,
        workspace slug, or repository name) used solely as a lookup key.
        """

    @abc.abstractmethod
    def get_issue(self, board: str, issue_id: int) -> Issue:
        """Return the issue identified by *issue_id* on *board*."""

    @abc.abstractmethod
    def create_issue(self, board: str, title: str, body: str) -> Issue:
        """Open a new issue on *board* and return the created record."""

    @abc.abstractmethod
    def close_issue(self, board: str, issue_id: int) -> bool:
        """Close the issue identified by *issue_id* on *board*.

        Returns True if the issue was successfully closed.
        Raises on failure.
        """

    @abc.abstractmethod
    def add_comment(self, board: str, issue_id: int, body: str) -> Comment:
        """Post a comment on *issue_id* on *board* and return the created record."""


_factories: list[Callable[[], IssueTrackerClient]] = []


def register(factory: Callable[[], IssueTrackerClient]) -> None:
    """Register a no-arg callable that produces an IssueTrackerClient.

    *factory* may be a plain function or a class with a no-arg constructor
    (i.e. one that reads config from the environment rather than __init__
    parameters). Replaces any previously registered factory.
    """
    _factories.clear()
    _factories.append(factory)


def get_client() -> IssueTrackerClient:
    """Return an IssueTrackerClient from the registered factory.

    Raises:
        RuntimeError: If no factory has been registered yet.

    """
    if not _factories:
        msg = "No IssueTrackerClient factory has been registered."
        raise RuntimeError(msg)
    return _factories[0]()
