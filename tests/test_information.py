from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import CommandRunner


def test_information(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi information rich")
    output: str = result.stdout.decode("utf-8")
    assert "rich" in output
    assert "Description" in output
    assert "Meta" in output


def test_information_with_version(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi information rich --version 1.0.0")
    output: str = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert "1.0.0" in output


def test_information_with_version_alt_syntax(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi information rich==1.0.0")
    output: str = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert "1.0.0" in output


def test_information_with_classifiers(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi information rich --show-classifiers")
    output: str = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert "── Classifiers ──" in output, "Classifiers were not found where it should have been"


def test_information_without_project_urls(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi information rich --hide-project-urls")
    output: str = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert "─── Project URLs ───" not in output, "Project urls were found where it shouldn't have been"


def test_information_without_requirements(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi information rich --hide-requirements")
    output: str = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert "── Requirements ──" not in output, "requirements were found where it shouldn't have been"


def test_information_without_github(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi information rich --hide-github")
    output: str = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert "─── GitHub ──" not in output, "Github was found where it shouldn't have been"


def test_information_without_stats(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi information rich --hide-stats")
    output: str = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert "─── Downloads ───" not in output, "Statistics were found where it shouldn't have been"


def test_information_without_meta(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi information rich --hide-meta")
    output: str = result.stdout.decode("utf-8")
    assert output, "No output was gotten"  # Assert if a output was returned
    assert "─── Meta ────" not in output, "Statistics were found where it shouldn't have been"


def test_information_help(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi information --help")
    assert result.stdout.decode("utf-8"), "No output was gotten"  # Assert if a output was returned
