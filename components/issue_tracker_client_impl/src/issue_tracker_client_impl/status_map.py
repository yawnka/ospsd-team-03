"""Mapping between Trello list names and canonical issue statuses."""

from __future__ import annotations

from issue_tracker_client_api.client import Status

# Maps lowercased Trello list name variants to a canonical Status enum value.
LIST_NAME_TO_STATUS: dict[str, Status] = {
    "to do": Status.TO_DO,
    "todo": Status.TO_DO,
    "backlog": Status.TO_DO,
    "new": Status.TO_DO,
    "open": Status.TO_DO,
    "in progress": Status.IN_PROGRESS,
    "in-progress": Status.IN_PROGRESS,
    "doing": Status.IN_PROGRESS,
    "wip": Status.IN_PROGRESS,
    "done": Status.COMPLETED,
    "completed": Status.COMPLETED,
    "complete": Status.COMPLETED,
    "closed": Status.COMPLETED,
    "finished": Status.COMPLETED,
}

# Preferred Trello list name to create/match when looking up by status.
STATUS_TO_LIST_NAME: dict[Status, str] = {
    Status.TO_DO: "To Do",
    Status.IN_PROGRESS: "In Progress",
    Status.COMPLETED: "Done",
}


def resolve_status(list_name: str) -> Status:
    """Return the canonical Status for a Trello list name.

    Falls back to ``Status.TO_DO`` for unrecognised names.
    """
    return LIST_NAME_TO_STATUS.get(list_name.lower().strip(), Status.TO_DO)


def resolve_list_name(status: Status) -> str:
    """Return the preferred Trello list name for a canonical *status*.

    Raises:
        ValueError: If *status* is not a recognised Status value.

    """
    if status not in STATUS_TO_LIST_NAME:
        msg = f"Unknown status {status!r}. Must be one of: {list(STATUS_TO_LIST_NAME)}"
        raise ValueError(msg)
    return STATUS_TO_LIST_NAME[status]
