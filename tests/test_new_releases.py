from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import CommandRunner


def test_new_releases(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi new-releases")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned


def test_new_releases_with_author(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi new-releases --show-author")
    output: str = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert re.search(r"\S+@\S+\.\S+", output)


def test_new_releases_without_link(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi new-releases --hide-link")
    output: str = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert " ┃ Link " not in output, "Link was found"


def test_new_releases_help(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi new-releases --help")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned
