# Issue Tracker Client - Trello

This repo provides a small, testable Python workspace for interacting with an issue tracker using a clean abstraction (`issue_tracker_client_api`) and a default implementation (`issue_tracker_client_impl`) backed by **Trello**.

Conceptually, Trello **cards** are treated as **issues**.

## Overview
This project implements a provider-agnostic issue tracker system using:
- A clean **abstract API package**
- A concrete **Trello implementation**
- **Dependency Injection (DI)** using auto-registration at import time
- Strict typing, linting, CI, and documentation

The system separates abstraction from implementation to allow providers to plug in without changing consumer code.

## Project Structure

```text
ospsd-team-03
├── .circleci           
│    └── config.yml 
│  
├── .github
│   ├── ISSUE_TEMPLATE/                   
│   ├── PULL_REQUEST.md                
│
├── components
│   ├── issue_tracker_client_api/          
│   │   ├── src/
│   │   ├── README.md                   
│   │   └── tests/                         
│   │
│   └── issue_tracker_client_impl/     
│       ├── src/
│       ├── README.md                    
│       └── tests/                       
│
├── tests/
│   ├── integration/                     
│   └── e2e/                             
│
├── docs/                                   
│   ├── components     
│   │   ├── issue_tracker_client_api.md
│   │   └── issue_tracker_client_impl.md 
│   ├── circleci-setup.md
│   ├── component.md
│   ├── testing.md
│   └── index.md                        
├── mkdocs.yml                           
├── pyproject.toml                       
├── README.md                          
├── uv.lock                               
└── LICENSE
```

## Core Components

1.  **`issue_tracker_client_api`**
Defines the abstract `IssueTrackerClient` base class (ABC). 
    This package provides:
    - The provider-agnostic contract
    - Domain models (`Issue`, `Comment`)
    - A lightweight DI registry (`register`, `get_client`)

2. **`issue_tracker_client_impl`**
Provides `DefaultIssueTrackerClient`, a concrete implementation backed by the Trello REST API.
    This package:
    - Authenticates using Trello API credentials
    - Implements all abstract operations
    - Registers itself automatically on import (Dependency Injection)

## Dependency Injection Flow
```python
import issue_tracker_client_impl  # triggers DI registration
from issue_tracker_client_api.client import get_client

client = get_client()
issues = client.list_issues("your_board_id")
print(len(issues))
```

1. The implementation registers itself at import time.
2. get_client() returns the registered implementation.
3. Consumers never depend on Trello directly.

This keeps the system loosely coupled and extensible.

## Quickstart

### 1) Create virtual environment and install dependencies
```bash
uv venv
source .venv/bin/activate
uv sync --all-packages --group dev
```

### 2) Set Trello credentials
Set the following environment variables locally or in CI:
```bash
export TRELLO_API_KEY="your_api_key"
export TRELLO_API_TOKEN="your_api_token"
export TRELLO_BOARD_ID="your_board_id"  # required for E2E tests
```

### 3) Run tests
```bash
# all tests (unit + integration + e2e if credentials are set)
uv run pytest

#  unit tests only
uv run pytest components/
```


## Documentation

Project documentation is organized as follows:
- [API Documentation](components/issue_tracker_client_api.md)
    Detailed documentation for the `issue_tracker_client_api` package.

- [Implementation Documentation](components/issue_tracker_client_impl.md)
    Detailed documentation for the `issue_tracker_client_impl` package.

- [Component Architecture](component.md)
    Explains the system design, abstraction layer, and dependency injection approach.

- [Testing Strategy](testing.md)
    Describes unit, integration, and end-to-end testing.

- [CircleCI Setup](circleci-setup.md)
    Documents the CircleCI pipeline configuration and automation workflow.

To run the documentation locally:
```bash
uv run mkdocs serve
```
