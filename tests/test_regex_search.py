from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import CommandRunner


def test_regex_search(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi regex-search discord-.+")
    output: str = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned


def test_regex_search_compact(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi regex-search --compact discord-.+")
    output: str = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert re.search(r"(\d+)(,\s*[a-zA-Z0-9_-]+)*", output)


def test_regex_search_help_message(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi regex-search --help")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned
