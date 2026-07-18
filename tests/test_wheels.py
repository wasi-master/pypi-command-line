from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import CommandRunner


def test_wheels(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi wheels charinfo")
    output: str = result.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    assert output, "No output was gotten"  # Assert if a output was returned


def test_wheels_with_version(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi wheels charinfo 0.1.0")
    output: str = result.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    assert output, "No output was gotten"  # Assert if a output was returned


def test_wheels_with_version_shortened(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi wheels charinfo 0.1")
    output: str = result.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    assert output, "No output was gotten"  # Assert if a output was returned


def test_wheels_with_version_alt(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi wheels charinfo==0.1.0")
    output: str = result.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    assert output, "No output was gotten"  # Assert if a output was returned


def test_wheels_with_version_shortened_alt(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi wheels charinfo==0.1")
    output: str = result.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    assert output, "No output was gotten"  # Assert if a output was returned


def test_wheels_with_supported_only(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi wheels charinfo --supported-only")
    output: str = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned


def test_wheels_help_message(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi wheels --help")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned
