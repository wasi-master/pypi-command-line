from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import CommandRunner


def test_compare(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi compare requests httpx")
    output: str = result.stdout.decode("utf-8")
    assert output, "No output was gotten"
    assert "requests" in output
    assert "httpx" in output
    assert "GitHub Stars" in output
    assert "Downloads" in output
    assert "Latest Version" in output


def test_compare_nonexistent(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi compare non_existent_package_1234567")
    output: str = result.stdout.decode("utf-8")
    assert output, "No output was gotten"
    assert "non_existent_package_1234567" in output
    assert "Not Found" in output
