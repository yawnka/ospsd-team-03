"""FastAPI application exposing the issue tracker client over HTTP."""

import os
import secrets
import time
from typing import Annotated

from fastapi import Cookie, Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from issue_tracker_client_api.client import Issue
from issue_tracker_client_impl.client import DefaultIssueTrackerClient
from issue_tracker_client_impl.oauth import (
    build_authorization_url,
    exchange_code_for_token,
    refresh_access_token,
)

from issue_tracker_client_service.auth import consume_state, create_state
from issue_tracker_client_service.schemas import (
    AddCommentIn,
    AuthStatusOut,
    CommentOut,
    CreateIssueIn,
    HealthOut,
    IssueOut,
)
from issue_tracker_client_service.session import get_session, save_session

app = FastAPI(
    title="Issue Tracker Client Service",
    version="0.1.0",
    description="FastAPI service exposing the issue tracker client implementation.",
)


def _issue_to_out(issue: Issue) -> IssueOut:
    """Convert a domain Issue object into an API response model."""
    return IssueOut(
        id=issue.id,
        title=issue.title,
        body=issue.body,
        state=issue.state.value,
    )


def get_client(
    session_id: str | None = Cookie(default=None),
) -> DefaultIssueTrackerClient:
    """Build a concrete client for the current request."""
    api_key = os.environ["TRELLO_API_KEY"]

    if session_id is not None:
        session = get_session(session_id)
        # check expiration
        if (session is not None and
        time.time() > session.expires_at and
        session.refresh_token is not None
        ):
            new_tokens = refresh_access_token(session.refresh_token)
            new_access_token = str(new_tokens["access_token"])
            expires_in = int(new_tokens.get("expires_in", 3600))
            new_expires_at = time.time() + expires_in

            # update session
            save_session(
                session_id,
                new_access_token,
                session.refresh_token,
                new_expires_at,
            )

            return DefaultIssueTrackerClient(
                api_key=api_key,
                token=new_access_token,
            )
        return DefaultIssueTrackerClient(
            api_key=api_key,
            token=session.access_token,
        )

    token = os.environ["TRELLO_API_TOKEN"]
    return DefaultIssueTrackerClient(api_key=api_key, token=token)


ClientDependency = Annotated[DefaultIssueTrackerClient, Depends(get_client)]


@app.get("/")
def root() -> dict[str, str]:
    """Return a root status message."""
    return {"message": "Issue Tracker Client Service is running"}


@app.get("/health")
def health() -> HealthOut:
    """Return service health status."""
    return HealthOut(status="ok")


@app.get("/auth/login")
def auth_login() -> RedirectResponse:
    """Start the OAuth authorization flow."""
    try:
        state = create_state()
        auth_url = build_authorization_url(state)
        return RedirectResponse(url=auth_url, status_code=302)
    except KeyError:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to start OAuth authorization flow",
        ) from exc

@app.get("/auth/callback")
def auth_callback(
    response: Response,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> AuthStatusOut:
    """Handle the OAuth callback."""
    if error is not None:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")

    if code is None or state is None:
        raise HTTPException(status_code=400, detail="Missing code or state")

    consume_state(state)

    try:
        token_payload = exchange_code_for_token(code)
    except KeyError:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to exchange OAuth code for tokens",
        ) from exc
    access_token = str(token_payload["access_token"])
    refresh_token_raw = token_payload.get("refresh_token")
    refresh_token = None if refresh_token_raw is None else str(refresh_token_raw)
    expires_in = int(token_payload.get("expires_in", 3600)) # token has lifetime of 1 hr
    expires_at = time.time() + expires_in

    session_id = secrets.token_urlsafe(32)
    save_session(session_id, access_token, refresh_token, expires_at)

    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        secure=False,
    )

    return AuthStatusOut(status="authenticated")


@app.get("/boards/{board}/issues")
def list_issues(
    board: str,
    client: ClientDependency,
) -> list[IssueOut]:
    """List issues for a board."""
    try:
        return [_issue_to_out(issue) for issue in client.list_issues(board)]
    except KeyError:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list issues for board '{board}'",
        ) from exc


@app.get("/boards/{board}/issues/{issue_id}")
def get_issue(
    board: str,
    issue_id: int,
    client: ClientDependency,
) -> IssueOut:
    """Fetch a single issue by ID."""
    try:
        issue = client.get_issue(board, issue_id)
    except KeyError:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Failed to fetch issue {issue_id} from board '{board}'",
        ) from exc
    else:
        return _issue_to_out(issue)


@app.post("/boards/{board}/issues")
def create_issue(
    board: str,
    payload: CreateIssueIn,
    client: ClientDependency,
) -> IssueOut:
    """Create a new issue in a board."""
    try:
        issue = client.create_issue(board, payload.title, payload.body)
    except KeyError:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create issue in board '{board}'",
        ) from exc
    else:
        return _issue_to_out(issue)

@app.post("/boards/{board}/issues/{issue_id}/close")
def close_issue(
    board: str,
    issue_id: int,
    client: ClientDependency,
) -> dict[str, bool]:
    """Close an existing issue."""
    try:
        success = client.close_issue(board, issue_id)
    except KeyError:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to close issue {issue_id} in board '{board}'",
        ) from exc
    else:
        return {"success": success}

@app.post("/boards/{board}/issues/{issue_id}/comments")
def add_comment(
    board: str,
    issue_id: int,
    payload: AddCommentIn,
    client: ClientDependency,
) -> CommentOut:
    """Add a comment to an issue."""
    try:
        comment = client.add_comment(board, issue_id, payload.body)
    except KeyError:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add comment to issue {issue_id} in board '{board}'",
        ) from exc
    else:
        return CommentOut(id=comment.id, body=comment.body)

@app.exception_handler(KeyError)
def handle_missing_env(_: Request, exc: KeyError) -> JSONResponse:
    """Return a readable error if a required environment variable is missing."""
    detail = f"Missing required environment variable: {exc.args[0]}"
    return JSONResponse(status_code=500, content={"detail": detail})
