# ospsd-team-03 — Trello Issue Tracker Client

This repo provides a small, testable Python workspace for interacting with an issue tracker using a clean abstraction (`issue_tracker_client_api`) and a default implementation (`issue_tracker_client_impl`) backed by **Trello**.

The goal is to treat Trello cards as **issues**, and expose a consistent interface for listing issues, reading a single issue, creating issues, closing issues, and commenting.

## Quickstart

### 1) Create venv + install dependencies (uv)
```bash
uv venv
source .venv/bin/activate
uv sync --all-packages --group dev
