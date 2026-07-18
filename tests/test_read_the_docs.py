from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import CommandRunner


def test_read_the_docs(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi read-the-docs --url-only django context")
    output: str = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
