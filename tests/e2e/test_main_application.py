"""End-to-End tests for the ospsd-team-03 application.

This module validates the full application stack as a black box:
file structure, import chains, Python syntax, DI wiring, and
authentication behaviour.
"""

import os
import subprocess
import sys
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import issue_tracker_client_api.client as _api
import pytest
from issue_tracker_client_impl.client import DefaultIssueTrackerClient

# Mark all tests in this file as e2e tests
pytestmark = pytest.mark.e2e


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _restore_factories() -> Generator[None, None, None]:
    """Snapshot and restore the DI registry around each E2E test."""
    saved = list(_api._factories)
    yield
    _api._factories.clear()
    _api._factories.extend(saved)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

WORKSPACE_ROOT: Path = Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_application_structure_integrity() -> None:
    """All required source files exist in the workspace."""
    expected_files = [
        "pyproject.toml",
        "components/issue_tracker_client_api/pyproject.toml",
        "components/issue_tracker_client_api/src/issue_tracker_client_api/__init__.py",
        "components/issue_tracker_client_api/src/issue_tracker_client_api/client.py",
        "components/issue_tracker_client_impl/pyproject.toml",
        "components/issue_tracker_client_impl/src/issue_tracker_client_impl/__init__.py",
        "components/issue_tracker_client_impl/src/issue_tracker_client_impl/client.py",
        "tests/e2e/test_main_application.py",
    ]

    missing = [f for f in expected_files if not (WORKSPACE_ROOT / f).exists()]

    if missing:
        pytest.fail(f"Missing required files: {missing}")


def test_all_imports_work() -> None:
    """Both packages can be imported in a fresh subprocess."""
    import_test_code = (
        "import issue_tracker_client_api\n"
        "import issue_tracker_client_impl\n"
        'print("All imports successful")\n'
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", import_test_code],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
        cwd=str(WORKSPACE_ROOT),
        env={**__import__("os").environ, "TRELLO_API_KEY": "dummy"},
    )

    if result.returncode != 0:
        pytest.fail(f"Import check failed:\n{result.stderr}")

    assert "All imports successful" in result.stdout


def test_source_files_syntax_valid() -> None:
    """Every .py file under components/**/src has valid Python syntax."""
    py_files = sorted((WORKSPACE_ROOT / "components").glob("*/src/**/*.py"))

    assert py_files, "No .py files found under components/**/src"

    for py_file in py_files:
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "py_compile", str(py_file)],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        if result.returncode != 0:
            pytest.fail(
                f"Syntax error in {py_file.relative_to(WORKSPACE_ROOT)}:\n"
                f"{result.stderr}"
            )


def test_di_full_flow_with_token() -> None:
    """DI round-trip: import -> register -> get_client -> correct type."""
    _api._factories.clear()
    sys.modules.pop("issue_tracker_client_impl", None)

    with patch.dict(
        "os.environ",
        {"TRELLO_API_KEY": "test-key-e2e", "TRELLO_API_TOKEN": "test-token-e2e"},
    ):
        import issue_tracker_client_impl  # noqa: PLC0415, F401

        client = _api.get_client()

    assert isinstance(client, DefaultIssueTrackerClient)


def test_client_raises_without_token() -> None:
    """DefaultIssueTrackerClient raises KeyError when TRELLO_API_KEY is absent."""
    _api._factories.clear()
    sys.modules.pop("issue_tracker_client_impl", None)

    skip = {"TRELLO_API_KEY", "TRELLO_API_TOKEN"}
    env = {k: v for k, v in os.environ.items() if k not in skip}


    with patch.dict("os.environ", env, clear=True):
        import issue_tracker_client_impl  # noqa: PLC0415, F401

        with pytest.raises(KeyError, match="TRELLO_API_KEY"):
            _api.get_client()


@pytest.mark.local_credentials
def test_full_workflow_against_real_trello() -> None:
    """Full E2E workflow: client creation → API call → response handling."""
    api_key = os.environ.get("TRELLO_API_KEY")
    api_token = os.environ.get("TRELLO_API_TOKEN")
    board_id = os.environ.get("TRELLO_BOARD_ID")

    missing = [
        name
        for name, value in {
            "TRELLO_API_KEY": api_key,
            "TRELLO_API_TOKEN": api_token,
            "TRELLO_BOARD_ID": board_id,
        }.items()
        if not value
    ]
    if missing:
        pytest.skip(f"Missing env var(s): {', '.join(missing)} — "
                    "skipping live E2E test")

    import issue_tracker_client_impl  # noqa: PLC0415, F401

    client = _api.get_client()
    assert isinstance(client, DefaultIssueTrackerClient)

    # 1. get_issues
    issues = list(client.get_issues(board_id))
    assert isinstance(issues, list)

    # 2. create_issue
    new_issue = client.create_issue(
        title="E2E Test Card",
        board_id=board_id,
        desc="Created by E2E test",
    )
    assert new_issue.title == "E2E Test Card"
    assert new_issue.board_id
    assert new_issue.desc == "Created by E2E test"

    # 3. get_issue
    fetched = client.get_issue(new_issue.id)
    assert fetched.id == new_issue.id
    assert fetched.title == "E2E Test Card"
    assert fetched.board_id == new_issue.board_id

    # 4. update_issue
    updated = client.update_issue(new_issue.id, desc="Updated by E2E test")
    assert updated.id == new_issue.id
    assert updated.desc == "Updated by E2E test"

    # 5. delete_issue (archive)
    result = client.delete_issue(new_issue.id)
    assert result is True
