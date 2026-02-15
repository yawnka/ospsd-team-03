"""Abstract contract for an issue-tracker client."""

import abc
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Issue:
    """Immutable snapshot of a single issue."""

    id: int
    title: str
    body: str
    state: str


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

        In Trello *board* is a board identifier; other providers may map it
        differently (e.g. a project key or workspace slug).
        """

    @abc.abstractmethod
    def get_issue(self, board: str, issue_id: int) -> Issue:
        """Return the issue identified by *issue_id* on *board*."""

    @abc.abstractmethod
    def create_issue(self, board: str, title: str, body: str) -> Issue:
        """Open a new issue on *board* and return the created record."""

    @abc.abstractmethod
    def close_issue(self, board: str, issue_id: int) -> None:
        """Close the issue identified by *issue_id* on *board*."""

    @abc.abstractmethod
    def add_comment(self, board: str, issue_id: int, body: str) -> Comment:
        """Post a comment on *issue_id* on *board* and return the created record."""


_factories: list[Callable[[], IssueTrackerClient]] = []


def register(factory: Callable[[], IssueTrackerClient]) -> None:
    """Register a callable that produces an IssueTrackerClient.

    Replaces any previously registered factory.
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
