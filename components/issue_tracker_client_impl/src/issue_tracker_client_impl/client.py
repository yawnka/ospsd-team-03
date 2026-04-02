"""Default implementation of IssueTrackerClient."""

import os

import requests
from issue_tracker_client_api.client import (
    Comment,
    Issue,
    IssueState,
    IssueTrackerClient,
)

BASE_URL = "https://api.trello.com/1"


class DefaultIssueTrackerClient(IssueTrackerClient):
    """Default concrete implementation of IssueTrackerClient."""

    def __init__(self) -> None:
        """Initialize Trello client with credentials from environment variables."""
        self._api_key: str = os.environ["TRELLO_API_KEY"]
        self._api_token: str = os.environ["TRELLO_API_TOKEN"]

    def _auth_params(self) -> dict[str, str]:
        """Return the key/token query params needed for every Trello call."""
        return {"key": self._api_key, "token": self._api_token}

    def _resolve_card_id(self, board: str, issue_id: int) -> str:
        """Given a board and an idShort (int), return the full Trello card ID string."""
        resp = requests.get(
            f"{BASE_URL}/boards/{board}/cards",
            params={**self._auth_params(), "fields": "idShort,id"},
            timeout=30,
        )
        resp.raise_for_status()
        for card in resp.json():
            if card["idShort"] == issue_id:
                return str(card["id"])
        msg = f"Card with idShort={issue_id} not found on board {board}"
        raise ValueError(msg)

    def list_issues(self, board: str) -> list[Issue]:
        """Return all open issues for *board*."""
        resp = requests.get(
            f"{BASE_URL}/boards/{board}/cards",
            params={
                **self._auth_params(),
                "filter": "open",
                "fields": "idShort,name,desc,closed",
            },
            timeout=30,
        )
        resp.raise_for_status()
        return [
            Issue(
                id=card["idShort"],
                title=card["name"],
                body=card.get("desc", ""),
                state=IssueState.CLOSED if card.get("closed") else IssueState.OPEN,
            )
            for card in resp.json()
        ]

    def get_issue(self, board: str, issue_id: int) -> Issue:
        """Return the issue identified by *issue_id* on *board*."""
        card_id = self._resolve_card_id(board, issue_id)
        resp = requests.get(
            f"{BASE_URL}/cards/{card_id}",
            params={**self._auth_params(), "fields": "idShort,name,desc,closed"},
            timeout=30,
        )
        resp.raise_for_status()
        card = resp.json()
        return Issue(
            id=card["idShort"],
            title=card["name"],
            body=card.get("desc", ""),
            state=IssueState.CLOSED if card.get("closed") else IssueState.OPEN,
        )

    def create_issue(self, board: str, title: str, body: str) -> Issue:
        """Open a new issue on *board* and return the created record."""
        # Get the first list on the board to place the card
        lists_resp = requests.get(
            f"{BASE_URL}/boards/{board}/lists",
            params={**self._auth_params(), "filter": "open", "fields": "id"},
            timeout=30,
        )
        lists_resp.raise_for_status()
        board_lists = lists_resp.json()
        if not board_lists:
            msg = f"Board {board} has no open lists"
            raise ValueError(msg)
        target_list_id = board_lists[0]["id"]

        # Create the card
        resp = requests.post(
            f"{BASE_URL}/cards",
            params={
                **self._auth_params(),
                "idList": target_list_id,
                "name": title,
                "desc": body,
            },
            timeout=30,
        )
        resp.raise_for_status()
        card = resp.json()
        return Issue(
            id=card["idShort"],
            title=card["name"],
            body=card.get("desc", ""),
            state=IssueState.OPEN,
        )

    def close_issue(self, board: str, issue_id: int) -> bool:
        """Close the issue identified by *issue_id* on *board*.

        Returns True if the issue was successfully closed.

        Raises:
            requests.HTTPError: If the API request fails.
            ValueError: If *issue_id* does not exist on *board*.

        """
        card_id = self._resolve_card_id(board, issue_id)
        resp = requests.put(
            f"{BASE_URL}/cards/{card_id}",
            params={**self._auth_params(), "closed": "true"},
            timeout=30,
        )
        resp.raise_for_status()
        return True

    def add_comment(self, board: str, issue_id: int, body: str) -> Comment:
        """Post a comment on *issue_id* on *board* and return the created record."""
        card_id = self._resolve_card_id(board, issue_id)
        resp = requests.post(
            f"{BASE_URL}/cards/{card_id}/actions/comments",
            params={**self._auth_params(), "text": body},
            timeout=30,
        )
        resp.raise_for_status()
        action = resp.json()
        return Comment(
            id=int(action["id"][-8:], 16),
            body=action["data"]["text"],
        )
