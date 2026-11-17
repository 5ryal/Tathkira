"""Placeholder test proving the test runner and package import work."""

import tathkira


def test_package_imports() -> None:
    """The tathkira package is importable from the src layout."""
    assert tathkira is not None
