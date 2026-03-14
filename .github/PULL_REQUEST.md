## Summary

  HW2: Transform the local issue tracker library into a deployable microservice with
  Trello authorization, FastAPI service, auto-generated client, and service client adapter.

  ## Changes

  ### Task 1: Trello Authorization (OAuth)
  - Added `oauth.py` module with `build_authorization_url` for Trello's redirect-based
  authorization flow (token delivered via URL fragment)
  - Implemented `/auth/login`, `/auth/callback`, `/auth/token` endpoints in the FastAPI service
  - Added in-memory session store for per-user Trello tokens
  - Added CORS middleware for cross-origin browser requests
  - Refactored `DefaultIssueTrackerClient` constructor to accept `api_key` and `token` as
  parameters (supports per-user credential injection)
  - Updated DI factory registration to use a lambda that reads env vars
  - Added comprehensive unit tests for OAuth and auth endpoints

  ### Task 2: FastAPI Service
  - Built FastAPI service exposing all core API endpoints over HTTP
  - Endpoints: `/health`, `/boards/{board}/issues` (list, get, create, close), comments
  - Request-scoped client dependency injection via `Depends()`
  - Pydantic request/response schemas
  - Custom error handling for missing environment variables

  ### Task 3: Auto-Generated Client + Service Client Adapter
  - Generated type-safe HTTP client from OpenAPI spec using `openapi-python-client`
  - Built `ServiceClientAdapter` implementing `IssueTrackerClient` ABC using the generated client
  - Adapter provides location transparency (remote service usable through same contract as local library)
  - DI auto-registration on import

  ### Task 4: Deployment + CircleCI
  - Added multi-stage `Dockerfile` for production deployment
  - Added `render.yaml` with service config, health check, and environment variable bindings
  - Added CircleCI `deploy` job that triggers Render deploy hook and verifies `/health`
  - Configured automatic deployment on push to `hw-2` branch
  - Environment variables (`TRELLO_API_KEY`, `TRELLO_API_TOKEN`, `REDIRECT_URI`) stored
  via Render's native secrets manager

  ### Task 5: Docs + Cleanup
  - Fixed mypy "source file found twice" error by removing spurious `src/__init__.py`
  - Fixed ruff import sorting violation (I001) in `app.py`
  - Added MkDocs documentation pages for service, service client, and adapter components
  - Updated `mkdocs.yml` nav and plugin paths for all five components
  - Updated `docs/index.md` to reflect full HW2 architecture
  - Updated root `README.md` with all five components, project structure, and deployment section
  - Fixed service `README.md`: removed DRAFT label, corrected OAuth provider from Google to Trello

  ## Files Modified

  ### Task 1 (Trello Auth)
  - `components/issue_tracker_client_impl/src/issue_tracker_client_impl/oauth.py` —
  Trello authorization URL builder
  - `components/issue_tracker_client_impl/tests/test_oauth.py` — OAuth unit tests
  - `components/issue_tracker_client_impl/src/issue_tracker_client_impl/client.py` —
  constructor now takes `api_key` and `token` params
  - `components/issue_tracker_client_impl/src/issue_tracker_client_impl/__init__.py` — DI
  registration uses lambda with env vars
  - `components/issue_tracker_client_service/src/issue_tracker_client_service/app.py` —
  auth endpoints + CORS middleware
  - `components/issue_tracker_client_service/src/issue_tracker_client_service/auth.py` —
  OAuth state management
  - `components/issue_tracker_client_service/src/issue_tracker_client_service/session.py` —
  in-memory session store
  - `components/issue_tracker_client_service/src/issue_tracker_client_service/schemas.py` —
  Pydantic models including `AuthStatusOut`
  - `components/issue_tracker_client_service/tests/test_service.py` — auth + service tests

  ### Task 2 (FastAPI Service)
  - `components/issue_tracker_client_service/` — full service component

  ### Task 3 (Generated Client + Adapter)
  - `components/issue_tracker_client_service_client/` — auto-generated OpenAPI client
  - `components/issue_tracker_client_adapter/` — service client adapter

  ### Task 4 (Deployment)
  - `Dockerfile` — multi-stage Docker build
  - `render.yaml` — Render service configuration
  - `.circleci/config.yml` — deploy job with health check verification

  ### Task 5 (Docs + Cleanup)
  - `components/issue_tracker_client_service/src/__init__.py` — removed (caused mypy duplicate module)
  - `components/issue_tracker_client_service/src/issue_tracker_client_service/app.py` — fixed import sorting
  - `components/issue_tracker_client_service/README.md` — removed DRAFT, corrected OAuth provider
  - `README.md` — all five components, deployment section, updated project structure
  - `mkdocs.yml` — added three new component pages to nav and plugin paths
  - `docs/index.md` — updated to reflect full architecture
  - `docs/components/issue_tracker_client_service.md` — new
  - `docs/components/issue_tracker_client_service_client.md` — new
  - `docs/components/issue_tracker_client_adapter.md` — new

  ## Testing

  - [x] All unit tests pass (67 passed, 1 skipped)
  - [x] Ruff passes (`ruff check .`)
  - [x] MyPy passes (`mypy -p ... --explicit-package-bases`)
  - [x] Coverage meets 85% threshold (94.10%)
  - [x] MkDocs builds cleanly (`mkdocs build --strict`)

  ## Notes for Reviewers

  - Auth provider is Trello's own redirect-based authorization (not a separate OAuth 2.0 provider)
  - Trello delivers tokens via URL fragment — the `/auth/callback` endpoint returns an HTML
  page with JS that extracts the token and POSTs it to `/auth/token`
  - Tokens are stored in an in-memory session; token expiration is set to 30 days
  - Env vars required: `TRELLO_API_KEY`, `TRELLO_API_TOKEN`, `REDIRECT_URI` —
  shared privately, never committed
  - Once a production URL is available, it must be added as an allowed origin in the
  Trello Power-Up admin page (https://trello.com/power-ups/admin)
