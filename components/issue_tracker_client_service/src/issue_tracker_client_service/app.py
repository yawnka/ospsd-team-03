"""FastAPI application exposing the issue tracker client over HTTP."""

import logging
import os
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, cast

from api.board import Board as SharedBoard  # type: ignore[import-untyped]
from api.client import Client as SharedClient  # type: ignore[import-untyped]
from api.issue import Issue as SharedIssue  # type: ignore[import-untyped]
from api.issue import Status as SharedStatus
from discord_client_impl.client import DiscordClient
from fastapi import Cookie, Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from issue_tracker_client_api.client import (
    Board as LocalBoard,
)
from issue_tracker_client_api.client import (
    BoardNotFoundError,
    IssueCreateError,
    IssueNotFoundError,
)
from issue_tracker_client_api.client import (
    Issue as LocalIssue,
)
from issue_tracker_client_api.client import (
    Status as LocalStatus,
)
from issue_tracker_client_impl.client import DefaultIssueTrackerClient
from issue_tracker_client_impl.oauth import build_authorization_url

from issue_tracker_client_service.ai_router import run_ai_chat
from issue_tracker_client_service.ai_schemas import AIChatIn, AIChatOut
from issue_tracker_client_service.auth import consume_state, create_state
from issue_tracker_client_service.schemas import (
    AuthStatusOut,
    BoardOut,
    CreateBoardIn,
    CreateIssueIn,
    HealthOut,
    IssueOut,
    SuccessOut,
    TokenIn,
    UpdateBoardIn,
    UpdateIssueIn,
)
from issue_tracker_client_service.session import get_session, save_session
from issue_tracker_client_service.telemetry import setup_telemetry

REQUIRED_ENV_VARS = (
    "TRELLO_API_KEY",
    "TRELLO_API_TOKEN",
    "OPENAI_API_KEY",
)

def _register_ai_client() -> None:
    """Ensure AI client implementation is registered."""
    import ai_client_impl  # noqa: F401, PLC0415
logger = logging.getLogger(__name__)


def _require_env(var_name: str) -> str:
    """Return a required environment variable or raise a startup error."""
    value = os.getenv(var_name)
    if not value:
        raise HTTPException(
            status_code=500,
            detail=f"Missing required environment variable: {var_name}",
        )
    return value


def _validate_required_env() -> None:
    """Fail fast at startup if required environment variables are missing."""
    for var_name in REQUIRED_ENV_VARS:
        _require_env(var_name)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Validate service configuration before accepting requests."""
    _validate_required_env()
    _register_ai_client()
    yield


app = FastAPI(
    title="Issue Tracker Client Service",
    version="0.1.0",
    description="FastAPI service exposing the issue tracker client implementation.",
    lifespan=lifespan,
)
setup_telemetry(app)

_cors_origin = os.environ.get("ALLOWED_ORIGIN")
# allow_credentials=True is invalid with allow_origins=["*"].
# Use explicit origin + credentials when ALLOWED_ORIGIN is set;
# fall back to "*" without credentials otherwise.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[_cors_origin] if _cors_origin else ["*"],
    allow_credentials=_cors_origin is not None,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _coerce_status(status: SharedStatus | LocalStatus | str) -> SharedStatus:
    """Normalize the remaining local/shared status variants to SharedStatus."""
    if isinstance(status, SharedStatus):
        return status
    if isinstance(status, LocalStatus):
        return SharedStatus(status.value)
    return SharedStatus(status)


def _board_to_out(board: SharedBoard | LocalBoard) -> BoardOut:
    """Convert a shared board object into an API response model."""
    if isinstance(board, LocalBoard):
        return BoardOut(id=board.id, board_name=board.name)
    return BoardOut(id=board.id, board_name=board.board_name)


def _issue_to_out(issue: SharedIssue | LocalIssue) -> IssueOut:
    """Convert a shared issue object into an API response model."""
    return IssueOut(
        id=issue.id,
        title=issue.title,
        desc=issue.desc,
        members=issue.members,
        due_date=issue.due_date,
        status=_coerce_status(issue.status),
        board_id=issue.board_id,
    )


def get_client(
    session_id: str | None = Cookie(default=None),
) -> SharedClient:
    """Build a concrete client for the current request."""
    api_key = _require_env("TRELLO_API_KEY")

    if session_id is not None:
        session = get_session(session_id)
        if session is not None:
            return cast(
                "SharedClient",
                DefaultIssueTrackerClient(
                    api_key=api_key,
                    token=session.access_token,
                ),
            )

    token = _require_env("TRELLO_API_TOKEN")
    return cast(
        "SharedClient",
        DefaultIssueTrackerClient(api_key=api_key, token=token),
    )


ClientDependency = Annotated[SharedClient, Depends(get_client)]


def _get_discord_client() -> DiscordClient | None:
    """Return a DiscordClient if credentials are configured, else None."""
    if not os.getenv("DISCORD_BOT_TOKEN") or not os.getenv("DISCORD_GUILD_ID"):
        return None
    return DiscordClient()


def _notify_discord(issue: IssueOut) -> None:
    """Send a Discord notification for a newly created issue. Never raises."""
    channel_id = os.getenv("DISCORD_NOTIFY_CHANNEL_ID")
    if not channel_id:
        return
    discord = _get_discord_client()
    if discord is None:
        return
    try:
        text = (
            f'New issue created: "{issue.title}" '
            f"(board: {issue.board_id}, status: {issue.status})"
        )
        discord.send_message(channel_id, text)
    except Exception:
        logger.exception("Discord notification failed — issue creation unaffected")


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

    except ValueError as exc:
        # Expected error: invalid state generation or malformed URL
        raise HTTPException(
            status_code=400,
            detail="Invalid authorization request",
        ) from exc

    except Exception as exc:
        # Unexpected failure (e.g., env/config issue)
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

    # Return HTML that extracts the token from the fragment and POSTs it.
    # The fragment (#token=...) is never sent to the server by the browser,
    # so we use a JS bridge to read it from window.location.hash and POST it.
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
            if (data.session_id) {{
                document.body.innerHTML =
                    "<h3>Authenticated!</h3>" +
                    "<p>Copy your <strong>session_id</strong> for API requests:</p>" +
                    "<code style='background:#f0f0f0;padding:8px 12px;display:block;" +
                    "word-break:break-all;border-radius:4px;font-size:14px'>" +
                    data.session_id + "</code>" +
                    "<p style='color:#555;font-size:13px'>In Swagger UI: click " +
                    "<strong>Authorize</strong>, or send it as the " +
                    "<strong>session_id</strong> cookie on your requests.</p>";
            }} else {{
                document.body.innerHTML = "<p>Authenticated!</p>";
            }}
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
def auth_token(request_body: TokenIn, response: Response) -> AuthStatusOut:
    """Receive the Trello token posted by the callback page's JS bridge.

    This endpoint is called automatically by the JavaScript returned from
    ``/auth/callback`` — it is not intended to be invoked directly.
    """
    session_id = secrets.token_urlsafe(32)
    save_session(
        session_id,
        access_token=request_body.token,
        refresh_token=None,
        expires_at=None,
    )
    # Set Secure=True only in production (HTTPS). Browsers will not send Secure cookies
    # over HTTP, so this must be False for local development (e.g., localhost).
    secure = os.getenv("ENV") == "production"

    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        secure=secure,
        path="/",
    )
    return AuthStatusOut(status="authenticated", session_id=session_id)


@app.get("/boards")
def get_boards(client: ClientDependency) -> list[BoardOut]:
    """List boards using the shared API contract."""
    try:
        boards = client.get_boards()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to list boards",
        ) from exc
    else:
        return [_board_to_out(board) for board in boards]


@app.get("/boards/{board_id}")
def get_board(
    board_id: str,
    client: ClientDependency,
) -> BoardOut:
    """Fetch a single board using the shared API contract."""
    try:
        board = client.get_board(board_id)
    except BoardNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Board {board_id} not found",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch board '{board_id}'",
        ) from exc
    else:
        return _board_to_out(board)


@app.post("/boards")
def create_board(
    payload: CreateBoardIn,
    client: ClientDependency,
) -> BoardOut:
    """Create a board using the shared API contract."""
    try:
        board = client.create_board(payload.name)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create board '{payload.name}'",
        ) from exc
    else:
        return _board_to_out(board)


@app.patch("/boards/{board_id}")
def update_board(
    board_id: str,
    payload: UpdateBoardIn,
    client: ClientDependency,
) -> BoardOut:
    """Update a board using the shared API contract."""
    try:
        board = client.update_board(board_id, name=payload.name)
    except BoardNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Board {board_id} not found",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update board '{board_id}'",
        ) from exc
    else:
        return _board_to_out(board)


@app.delete("/boards/{board_id}")
def delete_board(
    board_id: str,
    client: ClientDependency,
) -> SuccessOut:
    """Delete a board using the shared API contract."""
    try:
        success = client.delete_board(board_id)
    except BoardNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Board {board_id} not found",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete board '{board_id}'",
        ) from exc
    else:
        return SuccessOut(success=success)


@app.get("/boards/{board_id}/issues")
def get_issues(
    board_id: str,
    client: ClientDependency,
) -> list[IssueOut]:
    """List issues for a board using the shared API contract."""
    try:
        issues = client.get_issues(board_id)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list issues for board '{board_id}'",
        ) from exc
    else:
        return [_issue_to_out(issue) for issue in issues]


@app.get("/issues/{issue_id}")
def get_issue(
    issue_id: str,
    client: ClientDependency,
) -> IssueOut:
    """Fetch a single issue using the shared API contract."""
    try:
        issue = client.get_issue(issue_id)
    except IssueNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Issue {issue_id} not found",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch issue '{issue_id}'",
        ) from exc
    else:
        return _issue_to_out(issue)


@app.post("/boards/{board_id}/issues")
def create_issue(
    board_id: str,
    payload: CreateIssueIn,
    client: ClientDependency,
) -> IssueOut:
    """Create an issue using the shared API contract."""
    try:
        issue = client.create_issue(
            title=payload.title,
            board_id=board_id,
            desc=payload.desc,
            members=payload.members,
            due_date=payload.due_date,
            status=payload.status,
        )
    except IssueCreateError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create issue in board '{board_id}'",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create issue in board '{board_id}'",
        ) from exc
    else:
        out = _issue_to_out(issue)
        _notify_discord(out)
        return out


@app.patch("/issues/{issue_id}")
def update_issue(
    issue_id: str,
    payload: UpdateIssueIn,
    client: ClientDependency,
) -> IssueOut:
    """Update an issue using the shared API contract."""
    try:
        issue = client.update_issue(
            issue_id=issue_id,
            title=payload.title,
            desc=payload.desc,
            members=payload.members,
            due_date=payload.due_date,
            status=payload.status,
            board_id=payload.board_id,
        )
    except IssueNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Issue {issue_id} not found",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update issue '{issue_id}'",
        ) from exc
    else:
        return _issue_to_out(issue)


@app.delete("/issues/{issue_id}")
def delete_issue(
    issue_id: str,
    client: ClientDependency,
) -> SuccessOut:
    """Delete an issue using the shared API contract."""
    try:
        success = client.delete_issue(issue_id)
    except IssueNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Issue {issue_id} not found",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete issue '{issue_id}'",
        ) from exc
    else:
        return SuccessOut(success=success)

@app.post("/ai/chat")
def ai_chat(payload: AIChatIn,  client: ClientDependency) -> AIChatOut:
    """Handle AI chat requests for the issue tracker."""
    return run_ai_chat(payload=payload, issue_tracker_client=client)


