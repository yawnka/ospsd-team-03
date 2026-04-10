"""Mapping between Trello list names and canonical issue statuses."""

from __future__ import annotations

# Maps lowercased Trello list name variants to a canonical status string.
LIST_NAME_TO_STATUS: dict[str, str] = {
    "to do": "to_do",
    "todo": "to_do",
    "backlog": "to_do",
    "new": "to_do",
    "open": "to_do",
    "in progress": "in_progress",
    "in-progress": "in_progress",
    "doing": "in_progress",
    "wip": "in_progress",
    "done": "completed",
    "completed": "completed",
    "complete": "completed",
    "closed": "completed",
    "finished": "completed",
}

# Preferred Trello list name to create/match when looking up by status.
STATUS_TO_LIST_NAME: dict[str, str] = {
    "to_do": "To Do",
    "in_progress": "In Progress",
    "completed": "Done",
}

VALID_STATUSES: frozenset[str] = frozenset(STATUS_TO_LIST_NAME)


def resolve_status(list_name: str) -> str:
    """Return the canonical status for a Trello list name.

    Falls back to ``"to_do"`` for unrecognised names.
    """
    return LIST_NAME_TO_STATUS.get(list_name.lower().strip(), "to_do")


def resolve_list_name(status: str) -> str:
    """Return the preferred Trello list name for a canonical *status*.

    Raises:
        ValueError: If *status* is not one of the recognised values.

    """
    if status not in STATUS_TO_LIST_NAME:
        msg = f"Unknown status {status!r}. Must be one of: {sorted(VALID_STATUSES)}"
        raise ValueError(msg)
    return STATUS_TO_LIST_NAME[status]
