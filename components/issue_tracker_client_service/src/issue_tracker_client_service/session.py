"""Simple in-memory session store for authenticated users."""

from dataclasses import dataclass


@dataclass(frozen=True)
class UserSession:
    """Represent an authenticated user session."""

    access_token: str
    refresh_token: str | None = None
    expires_at: float  | None = None


_SESSIONS: dict[str, UserSession] = {}


def save_session(
    session_id: str,
    access_token: str,
    refresh_token: str | None,
    expires_at: float  | None,
) -> None:
    """Persist a user session in memory."""
    _SESSIONS[session_id] = UserSession(
        access_token,
        refresh_token,
        expires_at,
    )


def get_session(session_id: str) -> UserSession | None:
    """Retrieve a session if it exists."""
    return _SESSIONS.get(session_id)
