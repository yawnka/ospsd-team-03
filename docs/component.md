# Component Definition

Every workspace component lives under `components/<component_name>/` and represents either:
- An abstract contract implemented as an ABC or,
- A concrete implementation of that contract

## Directory Layout

Each component follows this structure:
```text
<component_name>/
├── pyproject.toml
├── README.md
├── src/<component_name>/
│   ├── __init__.py
│   └── client.py        # implementation logic (or API surface for contracts)
└── tests/               # optional component-scoped tests
```

> Note: In this repository, the implementation code lives in `client.py` (rather than `_impl.py`). The API and implementation packages follow the same high-level layout, with the implementation additionally performing DI registration on import.


## `pyproject.toml` Checklist

Each component must define:
#### **`[project]`**: 
- `name` matches the component folder
- `version`
- `description`
- `readme = "README.md"`
- `requires-python = ">=3.11"`
- Explicitly list **direct dependencies only**

#### **`[build-system]`**:
- Use `hatchling` as the build backend.
#### **`[tool.uv.sources]`**:
- Declare cross-component dependencies so the implementation can depend on the API component (e.g., via uv workspace sources).


## README Expectations

Each component README should document, at minimum:

- Overview and scope
- Exposed interfaces (classes/functions/models)
- Usage pattern (with absolute imports)
- Component dependencies and any required configuration

The README should describe the **public contract and behavior**, not internal implementation details.

## Implementation Notes

### `client.py`

- **Contract packages** (`issue_tracker_client_api`): define the ABC, domain models, and the DI hook (`register()` / `get_client()`).
- **Implementation packages** (`issue_tracker_client_impl`): define concrete classes that implement the contract and map provider responses into domain models.

### Package Initialization (`__init__.py`)

- **Contract package**: exports public types and the `get_client()` factory.
- **Implementation package**: performs **auto-registration on import** so consumers can call `get_client()` without manual wiring.


## Testing

Component-level tests belong in `tests/` within each component. They should:

- Target the public interface (ABC contract, domain models, DI behavior)
- Use mocks to isolate external services (Trello)
- Keep fixtures local to the component
