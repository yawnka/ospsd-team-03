"""Smoke tests — verify the package is importable and has expected metadata."""

import ospsd_team03


def test_package_importable() -> None:
    """The package must be importable without errors."""
    assert ospsd_team03.__doc__ is not None
