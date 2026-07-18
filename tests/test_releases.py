from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import CommandRunner


def test_releases(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi releases charinfo")
    output: str = result.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    assert output, "No output was gotten"  # Assert if a output was returned


def test_releases_with_version(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi releases charinfo --version 0.1.0")
    output: str = result.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    assert output, "No output was gotten"  # Assert if a output was returned


def test_releases_with_version_alt(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi releases charinfo==0.1.0")
    output: str = result.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    assert output, "No output was gotten"  # Assert if a output was returned


def test_releases_with_link(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi releases charinfo==0.1.0 --show-links")
    output: str = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert re.search(r"(https?:\/\/)?([\w\-])+\.{1}([a-zA-Z]{2,63})([\/\w-]*)*\/?\??([^#\n\r]*)?#?([^\n\r]*)", output)


def test_releases_search_help_message(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi releases --help")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned
