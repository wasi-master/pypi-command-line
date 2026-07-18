from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import CommandRunner


def test_description(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi description django")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned


def test_description_from_github(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi description django --force-github")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned


def test_description_help_message(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi description --help")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned
