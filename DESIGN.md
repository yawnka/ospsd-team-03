# Design Document

## Overview

HW1 established two components: `issue_tracker_client_api` (an abstract interface) and `issue_tracker_client_impl` (a Trello-backed concrete implementation). Both ran locally — consumers imported the library and called Trello directly.

HW2 transforms that library into a publicly accessible microservice. Three new components were added on top of the HW1 foundation without modifying the original interface or implementation:

- **`issue_tracker_client_service`** — exposes the implementation over HTTP (FastAPI, deployed on GCP Cloud Run)
- **`issue_tracker_client_service_client`** — a type-safe Python client auto-generated from the service's OpenAPI spec
- **`issue_tracker_client_adapter`** — implements the original `IssueTrackerClient` ABC by delegating to the generated client

The central design goal is **location transparency**: consumer code that works with the local implementation also works identically with the remote adapter, with no changes required.

HW3 adds infrastructure as code (Terraform), observability (OpenTelemetry + Grafana Cloud), and a fully automated CI/CD pipeline that builds, deploys, and verifies the service on every push.

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
                   issue_tracker_client_service (FastAPI, GCP Cloud Run)
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

Deploy `DefaultIssueTrackerClient` as a standalone HTTP service. This is the only component in the system that runs as a separate process (Docker container on GCP Cloud Run).

### Module Breakdown

| Module | Role |
|--------|------|
| `app.py` | FastAPI application; defines all routes and the per-request `get_client` dependency |
| `schemas.py` | Pydantic request/response models for the HTTP wire format (separate from domain models) |
| `session.py` | In-memory session store: `dict[str, UserSession]` keyed by `session_id` |
| `auth.py` | One-time CSRF state nonces: `create_state()` / `consume_state()` backed by `set[str]` |
| `telemetry.py` | OpenTelemetry instrumentation: tracing, metrics, and FastAPI auto-instrumentation (no-op when `OTEL_EXPORTER_OTLP_ENDPOINT` is unset) |

### Authorization Flow

Trello does not implement the standard OAuth 2.0 authorization code flow. Instead it uses a redirect-based token flow where the access token is returned in the **URL fragment** (e.g., `callback#token=<value>`). Because URL fragments are never sent to the server by the browser, the standard server-side code-exchange step is impossible.

The implementation works around this with a JavaScript bridge:

1. `GET /auth/login` — generates a CSRF state nonce, calls `build_authorization_url()` from `issue_tracker_client_impl.oauth`, and redirects the browser to the Trello authorization page (HTTP 302).
2. The user grants access on the Trello site.
3. Trello redirects to `GET /auth/callback?state=<value>#token=<value>`. The `state` query parameter arrives at the server; the `token` in the fragment does not.
4. The callback endpoint validates and consumes the state nonce, then returns an HTML page with inline JavaScript. The script reads `window.location.hash`, extracts the token, and POSTs it to `POST /auth/token`.
5. `POST /auth/token` creates a `UserSession`, stores it in `_SESSIONS`, generates a `session_id` with `secrets.token_urlsafe(32)`, and sets an HTTP-only cookie on the response:

   `Set-Cookie: session_id=...; HttpOnly; SameSite=Lax`

   The response also includes the `session_id` in the JSON body (`{"status": "authenticated", "session_id": "..."}`), but the cookie is the primary authentication mechanism.

6. The browser automatically stores the cookie and includes it on subsequent requests. The `get_client` FastAPI dependency reads the `session_id` cookie to look up the user's Trello token.

The cookie uses `Secure=True` in production so it is only sent over HTTPS, and `Secure=False` in local development so authentication still works over `http://localhost`.

This deviation from the standard OAuth 2.0 flow was approved by the professor because Trello does not support the OAuth 2.0 authorization code grant.

### Request Authentication

The primary authentication mechanism is session-based:

- **Session-based**: `session_id` cookie → `get_session()` → per-user Trello token

This is the intended authentication flow for normal service usage.

A fallback using `TRELLO_API_TOKEN` and `TRELLO_API_KEY` exists for CI and non-browser testing, but it is secondary to the cookie-based session flow.

### REST Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Root status message |
| `GET` | `/health` | Returns `{"status": "ok"}` — used for deployment health checks |
| `GET` | `/auth/login` | Redirects to Trello authorization page |
| `GET` | `/auth/callback` | Validates state nonce; serves JS bridge page |
| `POST` | `/auth/token` | Receives token from JS bridge; creates a session; sets the `session_id` cookie |
| `GET` | `/boards/{board}/issues` | List all issues for a board |
| `GET` | `/boards/{board}/issues/{issue_id}` | Get a single issue |
| `POST` | `/boards/{board}/issues` | Create a new issue |
| `POST` | `/boards/{board}/issues/{issue_id}/close` | Close an issue |
| `POST` | `/boards/{board}/issues/{issue_id}/comments` | Add a comment |

### Deployment

The service runs as a Docker container on GCP Cloud Run. The `Dockerfile` uses a two-stage build: a builder stage installs dependencies with `uv sync --no-dev --frozen`, and a slim runtime stage copies only the installed packages. This keeps the production image lean.

All infrastructure is managed by Terraform (see [Infrastructure as Code](#infrastructure-as-code-terraform) below). Every push to the `hw-3` branch triggers a CircleCI pipeline that builds the Docker image, pushes it to Artifact Registry, runs `terraform plan` and `terraform apply`, then verifies the deployment via a health check.

Required environment variables (sensitive values stored in GCP Secret Manager — never committed):

| Variable | Purpose | Source |
|----------|---------|--------|
| `TRELLO_API_KEY` | Trello application key | Secret Manager |
| `TRELLO_API_TOKEN` | Fallback Trello token (used when no session exists) | Secret Manager |
| `REDIRECT_URI` | OAuth callback URL (differs between local and production) | Terraform variable |
| `ENV` | Set to `production` for Secure cookies | Terraform (hardcoded) |
| `ALLOWED_ORIGIN` | CORS origin (optional) | Terraform variable |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Grafana Cloud OTLP endpoint (optional; empty = telemetry disabled) | Terraform variable |
| `OTEL_EXPORTER_OTLP_HEADERS` | Grafana Cloud authentication header | Secret Manager |
| `OTEL_SERVICE_NAME` | OpenTelemetry service name | Terraform variable |

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
| `client.py` | Generated client helpers wrapping `httpx`; the adapter uses `Client` with cookie-based session auth |

### Why Excluded from Ruff and Mypy

Generated code does not follow hand-written style conventions and would produce hundreds of false-positive violations. The `pyproject.toml` excludes `issue_tracker_client_service_client` from both ruff and mypy. This is standard practice for generated clients (gRPC stubs, OpenAPI clients, etc.). The adapter layer hides all generated code from consumers.

### Testing

This package has no unit tests of its own. It is tested indirectly: adapter unit tests patch the generated endpoint modules to verify delegation.

---

## Component E: `issue_tracker_client_adapter`

### Responsibility

Make the remote service indistinguishable from the local implementation from the consumer's perspective. This is the Adapter Pattern applied to achieve location transparency.

### The Adapter Pattern

`ServiceClientAdapter` implements the `IssueTrackerClient` ABC. Its constructor takes the `base_url` of the deployed service and creates a generated `Client`. Authentication is handled with the `session_id` cookie rather than bearer tokens or `Authorization` headers. Each ABC method delegates to the corresponding generated endpoint module:

```python
def list_issues(self, board: str) -> list[Issue]:
    response = list_issues_boards_board_issues_get.sync(board=board, client=self._client)
    return [_to_issue(i) for i in response]
```

The `_to_issue()` helper translates the HTTP wire model (`IssueOut`) into the domain model (`Issue`). This translation layer is necessary because the ABC domain models and the HTTP wire models are intentionally separate packages — the interface (`issue_tracker_client_api`) must not depend on the generated client.

The adapter is responsible for configuring the generated client so authenticated requests include the `session_id` cookie, allowing the service to resolve the user session.

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
| `issue_tracker_client_service` | `issue_tracker_client_impl`, `fastapi`, `uvicorn`, `opentelemetry-*` |
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
- **E2E tests** (`tests/e2e/test_main_application.py`): Exercise user-visible behavior through the client interface. Service and adapter behavior is additionally covered through HTTP-path integration tests.
- **OAuth flow**: Requires a browser interaction and cannot be fully automated in CI. Tests focus on the post-token logic (session creation, client instantiation). The auth flow is validated manually.
- **Telemetry unit tests** (`components/issue_tracker_client_service/tests/test_telemetry.py`): Verify that `setup_telemetry` is a no-op when `OTEL_EXPORTER_OTLP_ENDPOINT` is unset, configures providers correctly when set, parses OTLP headers, and handles edge cases (trailing slashes, URL-encoded values).

---

## Infrastructure as Code (Terraform)

All cloud resources are defined in `infrastructure/terraform/` and managed exclusively through Terraform. No manual `gcloud` commands are used for resource provisioning.

### Resources Managed

| Resource | Terraform Resource Type | Purpose |
|----------|------------------------|---------|
| Artifact Registry | `google_artifact_registry_repository` | Docker image storage |
| Secret Manager secrets | `google_secret_manager_secret` (x3) | Trello API key, Trello API token, OTLP headers |
| Service account | `google_service_account` | Cloud Run runtime identity |
| Secret IAM bindings | `google_secret_manager_secret_iam_member` (x3) | Grant SA access to secrets |
| Cloud Run service | `google_cloud_run_v2_service` | Application container |
| Public access | `google_cloud_run_v2_service_iam_member` | Allow unauthenticated invocations |

### State Management

Terraform state is stored in a GCS bucket (`ospsd-team-03-tfstate`), enabling shared state across local development and CI without committing sensitive state files.

### Bootstrap Gating

The `enable_service` variable (default `false`) allows a two-phase bootstrap:

1. `terraform apply` with `enable_service=false` — creates secrets, service account, and IAM bindings
2. Populate secret versions via `gcloud secrets versions add`
3. `terraform apply` with `enable_service=true` — creates the Cloud Run service (secrets are now available)

CI always passes `enable_service=true` because secrets are already populated.

### Security

Sensitive values (Trello credentials, OTLP headers) are stored in GCP Secret Manager and injected into Cloud Run containers via `secret_key_ref`. These values never appear in Terraform state or in plain-text environment variable definitions.

---

## Observability & Telemetry

### Architecture

```text
FastAPI (Cloud Run)
  → OpenTelemetry SDK (auto-instrumentation)
    → OTLP HTTP exporter
      → Grafana Cloud (metrics + traces)

Discord Bot (GCE e2-micro)
  → OpenTelemetry SDK (custom metrics)
    → OTLP HTTP exporter
      → Grafana Cloud (metrics)

Both → Grafana Dashboard (7 panels)
```

### Instrumentation

**Cloud Run service** — `telemetry.py` configures OpenTelemetry when `OTEL_EXPORTER_OTLP_ENDPOINT` is set:

- **Tracing**: `TracerProvider` with `BatchSpanProcessor` → OTLP HTTP exporter (`/v1/traces`)
- **Metrics**: `MeterProvider` with `PeriodicExportingMetricReader` (10s interval) → OTLP HTTP exporter (`/v1/metrics`)
- **FastAPI auto-instrumentation**: `FastAPIInstrumentor` emits `http.server.duration` histograms and per-status-code request counters

The 10-second export interval (vs. the default 60s) ensures metrics flush before Cloud Run scales the instance to zero.

**Discord Bot** — `bot_telemetry.py` emits three custom metrics via the same OTLP pipeline:

- `discord.bot.command.duration` (histogram) — AI command latency in seconds
- `discord.bot.command.success` (counter) — successful AI commands
- `discord.bot.command.failure` (counter) — failed AI commands

When the endpoint is unset, both `setup_telemetry` and `setup_bot_telemetry` are no-ops — local development and tests run without any observability infrastructure.

### Why Two Compute Resources

Cloud Run is request-driven and scales to zero between requests — ideal for the HTTP API. The Discord bot, however, must maintain a persistent WebSocket connection to the Discord Gateway, which is incompatible with Cloud Run's lifecycle model. A GCE `e2-micro` instance (Always Free tier) runs the bot as a long-lived process. Both resources are managed by Terraform.

### Grafana Dashboard

The dashboard (`infrastructure/grafana/dashboard.json`) has seven panels across two sections:

**Cloud Run service** (`service_name="issue-tracker-service"`):

1. **Request Latency (p50 / p95 / p99)** — `histogram_quantile` over `http_server_request_duration_seconds_bucket`
2. **Success Rate (2xx)** — ratio of 2xx responses to total requests
3. **Client Error Rate (4xx)** — ratio of 4xx responses to total requests
4. **Server Error Rate (5xx)** — ratio of 5xx responses to total requests

**Discord Bot** (`service_name="discord-bot"`):

5. **Command Latency (p50 / p95 / p99)** — `histogram_quantile` over `discord_bot_command_duration_seconds_bucket`
6. **Success Rate** — rate of `discord_bot_command_success_total`
7. **Failure Rate** — rate of `discord_bot_command_failure_total`

---

## CI/CD Pipeline

### Workflows

**`build_and_test`** (all branches): build → lint → type_check → unit_test → integration_test → coverage_report

**`deploy_to_cloud_run`** (`hw-3` branch): build → lint + type_check + unit_test → build_and_push_image → terraform_plan → terraform_apply → verify_health

### Deploy Pipeline Steps

1. **build_and_push_image** — authenticates to GCP, builds Docker image, pushes to Artifact Registry with `$CIRCLE_SHA1` tag
2. **terraform_plan** — runs `terraform plan` with the new image tag to preview changes
3. **terraform_apply** — applies the plan and persists the service URL to workspace
4. **verify_health** — polls `<service_url>/health` with retries until HTTP 200

---

## AI Integration (HW3)

### Overview

HW3 adds `ai_client_api` (abstract interface) and `ai_client_impl` (OpenAI implementation) following the same interface/implementation pattern from HW1. The AI is integrated into the FastAPI service at `POST /ai/chat`, where it can inspect and act on the issue tracker through typed tool calls.

### Interface: `ai_client_api`

`AIClient` is an abstract base class in `ai_client_api/client.py` (not `__init__.py`). It is framework-free — it imports only `abc` and `typing`. Two abstract methods:

- `send_message(prompt, context)` — simple text prompt / response
- `create_chat_completion(messages, tools, tool_choice)` — full chat API with optional tool definitions

The `register()` / `get_client()` factory pattern from HW1 is preserved in `ai_client_api/__init__.py`.

### Implementation: `ai_client_impl`

`OpenAIAIClient` implements `AIClient` using the OpenAI Python SDK (`gpt-4o-mini` by default). Provider credentials (`OPENAI_API_KEY`, `OPENAI_MODEL`) are read from environment variables at factory invocation time — never at import time, never hardcoded. Importing `ai_client_impl` registers the factory.

### Tool Calling

Ten domain tools are declared in `ai_tools.py` as typed JSON schemas:

| Tool | Domain Action |
|------|--------------|
| `get_boards` | List all boards |
| `get_board` | Fetch a board by ID |
| `get_issues` | List issues for a board |
| `get_issue` | Fetch an issue by ID |
| `create_issue` | Create an issue on a board |
| `update_issue` | Update issue fields (title, desc, status, members, …) |
| `create_board` | Create a new board |
| `update_board` | Rename a board |
| `delete_issue` | Delete an issue |
| `delete_board` | Delete a board |

`execute_tool()` dispatches the model's tool calls to the real `IssueTrackerClient` methods. Status strings are validated against the `Status` enum before use.

### AI Orchestration (`ai_router.py`)

`run_ai_chat()` drives a two-turn conversation:

1. Sends the user message with all tool definitions (`tool_choice="auto"`)
2. If the model emits tool calls, executes each via `execute_tool()` and collects results
3. Sends tool results back and requests a final natural-language reply
4. Returns `AIChatOut(reply, actions)` — never raw tool outputs

The `on_tool_executed` callback hook decouples AI tool execution from cross-vertical notification — `ai_router` has no direct knowledge of the chat vertical.

---

## Shared Vertical Contract (Issue Tracker Vertical)

Teams 1 (Jira), 3 (Trello), and 7 (Trello) agreed on a shared `api` package published at [`ospsd_issue_tracker`](https://github.com/tatyanacthomas/ospsd_issue_tracker). This defines provider-agnostic domain types and a `Client` ABC that all three teams implement.

### Shared Domain Types

| Type | Key Fields |
|------|-----------|
| `Board` | `id`, `board_name` |
| `Issue` | `id`, `title`, `desc`, `members`, `due_date`, `status`, `board_id` |
| `Status` | Enum: `TO_DO`, `IN_PROGRESS`, `COMPLETED` |

### Shared Client Methods

```python
get_boards() -> list[Board]
get_board(board_id: str) -> Board
get_issues(board_id: str) -> list[Issue]
get_issue(issue_id: str) -> Issue
create_issue(title, board_id, desc, members, due_date, status) -> Issue
update_issue(issue_id, title, desc, members, due_date, status, board_id) -> Issue
delete_issue(issue_id: str) -> bool
create_board(name: str) -> Board
update_board(board_id: str, name: str) -> Board
delete_board(board_id: str) -> bool
```

### How This Team Conforms

`DefaultIssueTrackerClient` (our Trello implementation from HW1) is cast to the shared `Client` type in `app.py`. The cast is valid because both ABCs define the same method signatures. The `_board_to_out()` and `_issue_to_out()` helpers normalize between the local domain models and the shared types.

---

## Cross-Vertical Integration (HW3)

### Choice: Chat Vertical (Discord — Team 8)

The issue tracker notifies the Chat vertical on real-time events: issue creation, AI tool execution, and AI response generation. The chosen provider is Discord (Team 8), but the integration is provider-agnostic through the shared `chat_client_api` contract from [`Shared-API`](https://github.com/HarshithKoriRaj/Shared-API).

### Provider Injection

`chat_provider.py` reads `CHAT_CLIENT_IMPL_MODULE` from the environment (default: `discord_client_impl`) and imports the module at lifespan startup. Importing registers the chat client factory with `chat_client_api` — the same DI pattern from HW1:

```python
# In app.py — no Discord-specific import anywhere in the service
get_chat_client().send_message(channel_id=channel_id, text=text)
```

Swapping providers (e.g., Slack, Telegram) requires only changing `CHAT_CLIENT_IMPL_MODULE`. The Terraform `var.chat_client_impl_module` injects this into Cloud Run, enabling provider swaps as a Terraform variable change with no code changes.

### Notification Triggers

| Event | Notification Sent |
|-------|-------------------|
| Issue created via REST | `"New issue created:\n'{title}' (board: {board_id}, status: {status})"` |
| AI tool executed | `"AI executed \`{tool}\`:\n{detail}"` |
| AI response generated | `"AI response:\n{reply}"` |

### Resilience

`_notify_chat_text()` catches all exceptions — a Discord failure never breaks issue creation or AI responses. The `DISCORD_NOTIFY_CHANNEL_ID` env var being absent silently skips all notifications.
