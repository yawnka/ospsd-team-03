# HW2 Design Document

## Overview

HW1 established two components: `issue_tracker_client_api` (an abstract interface) and `issue_tracker_client_impl` (a Trello-backed concrete implementation). Both ran locally — consumers imported the library and called Trello directly.

HW2 transforms that library into a publicly accessible microservice. Three new components were added on top of the HW1 foundation without modifying the original interface or implementation:

- **`issue_tracker_client_service`** — exposes the implementation over HTTP (FastAPI, deployed on Render)
- **`issue_tracker_client_service_client`** — a type-safe Python client auto-generated from the service's OpenAPI spec
- **`issue_tracker_client_adapter`** — implements the original `IssueTrackerClient` ABC by delegating to the generated client

The central design goal is **location transparency**: consumer code that works with the local implementation also works identically with the remote adapter, with no changes required.

---

## Architecture

```text
HW1 path (local):
Consumer → get_client() → DefaultIssueTrackerClient → Trello REST API

HW2 path (remote):
Consumer → get_client() → ServiceClientAdapter
                               ↓ HTTP (httpx)
                   issue_tracker_client_service_client
                               ↓ HTTP
                   issue_tracker_client_service (FastAPI, Render)
                               ↓
                   DefaultIssueTrackerClient → Trello REST API
```

In both paths the consumer code is identical:

```python
# Local (HW1)
import issue_tracker_client_impl
from issue_tracker_client_api.client import get_client
client = get_client()  # returns DefaultIssueTrackerClient

# Remote (HW2)
import issue_tracker_client_adapter
from issue_tracker_client_api.client import get_client
client = get_client()  # returns ServiceClientAdapter
```

Only the import changes. The registered DI factory switches transparently.

---

## Component C: `issue_tracker_client_service`

### Responsibility

Deploy `DefaultIssueTrackerClient` as a standalone HTTP service. This is the only component in the system that runs as a separate process (Docker container on Render).

### Module Breakdown

| Module | Role |
|--------|------|
| `app.py` | FastAPI application; defines all routes and the per-request `get_client` dependency |
| `schemas.py` | Pydantic request/response models for the HTTP wire format (separate from domain models) |
| `session.py` | In-memory session store: `dict[str, UserSession]` keyed by `session_id` |
| `auth.py` | One-time CSRF state nonces: `create_state()` / `consume_state()` backed by `set[str]` |

### Authorization Flow

Trello does not implement the standard OAuth 2.0 authorization code flow. Instead it uses a redirect-based token flow where the access token is returned in the **URL fragment** (e.g., `callback#token=<value>`). Because URL fragments are never sent to the server by the browser, the standard server-side code-exchange step is impossible.

The implementation works around this with a JavaScript bridge:

1. `GET /auth/login` — generates a CSRF state nonce, calls `build_authorization_url()` from `issue_tracker_client_impl.oauth`, and redirects the browser to the Trello authorization page (HTTP 302).
2. The user grants access on the Trello site.
3. Trello redirects to `GET /auth/callback?state=<value>#token=<value>`. The `state` query parameter arrives at the server; the `token` in the fragment does not.
4. The callback endpoint validates and consumes the state nonce, then returns an HTML page with inline JavaScript. The script reads `window.location.hash`, extracts the token, and POSTs it to `POST /auth/token`.
5. `POST /auth/token` creates a `UserSession`, stores it in `_SESSIONS`, generates a `session_id` with `secrets.token_urlsafe(32)`, and returns it in the JSON response body (`{"status": "authenticated", "session_id": "..."}`). No `Set-Cookie` header is set by the server.
6. The caller is responsible for storing the `session_id` and sending it as a cookie on subsequent requests. The `get_client` FastAPI dependency reads the `session_id` cookie to look up the user's Trello token.

This deviation from the standard OAuth 2.0 flow was approved by the professor because Trello does not support the OAuth 2.0 authorization code grant.

### Request Authentication

Two authentication modes are supported simultaneously:

- **Session-based**: `session_id` cookie → `get_session()` → per-user Trello token. Used when a user has completed the authorization flow.
- **Environment fallback**: `TRELLO_API_TOKEN` env var used when no valid session cookie is present. Used in CI and for direct service testing without a browser.

### REST Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Root status message |
| `GET` | `/health` | Returns `{"status": "ok"}` — used for deployment health checks |
| `GET` | `/auth/login` | Redirects to Trello authorization page |
| `GET` | `/auth/callback` | Validates state nonce; serves JS bridge page |
| `POST` | `/auth/token` | Receives token from JS bridge; returns `session_id` |
| `GET` | `/boards/{board}/issues` | List all issues for a board |
| `GET` | `/boards/{board}/issues/{issue_id}` | Get a single issue |
| `POST` | `/boards/{board}/issues` | Create a new issue |
| `POST` | `/boards/{board}/issues/{issue_id}/close` | Close an issue |
| `POST` | `/boards/{board}/issues/{issue_id}/comments` | Add a comment |

### Deployment

The service runs as a Docker container on [Render](https://render.com). The `Dockerfile` uses a two-stage build: a builder stage installs dependencies with `uv sync --no-dev --frozen`, and a slim runtime stage copies only the installed packages. This keeps the production image lean.

Every push to the `hw-2` branch triggers a CircleCI pipeline that runs lint, type checks, and tests, then calls the Render deploy hook to redeploy the service. The live URL is `https://ospsd-team-03.onrender.com`.

Required environment variables (set via Render's secrets manager — never committed):

| Variable | Purpose |
|----------|---------|
| `TRELLO_API_KEY` | Trello application key |
| `TRELLO_API_TOKEN` | Fallback Trello token (used when no session exists) |
| `REDIRECT_URI` | OAuth callback URL (differs between local and production) |

---

## Component D: `issue_tracker_client_service_client`

### Responsibility

Provide a type-safe Python library for calling the service over HTTP. The client is auto-generated — not hand-written.

### Generation

FastAPI automatically generates an OpenAPI 3.0 spec from the route definitions and Pydantic schemas in `app.py`. The client is generated from that spec using `openapi-python-client`:

```bash
openapi-python-client generate --url https://ospsd-team-03.onrender.com/openapi.json
```

Because the OpenAPI spec is derived from the same Pydantic schemas used in the service, the generated client models are always in sync with the service wire format. The generated models use `attrs` (not Pydantic), and the package depends on `attrs` and `python-dateutil` rather than `pydantic`.

### Structure

| Path | Contents |
|------|----------|
| `api/default/` | One module per endpoint; each exposes `sync`, `sync_detailed`, `asyncio`, `asyncio_detailed` variants |
| `models/` | `attrs`-based models mirroring the service's `schemas.py` |
| `client.py` | `Client` and `AuthenticatedClient` wrapping `httpx` |

### Why Excluded from Ruff and Mypy

Generated code does not follow hand-written style conventions and would produce hundreds of false-positive violations. The `pyproject.toml` excludes `issue_tracker_client_service_client` from both ruff and mypy. This is standard practice for generated clients (gRPC stubs, OpenAPI clients, etc.). The adapter layer hides all generated code from consumers.

### Testing

This package has no unit tests of its own. It is tested indirectly: adapter unit tests patch the generated endpoint modules to verify delegation.

---

## Component E: `issue_tracker_client_adapter`

### Responsibility

Make the remote service indistinguishable from the local implementation from the consumer's perspective. This is the Adapter Pattern applied to achieve location transparency.

### The Adapter Pattern

`ServiceClientAdapter` implements the `IssueTrackerClient` ABC. Its constructor takes the `base_url` of the deployed service and creates an `AuthenticatedClient`. Each ABC method delegates to the corresponding generated endpoint module:

```python
def list_issues(self, board: str) -> list[Issue]:
    response = list_issues_boards_board_issues_get.sync(board=board, client=self._client)
    return [_to_issue(i) for i in response]
```

The `_to_issue()` helper translates the HTTP wire model (`IssueOut`) into the domain model (`Issue`). This translation layer is necessary because the ABC domain models and the HTTP wire models are intentionally separate packages — the interface (`issue_tracker_client_api`) must not depend on the generated client.

### DI Auto-Registration

`__init__.py` registers the adapter factory at import time, identical to the pattern used by `issue_tracker_client_impl`:

```python
_api.register(
    lambda: ServiceClientAdapter(base_url=os.environ["ISSUE_TRACKER_SERVICE_URL"])
)
```

The `base_url` is read from the environment at instantiation time (not at import time), allowing the env var to be set after import if needed.

---

## Component Dependency Graph

| Component | Depends On |
|-----------|-----------|
| `issue_tracker_client_api` | (none — pure stdlib) |
| `issue_tracker_client_impl` | `issue_tracker_client_api`, `requests` |
| `issue_tracker_client_service` | `issue_tracker_client_impl`, `fastapi`, `uvicorn` |
| `issue_tracker_client_service_client` | `httpx`, `attrs`, `python-dateutil` (generated) |
| `issue_tracker_client_adapter` | `issue_tracker_client_api`, `issue_tracker_client_service_client` |

Note: `issue_tracker_client_adapter` does **not** depend on `issue_tracker_client_service`. The adapter only speaks HTTP to a deployed URL — it has no compile-time knowledge of the service implementation.

---

## Design Decisions

### In-Memory Session Storage

Sessions are stored in a plain `dict[str, UserSession]` in `session.py`. This is intentionally simple — the HW2 spec recommends session tokens over a database. The trade-off is that sessions are lost on service restart. For a production system this would be replaced with Redis or a similar persistent store.

### CSRF State Nonces

`auth.py` maintains a `set[str]` of one-time state tokens. `consume_state()` removes the state after validating it, preventing replay attacks on the OAuth callback. Like sessions, these are in-memory and lost on restart, which would break any authorization flows in progress at the time of a restart — an acceptable trade-off at this scale.

### Generated Client vs. Hand-Written HTTP Client

Auto-generation via `openapi-python-client` was chosen over writing a hand-crafted HTTP client. The benefit is that the client models are always in sync with the service API and require no maintenance. The trade-off is verbose generated code that must be excluded from linting. The adapter layer completely hides this from consumers.

### JavaScript Bridge for Fragment-Based Token

Trello's `callback_method=fragment` places the access token in the URL fragment, which the browser never sends to the server. The service returns an HTML page from `/auth/callback` containing inline JavaScript that reads `window.location.hash` and POSTs the token to `/auth/token`. This is unconventional but correct given the Trello API constraint and was approved by the professor as a deviation from the HW2 OAuth 2.0 requirement.

### CORS Configuration

The service enables CORS via `CORSMiddleware`. The allowed origin is read from the `ALLOWED_ORIGIN` environment variable, defaulting to `"*"` when not set. In production the variable should be set to the known callback origin.

---

## Testing Strategy for HW2 Components

See [Testing Strategy](testing.md) for the full guide. HW2-specific additions:

- **Service unit tests** (`components/issue_tracker_client_service/tests/test_service.py`): Use FastAPI's `TestClient`. `DefaultIssueTrackerClient` is patched via `patch.object` to avoid real Trello calls.
- **Adapter unit tests** (`components/issue_tracker_client_adapter/tests/test_adapter.py`): Generated endpoint modules are patched to verify that each ABC method delegates correctly without making real HTTP calls. Also verifies that importing the package registers the DI factory.
- **Integration tests** (`tests/integration/test_client_integration.py`): Verify that importing `issue_tracker_client_impl` correctly wires the DI registry and that `get_client()` returns a `DefaultIssueTrackerClient`.
- **E2E tests** (`tests/e2e/test_main_application.py`): Exercise `issue_tracker_client_impl` directly against the real Trello API. The service, adapter, and generated client are not exercised in the E2E suite.
- **OAuth flow**: Requires a browser interaction and cannot be fully automated in CI. Tests focus on the post-token logic (session creation, client instantiation). The auth flow is validated manually.
