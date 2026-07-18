from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest as _pytest

    from tests.conftest import CommandRunner


def test_browse(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi browse numpy --url-only")
    output: str = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert "numpy.org" in output or "pypi.org" in output


def test_browse_help_message(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi browse --help")
    assert "url" in result.stdout.decode("utf-8").lower()


def test_browse_handles_missing_project_urls(monkeypatch: _pytest.MonkeyPatch) -> None:
    """Packages whose metadata has "project_urls": null must not crash browse (regression test)."""
    import pytest
    import typer

    from pypi_cli import __main__ as cli

    info = {
        "project_urls": None,
        "project_url": "https://pypi.org/project/example/",
        "home_page": "https://example.org",
        "release_url": "https://pypi.org/project/example/1.0.0/",
        "maintainer_email": None,
    }
    monkeypatch.setattr(cli, "fetch_pypi_json", lambda name, version=None: {"info": info})
    with pytest.raises(typer.Exit):
        cli.browse(package_name="example", url_only=True)
