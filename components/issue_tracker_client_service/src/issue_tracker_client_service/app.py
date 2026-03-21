"""FastAPI application exposing the issue tracker client over HTTP."""

import os
import secrets
from typing import Annotated

from fastapi import Cookie, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from issue_tracker_client_api.client import Issue
from issue_tracker_client_impl.client import DefaultIssueTrackerClient
from issue_tracker_client_impl.oauth import build_authorization_url

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("ALLOWED_ORIGIN", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        if session is not None:
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
    """Start the Trello authorization flow."""
    try:
        state = create_state()
        auth_url = build_authorization_url(state)
        return RedirectResponse(url=auth_url, status_code=302)
    except KeyError:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to start authorization flow",
        ) from exc


@app.get("/auth/callback")
def auth_callback(
    state: str | None = None,
    error: str | None = None,
) -> HTMLResponse:
    """Serve an HTML page that extracts the Trello token from the URL fragment.

    Trello redirects to ``return_url#token=<value>``. Since the fragment is
    not sent to the server, this endpoint returns a small HTML/JS page that
    reads ``window.location.hash``, extracts the token, and POSTs it to
    ``/auth/token``.
    """
    if error is not None:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")

    if state is None:
        raise HTTPException(status_code=400, detail="Missing state parameter")

    consume_state(state)

    # Return HTML that extracts the token from the fragment and POSTs it
    html = f"""<!DOCTYPE html>
<html>
<head><title>Authenticating...</title></head>
<body>
<p>Completing authentication...</p>
<script>
    const hash = window.location.hash.substring(1);
    const params = new URLSearchParams(hash);
    const token = params.get("token");
    if (token) {{
        fetch("/auth/token", {{
            method: "POST",
            headers: {{"Content-Type": "application/json"}},
            body: JSON.stringify({{token: token, state: "{state}"}})
        }}).then(resp => resp.json()).then(data => {{
            document.body.innerHTML = "<p>Authenticated!</p>";
        }}).catch(err => {{
            document.body.innerHTML = "<p>Error: " + err + "</p>";
        }});
    }} else {{
        document.body.innerHTML = "<p>Error: No token received from Trello.</p>";
    }}
</script>
</body>
</html>"""
    return HTMLResponse(content=html)


@app.post("/auth/token")
def auth_token(
    request_body: dict[str, str],
) -> AuthStatusOut:
    """Receive the Trello token from the client-side callback page."""
    token = request_body.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Missing token")

    session_id = secrets.token_urlsafe(32)
    save_session(session_id, access_token=token, refresh_token=None, expires_at=None)

    return AuthStatusOut(status="authenticated", session_id=session_id)


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
