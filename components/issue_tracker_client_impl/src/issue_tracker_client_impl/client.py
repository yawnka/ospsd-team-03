"""Default implementation of IssueTrackerClient backed by the Trello API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator

import requests
from api.client import Client  # type: ignore[import-untyped]
from api.issue import Status  # type: ignore[import-untyped]
from issue_tracker_client_api.client import (
    Board,
    BoardNotFoundError,
    Issue,
    IssueNotFoundError,
)

from issue_tracker_client_impl.status_map import (
    resolve_status,
)

BASE_URL = "https://api.trello.com/1"


class DefaultIssueTrackerClient(Client):  # type: ignore[misc]
    """Concrete IssueTrackerClient that talks to the Trello REST API."""

    def __init__(self, api_key: str, token: str) -> None:
        """Store Trello API credentials."""
        self._api_key = api_key
        self._api_token = token

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _auth(self) -> dict[str, str]:
        return {"key": self._api_key, "token": self._api_token}

    def _get(self, path: str, **params: str) -> Any:  # noqa: ANN401
        resp = requests.get(
            f"{BASE_URL}/{path}",
            params={**self._auth(), **params},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def _put(self, path: str, **params: str) -> Any:  # noqa: ANN401
        resp = requests.put(
            f"{BASE_URL}/{path}",
            params={**self._auth(), **params},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **params: str) -> Any:  # noqa: ANN401
        resp = requests.post(
            f"{BASE_URL}/{path}",
            params={**self._auth(), **params},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def _delete(self, path: str) -> Any:  # noqa: ANN401
        resp = requests.delete(
            f"{BASE_URL}/{path}",
            params=self._auth(),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def _board_lists(self, board_id: str) -> list[dict[str, str]]:
        """Return all open lists on *board_id* as raw dicts."""
        return self._get(  # type: ignore[no-any-return]
            f"boards/{board_id}/lists",
            filter="open",
            fields="id,name",
        )

    def _list_id_to_name(self, board_id: str) -> dict[str, str]:
        """Return a mapping of list-id → list-name for *board_id*."""
        return {lst["id"]: lst["name"] for lst in self._board_lists(board_id)}

    def _issue_from_card(
        self, card: dict[str, Any], board_id: str, list_name: str
    ) -> Issue:
        members: list[str] | None = card.get("idMembers") or None
        canonical_board_id = card.get("idBoard", board_id)
        return Issue(
            id=card["id"],
            board_id=canonical_board_id,
            title=card["name"],
            desc=card.get("desc", ""),
            status=resolve_status(list_name),
            members=members,
            due_date=card.get("due"),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_boards(self) -> Iterator[Board]:
        """Return all boards visible to the authenticated user."""
        boards: list[dict[str, str]] = self._get("members/me/boards", fields="id,name")
        return iter(Board(id=b["id"], name=b["name"]) for b in boards)

    def get_board(self, board_id: str) -> Board:
        """Return the board identified by *board_id*.

        Raises:
            BoardNotFoundError: If the board does not exist or is inaccessible.

        """
        try:
            board: dict[str, str] = self._get(f"boards/{board_id}", fields="id,name")
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:  # noqa: PLR2004
                msg = f"Board {board_id!r} not found"
                raise BoardNotFoundError(msg) from exc
            raise
        return Board(id=board["id"], name=board["name"])

    def get_issues(
        self, board_id: str, status: Status | None = None
    ) -> Iterator[Issue]:
        """Return issues on *board_id*, optionally filtered by *status*."""
        id_to_name = self._list_id_to_name(board_id)

        cards: list[dict[str, Any]] = self._get(
            f"boards/{board_id}/cards",
            filter="open",
            fields="id,idBoard,name,desc,idList,idMembers,due",
        )

        issues: list[Issue] = []
        for card in cards:
            list_name = id_to_name.get(card["idList"], "")
            issue = self._issue_from_card(card, board_id, list_name)
            if status is not None and issue.status != status:
                continue
            issues.append(issue)

        return iter(issues)

    def get_issue(self, issue_id: str) -> Issue:
        """Return the issue (Trello card) identified by its full card ID.

        Raises:
            IssueNotFoundError: If the card does not exist.

        """
        try:
            card: dict[str, Any] = self._get(
                f"cards/{issue_id}",
                fields="id,idBoard,name,desc,idList,idMembers,due",
            )
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code in (400, 404):
                msg = f"Issue {issue_id!r} not found"
                raise IssueNotFoundError(msg) from exc
            raise

        board_id: str = card["idBoard"]
        list_info: dict[str, str] = self._get(f"lists/{card['idList']}", fields="name")
        return self._issue_from_card(card, board_id, list_info["name"])

    def create_issue(  # noqa: PLR0913
        self,
        title: str,
        board_id: str,
        desc: str | None = None,
        members: list[str] | None = None,
        due_date: str | None = None,
        status: Status = Status.TO_DO,
    ) -> Issue:
        """Create a new card in the list matching *status* on *board_id*."""
        board_lists = self._board_lists(board_id)
        if not board_lists:
            msg = f"Board {board_id!r} has no open lists"
            raise ValueError(msg)

        target_list = next(
            (lst for lst in board_lists if resolve_status(lst["name"]) == status),
            board_lists[0],
        )

        params: dict[str, str] = {"idList": target_list["id"], "name": title}
        if desc is not None:
            params["desc"] = desc
        if due_date is not None:
            params["due"] = due_date
        if members is not None:
            params["idMembers"] = ",".join(members)

        card: dict[str, Any] = self._post("cards", **params)
        return self._issue_from_card(card, board_id, target_list["name"])

    def _resolve_status_list_id(
        self, issue_id: str, status: Status, board_id: str | None
    ) -> str | None:
        """Return the Trello list ID that matches *status* on the card's board."""
        target_board_id = board_id
        if target_board_id is None:
            try:
                card_info: dict[str, Any] = self._get(
                    f"cards/{issue_id}", fields="idBoard"
                )
            except requests.HTTPError as exc:
                if exc.response is not None and exc.response.status_code in (400, 404):
                    msg = f"Issue {issue_id!r} not found"
                    raise IssueNotFoundError(msg) from exc
                raise
            target_board_id = card_info["idBoard"]
        board_lists = self._board_lists(target_board_id)
        target_list = next(
            (lst for lst in board_lists if resolve_status(lst["name"]) == status),
            None,
        )
        return target_list["id"] if target_list is not None else None

    def update_issue(  # noqa: C901, PLR0913
    self,
    issue_id: str,
    title: str | None = None,
    desc: str | None = None,
    members: list[str] | None = None,
    due_date: str | None = None,
    status: Status | None = None,
    board_id: str | None = None,
    ) -> Issue:
        """Update fields on the card identified by *issue_id*.

        Raises:
            IssueNotFoundError: If the card does not exist.
            ValueError: If Trello rejects the update for another reason.

        """
        params: dict[str, str] = {}

        if title is not None:
            params["name"] = title

        if desc is not None:
            params["desc"] = desc

        if due_date is not None:
            params["due"] = due_date

        if members is not None:
            params["idMembers"] = ",".join(members)

        if status is not None:
            try:
                list_id = self._resolve_status_list_id(issue_id, status, board_id)
            except IssueNotFoundError:
                raise
            except Exception as exc:
                msg = f"Failed to resolve status list for issue {issue_id!r}: {exc}"
                raise ValueError(msg) from exc

            if list_id is not None:
                params["idList"] = list_id

        try:
            updated: dict[str, Any] = self._put(f"cards/{issue_id}", **params)
        except requests.HTTPError as exc:
            if exc.response is None:
                raise

            status_code = exc.response.status_code
            response_text = exc.response.text

            if status_code == 404:  # noqa: PLR2004
                msg = f"Issue {issue_id!r} not found"
                raise IssueNotFoundError(msg) from exc

            msg = (
                f"Trello update failed for issue {issue_id!r}: "
                f"{status_code} {response_text}"
            )
            raise ValueError(msg) from exc

        list_info: dict[str, Any] = self._get(
            f"lists/{updated['idList']}",
            fields="name",
        )
        return self._issue_from_card(updated, updated["idBoard"], list_info["name"])

    def update_board(self, board_id: str, name: str | None = None) -> Board:
        """Update fields on the board identified by *board_id*.

        Raises:
            BoardNotFoundError: If the board does not exist.

        """
        params: dict[str, str] = {}
        if name is not None:
            params["name"] = name

        try:
            board: dict[str, str] = self._put(f"boards/{board_id}", **params)
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code in (400, 404):
                msg = f"Board {board_id!r} not found"
                raise BoardNotFoundError(msg) from exc
            raise

        return Board(id=board["id"], name=board["name"])

    def delete_issue(self, issue_id: str) -> bool:
        """Archive the card identified by *issue_id*.

        Returns True if successfully archived.

        Raises:
            IssueNotFoundError: If the card does not exist.

        """
        try:
            self._put(f"cards/{issue_id}", closed="true")
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code in (400, 404):
                msg = f"Issue {issue_id!r} not found"
                raise IssueNotFoundError(msg) from exc
            raise
        return True

    def delete_board(self, board_id: str) -> bool:
        """Close (archive) the board identified by *board_id*.

        Trello does not expose a public permanent-delete endpoint for boards;
        closing via PUT closed=true is the standard operation and what the
        Trello web UI does when a user "closes" a board.

        Returns True if successfully closed.

        Raises:
            BoardNotFoundError: If the board does not exist.

        """
        try:
            self._put(f"boards/{board_id}", closed="true")
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code in (400, 404):
                msg = f"Board {board_id!r} not found"
                raise BoardNotFoundError(msg) from exc
            raise
        return True

    def create_board(self, name: str) -> Board:
        """Create a new Trello board with the given *name*.

        Returns the created Board.
        """
        board: dict[str, str] = self._post("boards", name=name, defaultLists="false")
        return Board(id=board["id"], name=board["name"])
