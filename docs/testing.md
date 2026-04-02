# Testing Guide

This document explains the testing strategy and how to run different types of tests.

The repository follows a component-based architecture. Tests validate:

- API contract correctness
- Implementation behavior
- Dependency injection (DI) registration
- Trello integration (when credentials are available)
- End-to-end workflow behavior


## Test Markers

The project uses pytest markers to categorize tests based on their requirements and suitable environments.

### Core Test Types

- `unit`: Fast, isolated tests that do not require external dependencies
- `integration`: Tests that verify API + implementation interaction
- `e2e`: End-to-end tests validating complete application workflows

### Environment-Specific Markers

- `circleci`: Tests safe to run in CI/CD environments
- `local_credentials`: Tests that require local Trello credentials (environment variables)

> Note: This project authenticates to Trello via environment variables (not `credentials.json` / `token.json`). We keep the `local_credentials` marker to distinguish tests that require **real** credentials from tests that can run anywhere.

## Running Tests

### All Unit Tests (Fast)

```bash
uv run pytest components/ -m unit
```
These tests:
- Mock Trello API calls
- Verify domain model mapping
- Validate contract behavior
- Confirm DI registration works

### CircleCI-Compatible Tests Only

```bash
uv run pytest -m circleci
```

These tests:
- Do not require local credential files
- Validate DI wiring and factory functions
- Ensure non-interactive execution
- Confirm expected failure behavior when credentials are invalid

### Local Tests Only (Requires Credentials)

```bash
uv run pytest -m local_credentials
```
These tests:
- Make real Trello API calls
- Validate real authentication
- Confirm correct response parsing
- Verify full implementation behavior

### Integration Tests

```bash
uv run pytest -m integration
```
These tests verify:
- API contract and implementation compatibility
- Factory wiring via `get_client()`
- Mapping of provider responses into domain models
- Cross-component interaction (with or without mocks)

### E2E Tests

```bash
uv run pytest -m e2e
```
These tests verify:
- Full workflow from client acquisition to Trello interaction
- End-to-end behavior through public APIs only
- Correct domain-level outputs

### Exclude Credential-Dependent Tests

```bash
uv run pytest -m "not local_credentials"
```
Useful when running locally without Trello credentials.

## Test Categories by Environment

### CircleCI / CI Environment

Tests marked with `@pytest.mark.circleci` are safe to run in CI environments:

- **Requirements**: 
- No local credential files required
- Non-interactive execution only
- Environment variables may or may not be present

- **What they test**:
  - Imports and packaging correctness
  - Dependency injection registration
  - `get_client()` behavior
  - Contract compliance (API ↔ implementation integration)
  - Clean skipping/failure behavior when credentials are missing

Example CI command:

```bash
uv run pytest -m circleci --tb=short
```

### Local Development

Tests marked with `@pytest.mark.local_credentials` require real Trello credentials:

- **Requirements**:
  - Valid `TRELLO_API_KEY`, `TRELLO_API_TOKEN` and `TRELLO_BOARD_ID` in environment
  - Network access

- **What they test**:
  - Real Trello API connectivity
  - Board and card retrieval
  - Correct domain model construction
  - Full workflows (create/list/comment/close)
  - End-to-end functionality

## Environment Variables(CI or Local)

Set these environment variables in your environment:

```bash
export TRELLO_API_KEY="your_api_key"
export TRELLO_API_TOKEN="your_api_token"
export TRELLO_BOARD_ID="your_board_id"  # required for E2E tests
```

# Test Examples

### Running Tests Without Network Calls
```bash
# Only run tests that don't make real API calls
uv run pytest -m "unit or (circleci and not local_credentials)"
```

### Running Full Local Test Suite
```bash
# Run all tests including those requiring real credentials
uv run pytest
```

### Debugging Authentication Issues
```bash
# Run only authentication-related tests
uv run pytest -k "auth" -v
```

## Expected Behavior in Different Environments

### Local Development (with credentials)

- Unit tests pass
- Real Trello API calls succeed
- E2E tests pass (when `TRELLO_BOARD_ID` and is accessible)

### Local Development (without credentials)

- Unit tests pass
- Credential-dependent tests are skipped with clear messages
- No hanging or interactive prompts

### CircleCI (with environment variables)

- Tests marked `circleci` pass
- Tests marked `local_credentials` run (if enabled) or are skipped
- Fast execution (no timeouts)

### CircleCI (without environment variables)

- `circleci` tests still pass
- Credential-dependent tests skip cleanly
- No failures caused solely to missing credentials
