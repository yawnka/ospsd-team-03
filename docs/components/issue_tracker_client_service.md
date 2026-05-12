# Issue Tracker Client Service FastAPI

## Overview

`issue_tracker_client_service` provides the FastAPI HTTP service for the issue tracker system.

The service exposes board and issue operations over REST, provides Trello authorization endpoints, includes health checks, records telemetry, supports AI-assisted issue workflows, and can notify a Discord channel through the shared Chat API after issue actions.

## Purpose

This component is responsible for:

- exposing issue tracker functionality over HTTP,
- adapting request and response bodies with Pydantic schemas,
- creating request-scoped Trello clients,
- supporting Trello login and callback flows,
- storing authenticated sessions with HTTP-only cookies,
- falling back to environment-based Trello credentials for local and service usage,
- exposing AI-assisted workflows through `/ai/chat`,
- executing AI tool calls against the issue tracker client,
- sending Discord notifications for issue actions when configured,
- exposing health and OpenAPI documentation endpoints,
- recording request telemetry for latency, success, and failure monitoring.

## Architecture

### FastAPI Application

The service is defined in:

```text
components/issue_tracker_client_service/src/issue_tracker_client_service/app.py
```

The application wires together:
- FastAPI route handlers,
- Trello client construction,
- session-based authentication,
- AI client registration,
- Chat provider registration,
- telemetry middleware,
- Pydantic schemas.

### Startup Behavior
On startup, the service validates required environment variables, registers the AI client implementation, and registers the configured Chat provider.

Required startup variables include:

```bash
TRELLO_API_KEY
TRELLO_API_TOKEN
OPENAI_API_KEY
```

Discord variables are required only when Chat notifications are enabled.

### Dependency Injection

The service builds an issue tracker client per request using FastAPI dependencies.

```python
def get_client(session_id: str | None = Cookie(default=None)) -> SharedClient:
    ...
```

### Client Construction

The client is created using:

1. Session cookie (preferred)  
    Uses the `session_id` cookie to retrieve the user's stored Trello access token.

2. Environment variables (fallback)  
   Uses Trello API credentials for local/testing usage.

This lets the service support both browser-authorized users and non-interactive deployed usage.

### Authentication

The service supports a Trello redirect-based authentication flow.


Auth Endpoints:
- `GET /auth/login`
- `GET /auth/callback`
- `POST /auth/token`

Flow:
1. User visits `/auth/login`
2. Service redirects to Trello authorization page
3. User authorizes the app
4. Trello redirects to `/auth/callback` with the token in the URL fragment
5. A browser bridge extracts the token and sends it to `/auth/token`
6. The service:
   - creates a session
   - stores the Trello access token in memory
   - sets an HTTP-only `session_id` cookie

Future requests can authenticate through the `session_id` cookie. For local development, CI, and deployment, the service can also use environment-based Trello credentials.

### Session Model

Sessions are stored in memory.

```python
@dataclass
class UserSession:
    access_token: str
    refresh_token: str | None
    expires_at: float | None
```
This service does not require a database for sessions.

## Environment Variables

### Required

```bash
export TRELLO_API_KEY="your_trello_api_key"
export TRELLO_API_TOKEN="your_trello_api_token"
export OPENAI_API_KEY="your_openai_api_key"
```
### Optional / Feature-Specific

```bash
export REDIRECT_URI="http://localhost:8000/auth/callback"
export ALLOWED_ORIGIN="http://localhost:3000"
export ENV="production"

export CHAT_CLIENT_IMPL_MODULE="discord_client_impl"
export DISCORD_BOT_TOKEN="your_discord_bot_token"
export DISCORD_GUILD_ID="your_discord_server_id"
export DISCORD_NOTIFY_CHANNEL_ID="your_sandbox_channel_id"
```
| Variable                    | Purpose                                             |
| --------------------------- | --------------------------------------------------- |
| `TRELLO_API_KEY`            | Trello API key                                      |
| `TRELLO_API_TOKEN`          | Trello API token used as fallback credentials       |
| `OPENAI_API_KEY`            | API key for the AI client implementation            |
| `REDIRECT_URI`              | Trello callback URL                                 |
| `ALLOWED_ORIGIN`            | Optional CORS origin                                |
| `ENV`                       | Used to determine production cookie settings        |
| `CHAT_CLIENT_IMPL_MODULE`   | Chat provider module, usually `discord_client_impl` |
| `DISCORD_BOT_TOKEN`         | Discord bot token                                   |
| `DISCORD_GUILD_ID`          | Discord server ID                                   |
| `DISCORD_NOTIFY_CHANNEL_ID` | Discord channel used for notifications              |


## API Reference

### General
- `GET /`
- `GET /health`

### Auth
- `GET /auth/login`
- `GET /auth/callback`
- `POST /auth/token`

### Boards
- `GET /boards`
- `GET /boards/{board_id}`
- `POST /boards`
- `PATCH /boards/{board_id}`
- `DELETE /boards/{board_id}`

### Issues
- `GET /boards/{board_id}/issues`
- `GET /issues/{issue_id}`
- `POST /boards/{board_id}/issues`
- `PATCH /issues/{issue_id}`
- `DELETE /issues/{issue_id}`

### AI
- `POST /ai/chat`


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
Open the local API docs at [http://localhost:8000/docs](http://localhost:8000/docs).

### Health Check
```bash
curl http://localhost:8000/health
```
Expected response:

```json
{
  "status": "ok"
}
```

## Example Requests

### List Boards

```bash
curl http://localhost:8000/boards
```

### Get a Board

```bash
curl http://localhost:8000/boards/<board_id>
```

### Create a Board

```bash
curl -X POST "http://localhost:8000/boards" \
  -H "Content-Type: application/json" \
  -d '{"name":"Demo Board"}'
```

### Update a Board

```bash
curl -X PATCH "http://localhost:8000/boards/<board_id>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Updated Board Name"}'
```

### Delete a Board

```bash
curl -X DELETE "http://localhost:8000/boards/<board_id>"
```

### List Issues on a Board

```bash
curl http://localhost:8000/boards/<board_id>/issues
```

### Get an Issue

```bash
curl http://localhost:8000/issues/<issue_id>
```

### Create an Issue

```bash
curl -X POST "http://localhost:8000/boards/<board_id>/issues" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "New issue",
    "description": "Created via API",
    "status": "to_do"
  }'
```
### Update an Issue

```bash
curl -X PATCH "http://localhost:8000/issues/<issue_id>" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress"
  }'
```

### Delete an Issue

```bash
curl -X DELETE "http://localhost:8000/issues/<issue_id>"
```

### AI Chat

```bash
curl -X POST "http://localhost:8000/ai/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create an issue on my demo board called Fix login bug"
  }'
```
The AI endpoint can execute tool calls against the issue tracker client. When configured, successful AI tool execution also sends a Discord notification through the shared Chat API.

## AI Tool Calling

The service uses `issue_tracker_client_service.ai_router.run_ai_chat()` to run the AI workflow.

The AI flow is:

1. Receive a user message at `/ai/chat`.
2. Call the registered AI client with available tool definitions.
3. Execute requested tools through the issue tracker client.
4. Record executed actions in the response.
5. Notify Discord when a tool action succeeds.
6. Return the final AI reply and action list.

This keeps the AI provider, issue tracker provider, and Chat provider behind explicit interfaces.

## Discord Notifications

The service can send notifications through the shared Chat API when `DISCORD_NOTIFY_CHANNEL_ID` is configured.

Notifications are sent for:
- issue creation through the REST API,
- AI tool execution,
- final AI responses.

The Chat provider is configured through:
```bash
export CHAT_CLIENT_IMPL_MODULE="discord_client_impl"
export DISCORD_NOTIFY_CHANNEL_ID="your_sandbox_channel_id"
```
The Discord implementation also requires its own provider credentials.

## Telemetry

The service calls `setup_telemetry(app)` during application setup.

Telemetry is used to monitor:
- request latency,
- successful requests,
- failed requests,
- route labels,
- method labels,
- status labels.

The deployed service sends telemetry to the configured monitoring backend and dashboard.

## Testing

Run service tests:

```bash
uv run pytest components/issue_tracker_client_service/tests --no-cov
```

Run full suite:

```bash
uv run pytest
```

## Notes

- `GET /health` is required for deployment health checks.
- Browser URL bars only issue GET requests; use Swagger UI or `curl` for POST, PATCH, and DELETE requests.
- The service falls back to environment credentials when no session cookie exists.
- Session storage is in memory and is suitable for this project scope, but not durable across restarts.
- Provider secrets must be supplied through environment variables or platform secret configuration.
