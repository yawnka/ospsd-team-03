# ospsd-team-03
Team 3 Repository for Open Source &amp; Professional Software Development class Spring 2026

## Team Members
- ys4780	Yanka Sikder @yawnka
- fas6488	Farhen Shefa @farhen-shefa
- zz10803	Zunyu Zhang @zhangyushao0
- yk3183	Yusuke Katsuki @katsukii
- hr2712	Hyun Sang (Hayden) Ryu @hayden-hs

TAs:
- @adithyab-20
- @ivanearisty
- @AranyaAryaman

## What This Repo Provides

Two installable Python components under ` \components ` using a `uv` workspace:

| Package | Purpose |
|---------|---------|
| `issue_tracker_client_api` | Provider-agnostic abstract interface (ABC) + DI hooks |
| `issue_tracker_client_impl` | Concrete implementation; reads token from `ISSUE_TRACKER_TOKEN` env var |

Consumers should depend only on the interface component. 
The implementation component is imported only to register itself via Dependency Injection.

## Project Structure

```text
ospsd-team-03
├── .circleci           
│    └── config.yml                        # CI pipeline: runs linting, type-checking, tests, coverage
│  
├── .github
│   ├── ISSUE_TEMPLATE/                    # GitHub issue templates for bug reports & feature requests
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   │
│   ├── PULL_REQUEST.md                    # Pull request template for structured submissions
│
├── components
│   ├── issue_tracker_client_api/          # Interface component (provider-agnostic contract)
│   │   ├── src/
│   │   │   ├── __init__.py
│   │   │   └── client.py                  # Abstract Base Classes + DI factory (get_client)
│   │   ├── pyproject.toml                 # Package metadata and dependencies
│   │   ├── README.md                      # Interface-specific documentation
│   │   └── tests/                         # Unit tests for interface behavior
│   │       └── test_client_api.py
│   │
│   └── issue_tracker_client_impl/         # Trello implementation component
│       ├── src/
│       │   └── __init__.py                # Registers implementation via Dependency Injection
│       │   └── client.py                  # Concrete Trello client implementation
│       ├── pyproject.toml                 # Package metadata and provider dependencies
│       ├── README.md                      # Implementation-specific documentation
│       └── tests/                         # Unit tests (mocking Trello API where applicable)
│           └── test_impl.py                
│
├── tests/
│   ├── integration/                       # Integration tests (verifies DI wiring works correctly)
│   │   └── test_di_wiring.py
│   │
│   └── e2e/                               # End-to-end tests using real Trello credentials
│       └── test_main_application.py
│
├── docs/                                   
├── mkdocs.yml                            # MkDocs configuration
├── pyproject.toml                        # Shared tooling config (ruff, mypy, pytest, coverage)
├── README.md                             # Root project documentation
├── uv.lock                               # Locked dependency versions
└── LICENSE
```


## Quickstart

```sh
uv sync             # install workspace + dev deps
uv run ruff check . # lint  (select = ALL)
uv run mypy .       # type-check (strict = true)
uv run pytest       # test + coverage
```

## API Concepts

All client methods accept a `board` parameter as the primary scope identifier:

- In **Trello**, `board` maps to a Trello board ID.
- Other providers may map it differently (e.g. a project key, workspace slug).

Issue types (`Issue`, `Comment`) remain provider-agnostic in the API layer.

## How DI Works

Importing `issue_tracker_client_impl` auto-registers its factory into the API package:

```python
import issue_tracker_client_impl          # side-effect: registers DefaultIssueTrackerClient
from issue_tracker_client_api.client import get_client

client = get_client()                     # returns a DefaultIssueTrackerClient
client.list_issues("my-trello-board-id")  # board = Trello board identifier
<<<<<<< HEAD


## Recent Changes (HW1)

### E2E Tests - Hyun Sang Ryu
- Added end-to-end test suite (`tests/e2e/test_main_application.py`)
- Validates full application workflow with Trello integration
- Registered e2e pytest marker in `pyproject.toml````
=======
```

## Features

- Provider-agnostic Issue Tracker interface using Abstract Base Classes
- Trello-based concrete implementation
- Dependency Injection via factory registration
- Unit tests for each component
- Integration tests verifying DI wiring
- End-to-end (E2E) tests for full Trello workflow
- Strict static analysis (Ruff + Mypy strict mode)
- Coverage reporting with threshold enforcement
- uv-based workspace dependency management
>>>>>>> 419fa95 (docs: reorganize repo structure and update root README)
