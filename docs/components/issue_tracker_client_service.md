# Issue Tracker Client Service (FastAPI)

## Overview
`issue_tracker_client_service` provides a FastAPI-based HTTP service for the issue tracker system. It wraps the concrete issue tracker implementation, exposes issue operations as REST endpoints, includes a health-check endpoint, and supports Trello's redirect-based authorization login/callback flows at the service layer.

## Purpose

This package serves as the web service layer for the Issue Tracker abstraction:

- FastAPI Service Layer: Exposes issue tracker functionality over HTTP
- REST API Endpoints: Supports listing, retrieving, creating, closing, and commenting on issues
- Trello Authorization Flow: Provides login and callback endpoints for browser-based Trello authentication
- Session-Based Authentication: Stores authenticated sessions in an in-memory session store
- Automatic Token Refresh: Refreshes expired access tokens (not yet implemented)
- Dependency Injection: Uses a request-scoped client dependency
- OpenAPI Documentation: Automatically generates Swagger/OpenAPI docs
- Multi-User Support: Enables per-user authentication using Trello authorization sessions


## Architecture

### Dependency Injection

The service builds a client per request using FastAPI dependencies:

```python
def get_client(...) -> DefaultIssueTrackerClient:
    ...

ClientDependency = Annotated[DefaultIssueTrackerClient, Depends(get_client)]
```

### Client Construction

The client is created using:

1. Session cookie (preferred)  
    Uses the `session_id` cookie to retrieve the user's stored Trello access token.

2. Environment variables (fallback)  
   Uses Trello API credentials for local/testing usage.

### Authentication

The service uses a session-based authentication flow.

Endpoints:
- `GET /auth/login`
- `GET /auth/callback`
- `POST /auth/token`

Flow:
1. User hits `/auth/login`
2. Service redirects to Trello authorization page
3. User authorizes the app
4. Trello redirects to `/auth/callback` with the token in the URL fragment
5. A browser bridge extracts the token and sends it to `/auth/token`
6. The service:
   - creates a session
   - stores the Trello access token in memory
   - sets an HTTP-only `session_id` cookie

All future requests are authenticated via this cookie. The browser automatically includes it on every request.

No bearer tokens or `Authorization` headers are used.

### Session Model
```python
@dataclass
class UserSession:
    access_token: str
    refresh_token: str | None
    expires_at: float | None
```

- No database needed (in-memory store)
- Falls back to env vars if no session

## Environment Variables
```bash
export REDIRECT_URI="http://localhost:8000/auth/callback"
export TRELLO_API_KEY="your_api_key"
export TRELLO_API_TOKEN="your_api_token"
```

## API Reference

### General
- `GET /`
- `GET /health`

### Auth
- `GET /auth/login`
- `GET /auth/callback`
- `POST /auth/token`

### Issues
- `GET /boards/{board}/issues`
- `GET /boards/{board}/issues/{issue_id}`
- `POST /boards/{board}/issues`
- `POST /boards/{board}/issues/{issue_id}/close`
- `POST /boards/{board}/issues/{issue_id}/comments`

## Usage

### Run the Service

```bash
uv run uvicorn issue_tracker_client_service.app:app --reload
```

### Load .env
```bash
set -a && source .env && set +a
```

### Swagger UI
```bash
http://localhost:8000/docs
```

## Example Requests

### Health
```bash
curl http://localhost:8000/health
```

### List Issues
```bash
curl http://localhost:8000/boards/<board_id>/issues
```

### Create Issue
```bash
curl -X POST "http://localhost:8000/boards/<board_id>/issues" \
  -H "Content-Type: application/json" \
  -d '{"title":"New issue","body":"Created via API"}'
```

### Close Issue
```bash
curl -X POST "http://localhost:8000/boards/<board_id>/issues/1/close"
```

### Add Comment
```bash
curl -X POST "http://localhost:8000/boards/<board_id>/issues/1/comments" \
  -H "Content-Type: application/json" \
  -d '{"body":"Test comment"}'
```

## Testing

Run service tests:

``` bash
uv run pytest components/issue_tracker_client_service/tests --no-cov
```

Run full suite:
``` bash
uv run pytest
```

## AI Chat Endpoint (HW3 Second Submission)

The service exposes an AI chat endpoint that accepts natural-language requests and executes domain actions via tool calling:

```
POST /ai/chat
Content-Type: application/json

{"message": "Create an issue titled 'Fix login bug' on board abc123"}
```

Response:
```json
{
  "reply": "Created issue 'Fix login bug' on board abc123.",
  "actions": [{"tool": "create_issue", "detail": "Created: Fix login bug"}]
}
```

The endpoint is handled by `ai_router.run_ai_chat()`, which runs a multi-turn OpenAI tool-calling loop. Up to 10 domain tools are available (see [AI Client Implementation](ai_client_impl.md)).

## Discord Notification (HW3 Second Submission)

When an issue is created via `POST /boards/{board_id}/issues`, the service sends a Discord notification if the following environment variables are set:

| Variable | Purpose |
|----------|---------|
| `DISCORD_BOT_TOKEN` | Discord bot token |
| `DISCORD_GUILD_ID` | Discord server ID |
| `DISCORD_NOTIFY_CHANNEL_ID` | Channel to post notifications |

Discord failures are caught and logged — they never block issue creation.

## Notes

- `GET /health` is required for Cloud Run startup probes and CI health checks
- Browser URL bar only supports GET — use Swagger UI (`/docs`) or curl for POST
- Falls back to environment credentials (`TRELLO_API_KEY` / `TRELLO_API_TOKEN`) if no session exists
- Telemetry is a no-op when `OTEL_EXPORTER_OTLP_ENDPOINT` is unset (local development)
