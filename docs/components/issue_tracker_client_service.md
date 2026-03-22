# Issue Tracker Client Service (FastAPI)

## Overview

`issue_tracker_client_service` is the FastAPI-based HTTP service that exposes the issue tracker implementation over REST endpoints. It serves as the main deployment unit.

It provides:

- REST endpoints for all core issue operations (list, get, create, close, comment)
- OAuth 2.0 login/callback flow for Trello authentication
- Session-based multi-user support with in-memory session storage
- Health check endpoint for operational monitoring
- Auto-generated OpenAPI/Swagger documentation

## Architecture

### Dependency Injection

The service builds a `DefaultIssueTrackerClient` per request using FastAPI's `Depends`:

```python
def get_client(session_id: str | None = Cookie(default=None)) -> DefaultIssueTrackerClient:
    # 1. Use session cookie if present (OAuth token)
    # 2. Fall back to environment variables
    ...

ClientDependency = Annotated[DefaultIssueTrackerClient, Depends(get_client)]
```

### Authentication Flow

1. User visits `GET /auth/login`
2. Service redirects to Trello's authorization page
3. User grants access; Trello redirects to `GET /auth/callback`
4. Callback page extracts the token from the URL fragment and POSTs it to `/auth/token`
5. Service creates a session and returns a `session_id`

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Root status message |
| `GET` | `/health` | Health check (returns `{"status": "ok"}`) |
| `GET` | `/auth/login` | Start OAuth flow |
| `GET` | `/auth/callback` | OAuth callback |
| `POST` | `/auth/token` | Receive token from callback page |
| `GET` | `/boards/{board}/issues` | List issues |
| `GET` | `/boards/{board}/issues/{issue_id}` | Get a single issue |
| `POST` | `/boards/{board}/issues` | Create an issue |
| `POST` | `/boards/{board}/issues/{issue_id}/close` | Close an issue |
| `POST` | `/boards/{board}/issues/{issue_id}/comments` | Add a comment |

## Environment Variables

```bash
export TRELLO_API_KEY="your_api_key"
export TRELLO_API_TOKEN="your_api_token"       # fallback when no session
export REDIRECT_URI="http://localhost:8000/auth/callback"
```

## Running Locally

```bash
uv run uvicorn issue_tracker_client_service.app:app --reload
```

Visit `http://localhost:8000/docs` for the Swagger UI.

## Testing

```bash
uv run pytest components/issue_tracker_client_service/tests/ -q
```
