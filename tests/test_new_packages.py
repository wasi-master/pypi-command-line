from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import CommandRunner


def test_new_packages(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi new-packages")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned


def test_new_packages_with_author(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi new-packages --show-author")
    output: str = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert re.search(r"\S+@\S+\.\S+", output)


def test_new_packages_without_link(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi new-packages --hide-link")
    output: str = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert " ┃ Link " not in output, "Link was found"


def test_new_packages_help(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi new-packages --help")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned
