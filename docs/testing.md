# Testing Guide

This document explains the testing strategy and how to run different types of tests.

The repository follows a component-based architecture. Tests validate:

- issue tracker API contract correctness,
- Trello implementation behavior,
- AI client contract and OpenAI implementation behavior,
- dependency injection registration,
- AI tool-call execution,
- cross-vertical Chat integration through Discord,
- Trello integration when credentials are available,
- end-to-end workflow behavior.


## Test Markers

The project uses pytest markers to categorize tests based on their requirements and suitable environments.

### Core Test Types

- `unit`: Fast, isolated tests that do not require external services
- `integration`: Tests that verify component wiring, service behavior, AI tool-call flow, and cross-vertical behavior
- `e2e`: End-to-end tests validating complete application workflows

### Environment-Specific Markers

- `circleci`: Tests safe to run in CI/CD environments
- `local_credentials`: Tests that require real external credentials, such as Trello or Discord credentials

> Note: This project authenticates to external providers through environment variables. The `local_credentials` marker distinguishes tests that require real provider credentials from tests that can run anywhere.

## Running Tests

### All Unit Tests (Fast)

```bash
uv run pytest components/ -m unit
```
These tests:
- mock provider SDKs and network calls,
- verify domain model mapping,
- validate issue tracker and AI contracts,
- confirm dependency injection registration works,
- keep behavior deterministic and fast.


### CircleCI-Safe Tests Only

```bash
uv run pytest components/ tests/ -m "not local_credentials"
```

These tests:
- avoid real provider credentials,
- validate dependency injection wiring and factory functions,
- exercise deterministic AI tool-call paths,
- verify non-interactive execution,
- confirm expected failure or skip behavior when credentials are missing.

### Local Credential Tests

```bash
uv run pytest -m local_credentials
```
These tests may:
- make real Trello API calls,
- send or read messages through a sandbox Discord channel,
- validate real authentication,
- confirm provider response parsing,
- verify full implementation behavior across a live provider boundary.

### Integration Tests

```bash
uv run pytest tests/integration/ -m integration
```

These tests verify:
- API contract and implementation compatibility,
- factory wiring through `get_client()`,
- mapping of provider responses into domain models,
- service route behavior,
- AI tool-call execution,
- cross-component interaction,
- cross-vertical Chat integration.

### Real Discord Cross-Vertical Test

Most integration tests use deterministic fakes so they are safe for CI and local development without external credentials. The project also includes a credential-gated test that uses the real shared Chat API and Team 8's Discord implementation:

```text
tests/integration/test_real_discord_cross_vertical.py
```

This test intentionally keeps OpenAI and Trello fake so the AI tool call and issue creation are deterministic. It does **not** fake the Chat vertical. Instead, it imports the real Discord provider, resolves it through the shared `chat_client_api.get_client()` factory, sends a message to a sandbox Discord channel, and reads recent messages back through the same provider.

Run it manually with:

```bash
DISCORD_INTEGRATION_TESTS=1 \
DISCORD_BOT_TOKEN="your_discord_bot_token" \
DISCORD_GUILD_ID="your_discord_server_id" \
DISCORD_NOTIFY_CHANNEL_ID="your_sandbox_channel_id" \
uv run pytest tests/integration/test_real_discord_cross_vertical.py \
  -m local_credentials -rs
```

`DISCORD_INTEGRATION_TESTS=1` is a safety switch so real Discord messages are not sent during normal test runs.

### E2E Tests

```bash
uv run pytest -m e2e
```
These tests verify:
- full workflow behavior through public APIs,
- application entrypoint behavior,
- correct domain-level outputs,
- deployed or fully wired service behavior where applicable.

### Exclude Credential-Dependent Tests

```bash
uv run pytest -m "not local_credentials"
```
Useful when running locally without Trello, OpenAI, or Discord credentials.

## Test Categories by Environment

### CircleCI Environment

CI-safe tests should avoid real network calls unless a job is explicitly configured with credentials.

Requirements:
- no local credential files,
- non-interactive execution,
- deterministic behavior,
- no real Discord messages unless the credential-gated test is explicitly enabled.

What they test:
- imports and packaging correctness,
- dependency injection registration,
- `get_client()` behavior,
- contract compliance,
- deterministic AI tool-call behavior,
- clean skipping or failure behavior when credentials are missing.

Example CI-safe command:

```bash
uv run pytest components/ tests/ -m "not local_credentials" --tb=short
```

### Local Development

Tests marked with `@pytest.mark.local_credentials` require real external credentials. 

- **Requirements**:
  - valid `TRELLO_API_KEY`, `TRELLO_API_TOKEN`, and `TRELLO_BOARD_ID` for Trello tests,
  - valid `DISCORD_BOT_TOKEN`, `DISCORD_GUILD_ID`, and `DISCORD_NOTIFY_CHANNEL_ID` for real Discord tests,
  - network access.

- **What they test**:
  - real Trello API connectivity,
  - board and card retrieval,
  - correct domain model construction,
  - full issue workflows,
  - real Discord send/read behavior through the shared Chat API.


## Environment Variables

Set these environment variables as needed for local or CI runs:

```bash
export TRELLO_API_KEY="your_trello_api_key"
export TRELLO_API_TOKEN="your_trello_api_token"
export TRELLO_BOARD_ID="your_trello_board_id"

export OPENAI_API_KEY="your_openai_api_key"

export CHAT_CLIENT_IMPL_MODULE="discord_client_impl"
export DISCORD_BOT_TOKEN="your_discord_bot_token"
export DISCORD_GUILD_ID="your_discord_server_id"
export DISCORD_NOTIFY_CHANNEL_ID="your_sandbox_channel_id"
```
`TRELLO_BOARD_ID` is required for tests that create, list, or update real Trello cards. `DISCORD_INTEGRATION_TESTS=1` is additionally required to run the real Discord cross-vertical test.

## Test Examples

### Running Tests Without Network Calls

```bash
uv run pytest components/ tests/ -m "not local_credentials"
```

### Running Full Local Test Suite

```bash
uv run pytest
```

### Running Only AI-Related Tests

```bash
uv run pytest -k "ai" -v
```

### Running Only Discord-Related Tests

```bash
uv run pytest -k "discord" -v
```

### Debugging Authentication Issues

```bash
uv run pytest -k "auth" -v
```

## Expected Behavior in Different Environments

### Local Development with Credentials

- Unit tests pass.
- Credential-gated Trello tests can call the real Trello API.
- Credential-gated Discord tests can send/read messages in the sandbox Discord channel when `DISCORD_INTEGRATION_TESTS=1`.
- End-to-end tests pass when `TRELLO_BOARD_ID` is set and accessible.

### Local Development without Credentials

- Unit tests pass.
- CI-safe integration tests pass.
- Credential-dependent tests skip cleanly or are excluded with `-m "not local_credentials"`.
- No hanging or interactive prompts occur.

### CI with Environment Variables

- CI-safe tests pass.
- Credential-dependent tests run only if the job explicitly includes the required secrets.
- Coverage is generated.
- Test results are uploaded to CircleCI.

### CI without Environment Variables

- CI-safe tests still pass.
- Credential-dependent tests are skipped or excluded.
- No failures are caused solely by missing local credentials.