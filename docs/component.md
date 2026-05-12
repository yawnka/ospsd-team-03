# Component Guide

Every workspace component lives under `components/<component_name>/` and represents one of the following:

- an abstract contract implemented with Python ABCs,
- a concrete provider implementation of a contract,
- a deployable service package,
- a generated service client,
- an adapter that preserves a local interface while delegating to a remote service.

The goal is to keep each package small, typed, independently testable, and easy to swap through dependency injection.

## Directory Layout

Most handwritten components follow this structure:

```text
<component_name>/
├── pyproject.toml
├── README.md
├── src/<component_name>/
│   ├── __init__.py
│   └── client.py
└── tests/
```

Some components have additional files. For example, the FastAPI service contains route, schema, telemetry, and AI-tool wiring modules, while the generated service client contains generated endpoint and model packages.

## Component Types

### Contract Components

Contract packages define provider-agnostic interfaces. They should not depend on provider SDKs, HTTP clients, secrets, or deployment-specific configuration.

Examples:
- `issue_tracker_client_api`
- `ai_client_api`

Contract packages usually contain:
- ABC definitions,
- provider-agnostic domain models,
- dependency injection helpers such as `register()` and `get_client()`,
- public exports in `__init__.py`

### Implementation Components

Implementation packages provide concrete behavior behind a contract.

Examples:
- `issue_tracker_client_impl`
- `ai_client_impl`

Implementation packages usually contain:
- concrete classes that inherit from the contract ABC,
- provider-specific SDK or HTTP calls,
- translation between provider responses and project domain models,
- credential loading from environment variables,
- auto-registration on import.

Consumers should depend on the contract package, not directly on the implementation package.


### Service Component

`issue_tracker_client_service` is the deployable FastAPI application.

It is responsible for:
- HTTP routes,
- request and response schemas,
- health checks,
- telemetry,
- AI-assisted workflows,
- tool-call execution,
- cross-vertical Discord notifications,
- deployment entrypoints.

### Generated Client Component

`issue_tracker_client_service_client` is generated from the FastAPI service's OpenAPI schema.

It is responsible for:
- typed HTTP client methods,
- generated request and response models,
- remote access to the service.

Because this package is generated, edits should be limited and intentional. Regenerate it from the OpenAPI spec when the service API changes.

### Adapter Component

`issue_tracker_client_adapter` implements the issue tracker interface while delegating to the generated service client.

It is responsible for:
- preserving the local `IssueTrackerClient` contract,
- hiding HTTP details from consumers,
- supporting location transparency.


## `pyproject.toml` Checklist

Each component must define:
#### **`[project]`**: 
- `name` matches the component folder
- `version` is present
- `description` explains the package purpose
- `readme = "README.md"` is set
- `requires-python = ">=3.13"` matches the workspace
- Explicitly list **direct dependencies only**

#### **`[build-system]`**:
- Use `hatchling` as the build backend.
#### **`[tool.uv.sources]`**:
- Declare cross-component dependencies so the implementation can depend on the API component (e.g., via uv workspace sources).


## README Expectations

Each component README should document:

- purpose and scope,
- public classes, functions, or models,
- usage pattern with absolute imports,
- dependency injection behavior,
- required environment variables,
- external provider assumptions,
- test commands relevant to the component.

The README should describe the public contract and behavior more than private implementation details.

## Implementation Notes

### `client.py`

Many components use `client.py` as the primary public module.

Typical patterns:
- contract packages define the ABC, domain models, and DI hooks,
- implementation packages define concrete clients and register them,
- adapters implement a contract while calling a remote service client.

### Package Initialization

`__init__.py` should export the public API of the package.

For contract packages, this usually includes:
- ABC types,
- domain models,
- `register()`,
- `get_client()`.

For implementation packages, importing the package should perform provider registration when that pattern is used.


## Testing

Component-level tests belong in each component's `tests/` directory.

They should:
- target the public interface,
- verify ABC and DI behavior,
- isolate provider SDKs and network calls with mocks,
- use deterministic fixtures,
- avoid depending on live credentials.

Repository-level integration and end-to-end tests belong under the root `tests/` directory. Real provider tests that require credentials should be marked with `local_credentials`.
