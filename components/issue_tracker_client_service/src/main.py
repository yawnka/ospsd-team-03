"""Entry point for running the service locally from source."""

import os
import sys
from pathlib import Path

import uvicorn


def _ensure_import_paths() -> None:
    """Ensure the local src directory is importable."""
    current_dir = Path(__file__).parent
    package_src = current_dir / "src"

    if package_src.is_dir():
        sys.path.insert(0, str(package_src))


_ensure_import_paths()

from issue_tracker_client_service.app import app  # noqa: E402


def main() -> None:
    """Run the FastAPI application with uvicorn."""
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    reload_enabled = os.environ.get("RELOAD", "false").lower() in {"1", "true", "yes"}

    uvicorn.run(app, host=host, port=port, reload=reload_enabled)


if __name__ == "__main__":
    main()
