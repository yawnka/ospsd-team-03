"""Helpers for service-side OAuth state and session handling."""


import secrets

from fastapi import HTTPException

# In-memory store of valid OAuth states
_STATE_STORE: set[str] = set()


def create_state() -> str:
    """Generate and store a one-time OAuth state token."""
    state = secrets.token_urlsafe(32)
    _STATE_STORE.add(state)
    return state


def consume_state(state: str) -> None:
    """Validate and remove a previously issued state token."""
    if state not in _STATE_STORE:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    _STATE_STORE.remove(state)

