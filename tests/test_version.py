from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import CommandRunner


def test_version(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi version")
    output: str = result.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    assert "pypi-command-line" in output
    assert "Current version" in output


def test_version_with_another_package(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi version charinfo")
    output: str = result.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    assert "charinfo" in output
    import re
    assert re.search(r"\d+\.\d+", output), "No version number found in output"


def test_version_with_limit(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi version discord --limit 1")
    output: str = result.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n").strip()
    assert output, "No output was gotten"  # Assert if a output was returned
    assert len(output.splitlines()) == 1, "More that one item was gotten"


def test_version_with_no_pre_releases(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi version discord --no-pre-releases")
    output: str = result.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n").strip()
    assert output, "No output was gotten"  # Assert if a output was returned


def test_version_with_show_installed_versions(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi version discord --show-installed-version")
    output: str = result.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n").strip()
    assert output, "No output was gotten"  # Assert if a output was returned


def test_version_help_message(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi version --help")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned
