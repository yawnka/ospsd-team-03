"""Unit tests for the Trello OAuth helper functions."""

from unittest.mock import patch

import pytest
from issue_tracker_client_impl.oauth import build_authorization_url

pytestmark = pytest.mark.unit

FAKE_API_KEY = "fake-trello-api-key"
FAKE_REDIRECT_URI = "http://localhost:8000/auth/callback"

OAUTH_ENV = {
    "TRELLO_API_KEY": FAKE_API_KEY,
    "REDIRECT_URI": FAKE_REDIRECT_URI,
}


def test_build_authorization_url_contains_base_url() -> None:
    """Returned URL starts with the Trello authorize endpoint."""
    with patch.dict("os.environ", OAUTH_ENV):
        url = build_authorization_url(state="abc123")
    assert url.startswith("https://trello.com/1/authorize")


def test_build_authorization_url_contains_api_key() -> None:
    """Returned URL includes the Trello API key."""
    with patch.dict("os.environ", OAUTH_ENV):
        url = build_authorization_url(state="abc123")
    assert f"key={FAKE_API_KEY}" in url


def test_build_authorization_url_contains_state() -> None:
    """Returned URL includes the state parameter for CSRF protection."""
    with patch.dict("os.environ", OAUTH_ENV):
        url = build_authorization_url(state="xyz789")
    assert "state%3Dxyz789" in url or "state=xyz789" in url


def test_build_authorization_url_contains_return_url() -> None:
    """Returned URL includes the return_url with redirect URI."""
    with patch.dict("os.environ", OAUTH_ENV):
        url = build_authorization_url(state="abc123")
    assert "return_url=" in url


def test_build_authorization_url_requests_read_write_scope() -> None:
    """Returned URL requests read and write scope."""
    with patch.dict("os.environ", OAUTH_ENV):
        url = build_authorization_url(state="abc123")
    assert "scope=read" in url
    assert "write" in url


def test_build_authorization_url_uses_token_response_type() -> None:
    """Returned URL uses token response type."""
    with patch.dict("os.environ", OAUTH_ENV):
        url = build_authorization_url(state="abc123")
    assert "response_type=token" in url


def test_build_authorization_url_uses_fragment_callback_method() -> None:
    """Returned URL uses fragment callback method for token delivery."""
    with patch.dict("os.environ", OAUTH_ENV):
        url = build_authorization_url(state="abc123")
    assert "callback_method=fragment" in url


def test_build_authorization_url_sets_30day_expiration() -> None:
    """Returned URL requests a 30-day token expiration."""
    with patch.dict("os.environ", OAUTH_ENV):
        url = build_authorization_url(state="abc123")
    assert "expiration=30days" in url


def test_build_authorization_url_includes_app_name() -> None:
    """Returned URL includes the application name."""
    with patch.dict("os.environ", OAUTH_ENV):
        url = build_authorization_url(state="abc123")
    assert "name=" in url


def test_build_authorization_url_missing_api_key_raises() -> None:
    """Missing TRELLO_API_KEY raises KeyError."""
    with (
        patch.dict("os.environ", {"REDIRECT_URI": FAKE_REDIRECT_URI}, clear=True),
        pytest.raises(KeyError, match="TRELLO_API_KEY"),
    ):
        build_authorization_url(state="abc123")


def test_build_authorization_url_missing_redirect_uri_raises() -> None:
    """Missing REDIRECT_URI raises KeyError."""
    with (
        patch.dict("os.environ", {"TRELLO_API_KEY": FAKE_API_KEY}, clear=True),
        pytest.raises(KeyError, match="REDIRECT_URI"),
    ):
        build_authorization_url(state="abc123")
