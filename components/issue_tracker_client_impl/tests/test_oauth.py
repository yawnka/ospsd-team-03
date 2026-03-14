"""Unit tests for the OAuth 2.0 helper functions."""

from unittest.mock import MagicMock, patch

import pytest
from issue_tracker_client_impl.oauth import (
build_authorization_url,
exchange_code_for_token,
refresh_access_token,
)

pytestmark = pytest.mark.unit

FAKE_CLIENT_ID = "fake-client-id"
FAKE_CLIENT_SECRET = "fake-client-secret"  # noqa: S105 — test credential
FAKE_REDIRECT_URI = "http://localhost:8000/auth/callback"

OAUTH_ENV = {
"OAUTH_CLIENT_ID": FAKE_CLIENT_ID,
"OAUTH_CLIENT_SECRET": FAKE_CLIENT_SECRET,
"REDIRECT_URI": FAKE_REDIRECT_URI,
}


def test_build_authorization_url_contains_base_url() -> None:
    """Returned URL starts with the Google OAuth authorize endpoint."""
    with patch.dict("os.environ", OAUTH_ENV):
        url = build_authorization_url(state="abc123")
    assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth")


def test_build_authorization_url_contains_client_id() -> None:
    """Returned URL includes the client_id query parameter."""
    with patch.dict("os.environ", OAUTH_ENV):
        url = build_authorization_url(state="abc123")
    assert f"client_id={FAKE_CLIENT_ID}" in url


def test_build_authorization_url_contains_state() -> None:
    """Returned URL includes the state parameter for CSRF protection."""
    with patch.dict("os.environ", OAUTH_ENV):
        url = build_authorization_url(state="xyz789")
    assert "state=xyz789" in url


def test_build_authorization_url_contains_redirect_uri() -> None:
    """Returned URL includes the redirect_uri query parameter."""
    with patch.dict("os.environ", OAUTH_ENV):
        url = build_authorization_url(state="abc123")
    assert "redirect_uri=" in url


def test_exchange_code_for_token_posts_to_google() -> None:
    """exchange_code_for_token POSTs to the Google token endpoint."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"access_token": "at", "refresh_token": "rt"}

    with (
        patch.dict("os.environ", OAUTH_ENV),
        patch("issue_tracker_client_impl.oauth.requests.post", return_value=mock_resp)
    as mock_post,
    ):
        exchange_code_for_token(code="auth-code-123")

    mock_post.assert_called_once()
    call_url = mock_post.call_args[0][0]
    assert call_url == "https://oauth2.googleapis.com/token"


def test_exchange_code_for_token_sends_correct_data() -> None:
    """exchange_code_for_token sends the authorization code and credentials."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"access_token": "at"}

    with (
        patch.dict("os.environ", OAUTH_ENV),
        patch("issue_tracker_client_impl.oauth.requests.post", return_value=mock_resp)
    as mock_post,
    ):
        exchange_code_for_token(code="auth-code-123")

    data = mock_post.call_args[1]["data"]
    assert data["grant_type"] == "authorization_code"
    assert data["code"] == "auth-code-123"
    assert data["client_id"] == FAKE_CLIENT_ID


def test_exchange_code_for_token_returns_json() -> None:
    """exchange_code_for_token returns the parsed JSON response."""
    expected = {"access_token": "at", "refresh_token": "rt", "expires_in": 3600}
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = expected

    with (
        patch.dict("os.environ", OAUTH_ENV),
        patch("issue_tracker_client_impl.oauth.requests.post", return_value=mock_resp),
    ):
        result = exchange_code_for_token(code="auth-code-123")

    assert result == expected


def test_refresh_access_token_posts_to_google() -> None:
    """refresh_access_token POSTs to the Google token endpoint."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"access_token": "new-at"}

    with (
        patch.dict("os.environ", OAUTH_ENV),
        patch("issue_tracker_client_impl.oauth.requests.post", return_value=mock_resp)
    as mock_post,
    ):
        refresh_access_token(refresh_token="rt-123")  # noqa: S106 — test credential

    data = mock_post.call_args[1]["data"]
    assert data["grant_type"] == "refresh_token"
    assert data["refresh_token"] == "rt-123"  # noqa: S105 — test credential


def test_refresh_access_token_returns_json() -> None:
    """refresh_access_token returns the parsed JSON response."""
    expected = {"access_token": "new-at", "expires_in": 3600}
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = expected

    with (
        patch.dict("os.environ", OAUTH_ENV),
        patch("issue_tracker_client_impl.oauth.requests.post", return_value=mock_resp),
    ):
        result = refresh_access_token(refresh_token="rt-123")  # noqa: S106 — test credential

    assert result == expected
