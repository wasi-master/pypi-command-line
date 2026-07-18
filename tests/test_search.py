from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import CommandRunner


def test_search_is_deprecated(runner: type[CommandRunner]) -> None:
    """The search command is disabled because PyPI blocks the requests; it should say so."""
    result = runner.run("pypi search charinfo")
    output: str = result.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    assert "not available" in output
    assert "rsearch" in output


def test_search_help_message(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi search --help")
    output: str = result.stdout.decode("utf-8")
    assert "Search for a package" in output
