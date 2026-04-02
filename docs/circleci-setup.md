# CircleCI Setup Guide

This document explains how to configure CircleCI for the project.

## Overview

The CI/CD pipeline includes:

- **Build**: Environment setup with `uv`
- **Lint**: Code quality checks with `ruff`
- **Type Check**: Static analysis with `mypy`
- **Unit Tests**: Fast tests with 85% coverage requirement
- **Integration Tests**: DI wiring and client contract verification
- **Coverage Report**: HTML coverage artifact

## Quick Setup

### 1. Connect Repository
1. Log in to [CircleCI](https://circleci.com/)
2. Add your repository from "Projects"
3. CircleCI auto-detects `.circleci/config.yml`

### 2. Environment Variables

Set these in your CircleCI project settings (Project Settings > Environment Variables):

| Variable | Description |
|----------|-------------|
| `TRELLO_API_KEY` | Trello REST API key |
| `TRELLO_API_TOKEN` | Trello REST API token |
| `TRELLO_BOARD_ID` | Target Trello board ID |

To obtain these:
- **API Key & Token**: Visit the [Trello Developer Portal](https://developer.atlassian.com/cloud/trello/guides/rest-api/api-introduction/)
- **Board ID**: Found in the URL when viewing your board (`https://trello.com/b/<BOARD_ID>/...`)

## Workflow

```
build → lint + type_check + unit_test → integration_test → coverage_report
```

All jobs run on every branch. The `integration_test` and `coverage_report` jobs require `unit_test` to pass first.

## Local Development

Run the same checks locally:

```bash
# Setup
uv sync --all-packages --group dev

# Quality checks
uv run ruff check .
uv run mypy -p issue_tracker_client_api -p issue_tracker_client_impl --explicit-package-bases

# Tests
uv run pytest components/ tests/ -m "not local_credentials" -v
uv run pytest --cov=components --cov-report=term-missing --cov-fail-under=85
```

## Troubleshooting

- **Missing environment variables**: Ensure `TRELLO_API_KEY`, `TRELLO_API_TOKEN`, and `TRELLO_BOARD_ID` are set in CircleCI project settings
- **Coverage failures**: Project requires 85% coverage — add tests or adjust threshold
- **uv command issues**: Use pure `uv` commands (`uv tree`, `uv add`) not `uv pip`

## Security Notes

- Never commit credentials to the repository
- Use CircleCI environment variables for all secrets
- The `.env` file is ignored by `.gitignore`
