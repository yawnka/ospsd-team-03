"""Google OAuth 2.0 helper functions for the Issue Tracker service."""

import os
from typing import Any
from urllib.parse import urlencode

import requests


def build_authorization_url(state: str) -> str:
    """Build the Google OAuth 2.0 authorization URL."""
    client_id = os.environ["OAUTH_CLIENT_ID"]
    redirect_uri = os.environ["REDIRECT_URI"]

    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }

    return f"{base_url}?{urlencode(params)}"


def exchange_code_for_token(code: str) -> dict[str, Any]:
    """Exchange an authorization code for access and refresh tokens."""
    client_id = os.environ["OAUTH_CLIENT_ID"]
    client_secret = os.environ["OAUTH_CLIENT_SECRET"]
    redirect_uri = os.environ["REDIRECT_URI"]

    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        },
        timeout=10,
    )
    resp.raise_for_status()
    result: dict[str, Any] = resp.json()
    return result


def refresh_access_token(refresh_token: str) -> dict[str, Any]:
    """Refresh an expired access token."""
    client_id = os.environ["OAUTH_CLIENT_ID"]
    client_secret = os.environ["OAUTH_CLIENT_SECRET"]

    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
        },
        timeout=10,
    )
    resp.raise_for_status()
    result: dict[str, Any] = resp.json()
    return result
