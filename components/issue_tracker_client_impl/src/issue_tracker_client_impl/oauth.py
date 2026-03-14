"""Trello OAuth helper functions for the Issue Tracker service.

Trello uses a redirect-based authorization flow where the user visits a Trello
URL, grants permission, and is redirected back with a token in the URL fragment.
The service then receives the token via a client-side redirect to the callback.

See: https://developer.atlassian.com/cloud/trello/guides/rest-api/authorization/
"""

import os
from urllib.parse import urlencode

TRELLO_AUTHORIZE_URL = "https://trello.com/1/authorize"


def build_authorization_url(state: str) -> str:
    """Build the Trello authorization URL.

    Redirects the user to Trello's consent screen. After granting access,
    Trello redirects to ``REDIRECT_URI`` with the token in the URL fragment.
    """
    api_key = os.environ["TRELLO_API_KEY"]
    redirect_uri = os.environ["REDIRECT_URI"]

    params = {
        "expiration": "30days",
        "name": "Issue Tracker Service",
        "scope": "read,write",
        "response_type": "token",
        "key": api_key,
        "callback_method": "fragment",
        "return_url": redirect_uri + f"?state={state}",
    }

    return f"{TRELLO_AUTHORIZE_URL}?{urlencode(params)}"
