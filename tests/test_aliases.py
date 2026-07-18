"""Tests for command aliases and global CLI options."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import CommandRunner


def test_all_alias_targets_are_real_commands() -> None:
    """Every alias must point at a command that actually exists (catches typos like s -> rsearch)."""
    import typer.main

    from pypi_cli.__main__ import ALIAS_MAPPING, COMMAND_ALIASES, app

    click_app = typer.main.get_command(app)
    command_names = set(click_app.commands)
    assert set(COMMAND_ALIASES) <= command_names, "COMMAND_ALIASES contains unknown commands"
    assert set(ALIAS_MAPPING.values()) <= command_names, "An alias points at a nonexistent command"


def test_aliases_do_not_shadow_commands() -> None:
    import typer.main

    from pypi_cli.__main__ import ALIAS_MAPPING, app

    click_app = typer.main.get_command(app)
    assert not set(ALIAS_MAPPING) & set(click_app.commands), "An alias shadows a real command name"


def test_alias_resolves_to_regex_search(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi s --help")
    output: str = result.stdout.decode("utf-8")
    assert "regular expression" in output.lower()


def test_alias_resolves_to_information(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi i --help")
    output: str = result.stdout.decode("utf-8")
    assert "information" in output


def test_alias_resolves_to_releases(runner: type[CommandRunner]) -> None:
    result = runner.run("pypi rel --help")
    output: str = result.stdout.decode("utf-8")
    assert "releases" in output


def test_invalid_repository_is_rejected(runner: type[CommandRunner]) -> None:
    result = runner.run_raw("pypi --repository not_a_url version")
    assert result.returncode == 2
    output: str = (result.stdout + result.stderr).decode("utf-8")
    assert "Invalid repository" in output


def test_invalid_timeout_is_rejected(runner: type[CommandRunner]) -> None:
    result = runner.run_raw("pypi --timeout 0.001 version")
    assert result.returncode == 2
    output: str = (result.stdout + result.stderr).decode("utf-8")
    assert "--timeout" in output
