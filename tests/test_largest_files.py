from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import CommandRunner


def test_largest_files(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi largest-files")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned


def test_largest_files_help(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi largest-files --help")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned
