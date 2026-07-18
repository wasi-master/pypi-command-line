"""The main file."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable

from datetime import datetime
from urllib.parse import quote

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme
from typer import Argument, Option
from typer.models import CommandFunctionType
from typer.core import TyperCommand as Command, TyperGroup as Group

try:
    import rich_click as click
except ImportError:
    import click

try:
    import ujson as json
except ImportError:
    import json  # type: ignore[no-redef]
else:
    json.JSONDecodeError = ValueError  # type: ignore[misc,assignment]

if TYPE_CHECKING:
    from collections.abc import Iterator
    from concurrent.futures import Future
    from urllib.parse import ParseResult
    from datetime import tzinfo as _TzInfo
    from types import ModuleType
    from typing import IO

    from bs4.element import Tag
    from packaging.requirements import Requirement
    from packaging.specifiers import SpecifierSet
    from requests import Response, Session

base_url: str = "https://pypi.org"

logger: logging.Logger = logging.getLogger("pypi_cli")

DEFAULT_TIMEOUT: float = 15.0
_timeout: float = DEFAULT_TIMEOUT

DEFAULT_HEADERS: dict[str, str] = {"User-Agent": "wasi_master/pypi_cli", "Accept": "application/json"}


def _is_interactive() -> bool:
    """Return True when both stdin and stdout are attached to a TTY."""
    import sys  # pylint: disable=import-outside-toplevel

    return sys.stdin.isatty() and sys.stdout.isatty()


def _github_headers() -> dict[str, str]:
    """Headers for GitHub API requests, including auth when GITHUB_TOKEN is set."""
    import os  # pylint: disable=import-outside-toplevel

    token: str | None = os.environ.get("GITHUB_TOKEN")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def get_cache_dir() -> str:
    """Return (and create) the user cache directory for pypi-command-line."""
    import os  # pylint: disable=import-outside-toplevel

    try:
        from platformdirs import user_cache_dir  # pylint: disable=import-outside-toplevel

        cache_dir: str = user_cache_dir("pypi-command-line")
    except ImportError:
        cache_dir = os.path.join(os.path.dirname(__file__), "cache")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def _with_default_timeout(session_obj: Session) -> Session:
    """Make every request on the session use the configured timeout unless one is given."""
    original_request: Callable[..., Response] = session_obj.request

    def request(method: str, url: str, **kwargs: Any) -> Response:
        kwargs.setdefault("timeout", _timeout)
        return original_request(method, url, **kwargs)

    session_obj.request = request
    return session_obj


def _make_plain_session() -> Session:
    """Create a non-caching requests session with the default headers and timeout."""
    from requests import Session  # pylint: disable=import-outside-toplevel

    plain_session: Session = Session()
    plain_session.headers.update(DEFAULT_HEADERS)
    return _with_default_timeout(plain_session)


session: Session

try:
    from requests_cache.session import CachedSession
except ImportError:
    session = _make_plain_session()
else:
    import os.path  # pylint: disable=import-outside-toplevel

    cache_path: str = os.path.join(get_cache_dir(), "requests")
    session = _with_default_timeout(
        CachedSession(
            cache_path,
            backend="sqlite",
            urls_expire_after={
                **dict.fromkeys(
                    [f"{base_url}/simple", f"{base_url}/stats", "https://api.github.com/repos/*/readme"], 86400
                ),
                f"{base_url}/pypi": 10800,
                f"{base_url}/search": 3600,
                f"{base_url}/rss": 60,
                "https://pypistats.org/api/packages/": 21600,
                "https://img.shields.io": 30,
            },
            headers=DEFAULT_HEADERS,
            cache_control=True,
        )
    )

try:
    import lxml
except ImportError:
    lxml = None


def __color_error_message() -> None:
    """Override click.UsageError.show to show colored output"""
    from click._compat import get_text_stderr  # pylint: disable=import-outside-toplevel
    from rich.markup import escape  # pylint: disable=import-outside-toplevel

    def show(self: click.exceptions.UsageError, file: IO[Any] | None = None) -> None:
        if file is None:
            file = get_text_stderr()
        hint: str = ""
        if self.ctx is not None and self.ctx.command.get_help_option(self.ctx) is not None:
            hint = f"[magenta]Try '[blue]{self.ctx.command_path} [bold]{self.ctx.help_option_names[-1]}[/bold][/blue]' or visit [cyan]https://wasi-master.github.io/pypi-command-line/usage#{self.ctx.command.name.replace('-', '')}[/cyan] for help.[/magenta]"
            hint = f"{hint}\n"
        if self.ctx is not None:
            console.print("[yellow]:disappointed_relieved: You did not do this properly[/]")
            console.print(
                f"{(self.ctx.get_usage().replace('...', '').replace('Usage: ', '[green]Usage: [/]').replace('[OPTIONS]', '[bright_black]'+ escape('[OPTIONS…]') + '[/]').replace('[ARGS]', '[bright_black]'+ escape('[ARGS…]') + '[/]'))}\n{hint}"
            )
        console.print(f":exclamation: [bold][red]Error[/bold]: {self.format_message()}[/red]")
        try:
            import questionary  # pylint: disable=import-outside-toplevel
            from questionary import Choice, Style  # pylint: disable=import-outside-toplevel
        except ImportError:
            pass
        else:
            if not _is_interactive():
                return
            style: Style = Style([("link", "cyan"), ("command", "blue"), ("cancel", "gray")])
            print("\n")
            resp: int | None = questionary.select(
                "What do you want to do",
                choices=[
                    Choice(
                        [
                            ("class:text", "Run '"),
                            ("class:command", f"{self.ctx.command_path} {self.ctx.help_option_names[-1]}"),
                            ("class:text", "'"),
                        ],
                        value=0,
                    ),
                    Choice(
                        [
                            ("class:text", "Open "),
                            (
                                "class:link",
                                f"https://wasi-master.github.io/pypi-command-line/usage#{self.ctx.command.name.replace('-', '')}",
                            ),
                        ],
                        value=1,
                    ),
                    Choice([("class:cancel", "Nothing")], value=2),
                ],
                use_shortcuts=True,
                style=style,
            ).ask()
            if resp == 0:
                console.print(f"[blue]❯ [/]{self.ctx.command_path} {self.ctx.help_option_names[-1]}")

                print(self.ctx.get_help())
            elif resp == 1:
                import webbrowser  # pylint: disable=import-outside-toplevel

                webbrowser.open(
                    f"https://wasi-master.github.io/pypi-command-line/usage#{self.ctx.command.name.replace('-', '')}"
                )
            else:
                raise typer.Exit()

    click.exceptions.UsageError.show = show

# Aliases for each command. Also rendered in the documentation's "Aliases" sections.
COMMAND_ALIASES: dict[str, list[str]] = {
    "browse": ["b"],
    "cache-clear": ["cc"],
    "cache-info": ["ci"],
    "cache-refresh": ["cr"],
    "check": ["chk"],
    "compare": ["c", "cmp"],
    "dependencies": ["d", "dep", "deps", "tree"],
    "description": ["desc", "readme"],
    "information": ["i", "info", "show"],
    "largest-files": ["lf"],
    "new-packages": ["np"],
    "new-releases": ["nr"],
    "read-the-docs": ["rtd", "docs", "documentation"],
    "regex-search": ["rs", "rsearch", "s"],
    "releases": ["rel"],
    "version": ["v", "ver"],
    "vulnerabilities": ["vuln", "vulns"],
    "wheels": ["w", "whl"],
}
ALIAS_MAPPING: dict[str, str] = {alias: command for command, aliases in COMMAND_ALIASES.items() for alias in aliases}


class AliasedGroup(Group):
    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        rv: click.Command | None = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        if cmd_name in ALIAS_MAPPING:
            return click.Group.get_command(self, ctx, ALIAS_MAPPING[cmd_name])
        commands: list[str] = self.list_commands(ctx)
        matches: list[str] = [x for x in commands if x.startswith(cmd_name)]
        if not matches:
            processor: Callable[[str], str] = lambda x: x.replace("-", "").lower()
            get_closest_match: Callable[[str], list[str]]
            try:
                import rapidfuzz  # pylint: disable=import-outside-toplevel

                get_closest_match = lambda cmd: [
                    i[0]
                    for i in rapidfuzz.process.extract(
                        cmd, commands, scorer=rapidfuzz.fuzz.WRatio, score_cutoff=50, processor=processor, limit=5
                    )
                ]
            except ImportError:
                try:
                    import warnings  # pylint: disable=import-outside-toplevel

                    # thefuzz emits a UserWarning at import time when its fast
                    # Levenshtein backend is missing; record it without leaking
                    # a global warning filter into the rest of the process.
                    with warnings.catch_warnings(record=True) as caught_warnings:
                        warnings.simplefilter("always")
                        import thefuzz.fuzz  # pylint: disable=import-outside-toplevel
                        import thefuzz.process  # pylint: disable=import-outside-toplevel
                    if any(issubclass(w.category, UserWarning) for w in caught_warnings):
                        console.print(
                            "[yellow]WARNING:[/] Using slow [red]thefuzz[/] and [red]difflib.SequenceMatcher[/]. "
                            "Consider installing [red]rapidfuzz[/] or [red]python-Levenshtein[/]"
                        )
                    get_closest_match = lambda cmd: [
                        i[0]
                        for i in thefuzz.process.extractBests(
                            cmd, commands, score_cutoff=50, processor=processor, limit=5
                        )
                    ]
                except ImportError:
                    import difflib  # pylint: disable=import-outside-toplevel

                    get_closest_match = lambda cmd: difflib.get_close_matches(cmd, commands, n=5, cutoff=0.5)
        if len(matches) == 0:
            closest_matches: list[str] = get_closest_match(cmd_name)
            if not closest_matches:
                # No match is more than 50% similar to the used name
                return None

            try:
                import questionary  # pylint: disable=import-outside-toplevel
            except ImportError:
                questionary = None  # type: ignore[assignment]
            if questionary is None or not _is_interactive():
                console.print(
                    f"""[cyan]ℹ️ Info:[/] Found invalid command '{cmd_name}', did you mean any of these: {', '.join(f"'[red]{match}[/]'" for match in closest_matches)}"""
                )
                raise typer.Exit()
            else:
                console.print(
                    f"""[cyan]ℹ️ Info:[/] Found invalid command '{cmd_name}', closest matches: {', '.join(f"'[red]{match}[/]'" for match in closest_matches)}"""
                )
                resp: str | None = questionary.select(
                    "Which one did you want to run?",
                    choices=closest_matches,
                    style=questionary.Style([("text", "red"), ("highlighted", "bg:ansibrightred")]),
                ).ask()

            if not resp:
                raise typer.Exit()
            return click.Group.get_command(self, ctx, resp)
        elif len(matches) == 1:
            console.print(f"[cyan]ℹ️ Info:[/] Found shortened name '{cmd_name}', using '{matches[0]}'")
            return click.Group.get_command(self, ctx, matches[0])
        formatted_matches: str = ", ".join(sorted(f"[red]{match}[/]" for match in matches))
        try:
            import questionary
        except ImportError:
            questionary = None  # type: ignore[assignment]
        if questionary is None or not _is_interactive():
            ctx.fail(f"Found Too many matches for '{cmd_name}': {formatted_matches}")
        else:
            import difflib  # pylint: disable=import-outside-toplevel

            console.print(f"[red]:warning: Attention:[/] Found Too many matches for '{cmd_name}': {formatted_matches}")
            command: str | None = questionary.select(
                "Select one to continue",
                choices=difflib.get_close_matches(cmd_name, matches, cutoff=0.0),
                style=questionary.Style([("text", "red"), ("highlighted", "bg:ansibrightred")]),
            ).ask()
            if not command:
                raise typer.Exit()
            return click.Group.get_command(self, ctx, command)
        return None

    def resolve_command(self, ctx: click.Context, args: list[str]) -> tuple[str | None, click.Command, list[str]]:
        # always return the full command name
        _, cmd, args = super().resolve_command(ctx, args)
        assert cmd is not None
        return cmd.name, cmd, args


class PypiTyper(typer.Typer):
    """A custom subclassed version of typer.Typer to allow rich help."""

    def __init__(
        self,
        *args: Any,
        cls: type[Group] = AliasedGroup,
        **kwargs: Any,
    ) -> None:
        """Initialise with a RichGroup class as the default."""
        super().__init__(*args, cls=cls, **kwargs)

    def command(  # type: ignore[override]
        self,
        *args: Any,
        cls: type[Command] = Command,
        **kwargs: Any,
    ) -> Callable[[CommandFunctionType], CommandFunctionType]:
        return super().command(*args, cls=cls, **kwargs)



# We instantiate a custom typer app
app: PypiTyper = PypiTyper()
console: Console = Console(
    theme=Theme(
        {
            "markdown.link": "#6088ff",
            "wheel.distribution": "#92EC5A",
            "wheel.version": "#F2C259",
            "wheel.build_tag": "#FF7F30",
            "wheel.python_tag": "#FF6EF8",
            "wheel.abi_tag": "#9263FB",
            "wheel.platform_tag": "#33F1C8",
            "wheel.file_extension": "#4AA0FC",

            "requirement.name": "#92EC5A",
            "requirement.extras": "#9263FB",
            "requirement.url": "#4AA0FC",
            "requirement.versionspec": "#33F1C8",
            "requirement.marker": "#F2C259",
        }
    ),
    emoji=True,
    emoji_variant="emoji",
    tab_size=4,
)
__color_error_message()  # makes the error messages colored


class Package:
    """Represents a package gotten from scraping the search results."""

    __slots__ = ("name", "date", "released", "description")

    name: str
    date: str
    released: datetime
    description: str

    def __init__(self, soup: Tag) -> None:
        """Instantiate a package object gotten from scraping the search results.

        Parameters
        ----------
        soup : bs4.BeautifulSoup
            The soup that was gotten from PyPI
        """
        name_el: Any = soup.find(class_="package-snippet__name")
        self.name = name_el.get_text()
        time: Any = soup.find(class_="package-snippet__created")
        self.date = time.get_text().strip()
        self.released = datetime.strptime(time.find("time")["datetime"][:-5], "%Y-%m-%dT%H:%M:%S")
        description_el: Any = soup.find(class_="package-snippet__description")
        self.description = description_el.get_text()

def utc_to_local(utc_dt: datetime, tzinfo: _TzInfo) -> datetime:
    """Convert a datetime from utc to local time."""
    return utc_dt.replace(tzinfo=tzinfo).astimezone(tz=None).replace(tzinfo=None)


def _parse_iso_datetime(dt_str: str) -> datetime:
    """Parse ISO 8601 datetime string from PyPI."""
    if dt_str.endswith("Z"):
        dt_str = dt_str[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(dt_str)
    except ValueError:
        try:
            return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ")


def remove_dot_git(text: str) -> str:
    """Remove the .git suffix from a URL."""
    if text.endswith(".git"):
        return text[:-4]
    return text


GITHUB_REPO_RE: str = r"https://(?:www\.)?github\.com/(?P<repo>[A-Za-z0-9_.-]{0,38}/[A-Za-z0-9_.-]{0,100})(?:\.git)?"


def find_github_repos(info: dict[str, Any]) -> list[str]:
    """Find GitHub repositories mentioned in package metadata, preferring project_urls.

    Returns a deduplicated list of "owner/repo" strings in order of appearance.
    """
    import re  # pylint: disable=import-outside-toplevel

    repos: list[str] = re.findall(GITHUB_REPO_RE, str(info))
    if len(repos) > 1 and info.get("project_urls"):
        repos = re.findall(GITHUB_REPO_RE, str(info["project_urls"]))
    return list(dict.fromkeys(remove_dot_git(repo) for repo in repos))


def fetch_pypi_json(package_name: str, version: str | None = None) -> dict[str, Any]:
    """Fetch a package's JSON metadata from the index, exiting with an error message on failure."""
    import requests  # pylint: disable=import-outside-toplevel

    url: str = f"{base_url}/pypi/{quote(package_name)}{f'/{quote(version)}' if version else ''}/json"
    try:
        with console.status("Getting data from PyPI"):
            response: Response = session.get(url)
    except requests.exceptions.RequestException as exc:
        logger.debug("Request to %s failed", url, exc_info=True)
        console.print(f"[red]:x: Network error while contacting {base_url}: {exc}[/]")
        raise typer.Exit(code=1)

    if response.status_code != 200:
        if response.status_code == 404:
            console.print(f"[red]:no_entry_sign: Project [green]{package_name}[/] not found[/]")
        else:
            console.print(f"[orange1]:grey_exclamation: Some error occurred. response code {response.status_code}[/]")
        raise typer.Exit(code=1)
    return json.loads(response.text)


def poetry_spec_to_req_str(pkg_name: str, version_spec: str) -> str:
    """Convert a poetry-style version spec (with ^ or ~) to a PEP 508 requirement string."""
    if not version_spec or version_spec == "*":
        return pkg_name
    if version_spec[0] in ("^", "~"):
        v: str = version_spec[1:]
        parts: list[str] = v.split(".")
        upper: str
        if version_spec[0] == "^":
            if parts[0] == "0" and len(parts) > 1:
                upper = f"0.{int(parts[1]) + 1}.0"
            else:
                upper = f"{int(parts[0]) + 1}.0.0"
        else:
            if len(parts) > 1:
                upper = f"{parts[0]}.{int(parts[1]) + 1}.0"
            else:
                upper = f"{int(parts[0]) + 1}.0.0"
        return f"{pkg_name}>={v},<{upper}"
    if version_spec[0].isdigit():
        return f"{pkg_name}=={version_spec}"
    return f"{pkg_name}{version_spec}"


def is_wheel_supported(wheel: dict[str, Any]) -> bool:
    """Check whether a wheel file (a PyPI "urls" entry) is installable on the current platform."""
    from packaging.tags import parse_tag, sys_tags  # pylint: disable=import-outside-toplevel
    from wheel_filename import InvalidFilenameError, parse_wheel_filename  # pylint: disable=import-outside-toplevel

    try:
        parsed_wheel_file = parse_wheel_filename(wheel["filename"])
    except InvalidFilenameError:
        return True
    for tag in parsed_wheel_file.tag_triples():
        if any(tag in sys_tags() for tag in list(parse_tag(tag))):
            return True
    return False


def _format_classifiers(_classifiers: str) -> str:
    """Format classifiers gotten from the API."""
    from collections import defaultdict
    classifier_dict: defaultdict[str, list[str]] = defaultdict(list)
    for classifier in _classifiers.splitlines():
        topic, content = map(str.strip, classifier.split("::", 1))
        classifier_dict[topic].append(content)
    return "".join(
        f"[bold]{topic}[/]\n" + "".join(f"  {c}\n" for c in contents)
        for topic, contents in classifier_dict.items()
    )


def get_latest_version() -> str | None:
    """Return the latest released version of pypi-command-line, or None on failure."""
    try:
        r: Response = session.get("https://pypi.org/pypi/pypi-command-line/json")
        if r.status_code != 200:
            return None
        return json.loads(r.text)["info"]["version"]
    except Exception:  # pylint: disable=broad-except
        logger.debug("Failed to fetch the latest version from PyPI", exc_info=True)
        return None


def _get_installed_version(package_name: str) -> str | None:
    """Return the locally installed version of a package, or None if not installed."""
    from importlib.metadata import PackageNotFoundError  # pylint: disable=import-outside-toplevel
    from importlib.metadata import version as _installed_version  # pylint: disable=import-outside-toplevel

    try:
        return _installed_version(package_name)
    except PackageNotFoundError:
        return None
    except Exception:  # pylint: disable=broad-except
        logger.debug("Failed to get installed version for %s", package_name, exc_info=True)
        return None


def load_cache() -> list[str]:
    import os  # pylint: disable=import-outside-toplevel

    cache_file: str = os.path.join(get_cache_dir(), "packages.txt")

    try:
        last_refreshed: float = os.path.getmtime(cache_file)
    except FileNotFoundError:
        return fill_cache(msg="Generating cache")
    else:
        import time  # pylint: disable=import-outside-toplevel

        if time.time() - last_refreshed > 86400:
            return fill_cache(msg="Cache is too old (>1d). Refreshing cache")
        with open(cache_file, "r", encoding="utf-8") as f:
            return f.read().splitlines()


def fill_cache(msg: str = "Fetching cache") -> list[str]:
    """Fill the cache with the packages."""
    import os  # pylint: disable=import-outside-toplevel

    import requests  # pylint: disable=import-outside-toplevel
    from rich.progress import Progress  # pylint: disable=import-outside-toplevel

    all_packages_url: str = f"{base_url}/simple/"
    cache_file: str = os.path.join(get_cache_dir(), "packages.txt")

    # Prefer the PyPI Simple JSON API (PEP 691): smaller payload and a stable
    # format. Indexes that don't support it fall back to the legacy HTML.
    headers: dict[str, str] = {**DEFAULT_HEADERS, "Accept": "application/vnd.pypi.simple.v1+json"}
    chunks: list[bytes] = []
    response_data: str
    try:
        with Progress(transient=True) as progress:
            response = requests.get(all_packages_url, stream=True, timeout=_timeout, headers=headers)
            response.raise_for_status()
            content_length: str | None = response.headers.get("content-length")
            if content_length is not None:
                total_length: int = int(content_length)
                task = progress.add_task(msg, total=total_length)
                for data in response.iter_content(chunk_size=32768):
                    chunks.append(data)
                    progress.advance(task, len(data))
                response_data = b"".join(chunks).decode("utf-8")
            else:
                response_data = response.content.decode("utf-8")
    except requests.exceptions.RequestException as exc:
        logger.debug("Failed to fetch the package list", exc_info=True)
        console.print(f"[red]:x: Failed to fetch the package list from {all_packages_url}: {exc}[/]")
        raise typer.Exit(code=1)

    packages: list[str] | None = None
    if "json" in response.headers.get("content-type", ""):
        try:
            packages = [project["name"] for project in json.loads(response_data)["projects"]]
        except (json.JSONDecodeError, KeyError, TypeError):
            logger.debug("Failed to parse simple index JSON, falling back to HTML", exc_info=True)
            packages = None
    if packages is None:
        import re  # pylint: disable=import-outside-toplevel

        packages = re.findall(r"<a[^>]*>([^<]+)<\/a>", response_data)
    # Write atomically so an interrupted refresh can't leave a truncated cache
    temp_file: str = cache_file + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write("\n".join(packages))
    os.replace(temp_file, cache_file)
    return packages



def fetch_comparison_data(package_name: str) -> dict[str, str] | None:
    if not package_name:
        return None

    # Parse version if present
    version: str | None = None
    if "==" in package_name:
        package_name, _, version = package_name.partition("==")

    url: str = f"{base_url}/pypi/{quote(package_name)}{f'/{quote(version)}' if version else ''}/json"
    try:
        response: Response = session.get(url)
        if response.status_code != 200:
            return {
                "name": package_name,
                "version": "[red]Not Found[/]" if response.status_code == 404 else f"[red]Error {response.status_code}[/]",
                "release_date": "N/A",
                "stars": "N/A",
                "open_issues": "N/A",
                "downloads": "N/A",
                "python_version": "N/A",
            }
        parsed_data: dict[str, Any] = json.loads(response.text)
    except Exception as e:
        return {
            "name": package_name,
            "version": f"[red]Error: {str(e)}[/]",
            "release_date": "N/A",
            "stars": "N/A",
            "open_issues": "N/A",
            "downloads": "N/A",
            "python_version": "N/A",
        }

    info: dict[str, Any] = parsed_data.get("info", {})
    releases: dict[str, list[dict[str, Any]]] = parsed_data.get("releases", {})
    urls: list[dict[str, Any]] = parsed_data.get("urls", [])

    latest_version: str = info.get("version", "Unknown")

    # Extract release date
    release_date: str = "Unknown"
    from datetime import timezone  # pylint: disable=import-outside-toplevel
    try:
        release_time: datetime
        if urls:
            release_time = utc_to_local(
                _parse_iso_datetime(urls[-1]["upload_time_iso_8601"]), timezone.utc
            )
            release_date = release_time.strftime("%b %d, %Y")
        elif latest_version in releases and releases[latest_version]:
            release_time = utc_to_local(
                _parse_iso_datetime(releases[latest_version][0]["upload_time_iso_8601"]), timezone.utc
            )
            release_date = release_time.strftime("%b %d, %Y")
    except Exception:
        logger.debug("Failed to determine release date for %s", package_name, exc_info=True)

    # Extract Python version support
    python_version: str = info.get("requires_python") or "Unknown"

    # Extract GitHub repo URL
    repos: list[str] = find_github_repos(info)
    repo: str | None = repos[0] if repos else None

    stars: str = "N/A"
    open_issues: str = "N/A"
    if repo:
        github_url: str = f"https://api.github.com/repos/{quote(repo)}"
        try:
            resp: Response = session.get(github_url, headers=_github_headers())
            if resp.status_code == 200:
                github_data: dict[str, Any] = json.loads(resp.text)
                if not (github_data.get("message") and github_data["message"] == "Not Found"):
                    stars_val: int | None = github_data.get("stargazers_count")
                    issues_val: int | None = github_data.get("open_issues")
                    if stars_val is not None:
                        stars = f"{stars_val:,}"
                    if issues_val is not None:
                        open_issues = f"{issues_val:,}"
        except Exception:
            logger.debug("Failed to fetch GitHub data for %s", repo, exc_info=True)

    # Extract monthly downloads from pypistats
    downloads: str = "N/A"
    stats_url: str = f"https://pypistats.org/api/packages/{quote(package_name)}/recent"
    try:
        r: Response = session.get(stats_url)
        if r.status_code == 200:
            parsed_stats: Any = json.loads(r.text)
            if isinstance(parsed_stats, dict) and "data" in parsed_stats:
                last_month_downloads: int | None = parsed_stats["data"].get("last_month")
                if last_month_downloads is not None:
                    downloads = f"{last_month_downloads:,}"
    except Exception:
        logger.debug("Failed to fetch download stats for %s", package_name, exc_info=True)

    return {
        "name": info.get("name", package_name),
        "version": latest_version,
        "release_date": release_date,
        "stars": stars,
        "open_issues": open_issues,
        "downloads": downloads,
        "python_version": python_version,
    }


def parse_requirements_txt(content: str) -> list[Requirement]:
    packages: list[Requirement] = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        if " #" in line:
            line = line.split(" #", 1)[0].strip()
        parts: list[str] = []
        for part in line.split():
            if part.startswith("--"):
                break
            parts.append(part)
        line = " ".join(parts).strip()
        if not line:
            continue
        try:
            from packaging.requirements import Requirement
            req = Requirement(line)
            if req.marker and not req.marker.evaluate():
                continue
            packages.append(req)
        except Exception:
            logger.debug("Skipping unparseable requirement line: %r", line, exc_info=True)
    return packages


def parse_pyproject_toml(content: str) -> list[Requirement]:
    tomllib: ModuleType | None = None
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ImportError:
            try:
                import toml as tomllib  # type: ignore[no-redef]
            except ImportError:
                pass

    if tomllib is None:
        return _fallback_parse_pyproject(content)

    try:
        data: dict[str, Any] = tomllib.loads(content)
    except Exception:
        logger.debug("Failed to parse pyproject.toml content", exc_info=True)
        return []

    packages: list[Requirement] = []
    project: dict[str, Any] = data.get("project", {})
    dependencies: list[str] = project.get("dependencies", [])
    for dep in dependencies:
        try:
            from packaging.requirements import Requirement
            packages.append(Requirement(dep))
        except Exception:
            logger.debug("Skipping unparseable dependency: %r", dep, exc_info=True)

    optional_dependencies: dict[str, list[str]] = project.get("optional-dependencies", {})
    for group, deps in optional_dependencies.items():
        for dep in deps:
            try:
                from packaging.requirements import Requirement
                packages.append(Requirement(dep))
            except Exception:
                logger.debug("Skipping unparseable dependency: %r", dep, exc_info=True)

    tool: dict[str, Any] = data.get("tool", {})
    poetry: dict[str, Any] = tool.get("poetry", {})

    poetry_deps: list[dict[str, Any]] = []
    if "dependencies" in poetry:
        poetry_deps.append(poetry["dependencies"])

    group_data: dict[str, Any] = poetry.get("group", {})
    for group_name, group_val in group_data.items():
        if "dependencies" in group_val:
            poetry_deps.append(group_val["dependencies"])

    for dep_dict in poetry_deps:
        for pkg_name, val in dep_dict.items():
            if pkg_name.lower() == "python":
                continue
            version_spec: str
            if isinstance(val, dict):
                version_spec = val.get("version", "")
            else:
                version_spec = val

            req_str: str = poetry_spec_to_req_str(pkg_name, version_spec)
            try:
                from packaging.requirements import Requirement
                packages.append(Requirement(req_str))
            except Exception:
                logger.debug("Skipping unparseable dependency: %r", req_str, exc_info=True)

    return packages


def _fallback_parse_pyproject(content: str) -> list[Requirement]:
    packages: list[Requirement] = []
    lines: list[str] = content.splitlines()
    in_dependencies: bool = False
    in_poetry_dependencies: bool = False
    current_section: str = ""
    for line in lines:
        line_stripped: str = line.strip()
        if not line_stripped or line_stripped.startswith("#"):
            continue

        if line_stripped.startswith("[") and line_stripped.endswith("]"):
            current_section = line_stripped[1:-1].strip()
            in_dependencies = (current_section == "project" or current_section == "project.optional-dependencies")
            in_poetry_dependencies = ("tool.poetry.dependencies" in current_section or "tool.poetry.group" in current_section)
            continue

        if current_section == "project":
            if "dependencies" in line_stripped and "=" in line_stripped:
                in_dependencies = True
                continue

        if in_dependencies:
            import re
            match = re.search(r'["\']([^"\']+)["\']', line_stripped)
            if match:
                req_str = match.group(1)
                try:
                    from packaging.requirements import Requirement
                    packages.append(Requirement(req_str))
                except Exception:
                    logger.debug("Skipping unparseable dependency: %r", req_str, exc_info=True)
            if "]" in line_stripped and not "[" in line_stripped:
                if current_section == "project":
                    in_dependencies = False
            continue

        if in_poetry_dependencies:
            if "=" in line_stripped:
                parts: list[str] = line_stripped.split("=", 1)
                pkg_name: str = parts[0].strip().strip('"\'')
                if pkg_name.lower() == "python":
                    continue
                val: str = parts[1].strip()
                import re
                ver_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', val)
                if ver_match:
                    version_spec = ver_match.group(1)
                else:
                    str_match = re.search(r'^["\']([^"\']+)["\']', val)
                    version_spec = str_match.group(1) if str_match else ""

                req_str = poetry_spec_to_req_str(pkg_name, version_spec)
                try:
                    from packaging.requirements import Requirement
                    packages.append(Requirement(req_str))
                except Exception:
                    logger.debug("Skipping unparseable dependency: %r", req_str, exc_info=True)
    return packages



def _refresh_cache() -> None:
    with console.status("Getting current cache"):
        old_cache: list[str] = load_cache()
    new_cache: list[str] = fill_cache(msg="Fetching new cache")
    changed: int = len(new_cache) - len(old_cache)
    console.print(f"[yellow]:repeat: Updated the cache, number of new packages till last refresh:[/] [red]{changed}[/]")


def _clear_cache() -> None:
    try:
        session.cache.clear()
    except AttributeError:
        pass
    else:
        console.print(f"[cyan]ℹ️ Info:[/] Emptied cache, now trying to delete the cache file")

    import os
    from contextlib import nullcontext

    folder: str = get_cache_dir()
    for filename in os.listdir(folder):
        file_path: str = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path):
                disable_cache = session.cache_disabled() if hasattr(session, "cache_disabled") else nullcontext()
                with disable_cache:
                    os.remove(file_path)
        except Exception as exc:
            console.print(f"[red]:x: Failed to delete {file_path}. Reason: {exc}[/]")


def _get_github_readme(repo: str) -> tuple[str, str] | tuple[None, None]:
    readme: dict[str, Any] = session.get(f"https://api.github.com/repos/{repo}/readme", headers=_github_headers()).json()
    if readme.get("message") == "Not Found":
        console.print(f"[red]:x: Could not find readme for[/] [yellow]{repo}[/]")
        raise typer.Exit()
    msg: str | None = readme.get("message")
    if msg is not None and "API rate limit exceeded" in msg:
        console.print(f"[red]:x: API rate limit exceeded for GitHub[/]")
        raise typer.Exit()
    # The readme API response points at the file on the repo's actual default
    # branch; building a raw URL by hand would wrongly assume it is "master".
    download_url: str | None = readme.get("download_url")
    if not download_url:
        return None, None
    content: Response = session.get(download_url)
    if content.status_code == 200:
        if "API rate limit exceeded" in content.text:
            console.print(f"[red]:x: API rate limit exceeded for GitHub[/]")
            raise typer.Exit()
        return content.text, readme["path"]
    return None, None


def _format_xml_packages(
    url: str, title: str, pubmsg: str, show_author: bool, hide_link: bool, *, split_title: bool = False
) -> None:
    try:
        import bs4  # pylint: disable=import-outside-toplevel
    except ImportError:
        bs4 = None  # type: ignore[assignment]
    table: Table = Table(title=title, show_lines=True)
    table.add_column("Index", style="magenta", header_style="bold magenta")
    table.add_column("Name", style="green", header_style="bold green")
    if show_author:
        table.add_column("Author", style="red", header_style="bold red")
    table.add_column("Description", style="white", header_style="bold white")
    if not hide_link:
        table.add_column("Link", style="cyan", header_style="bold blue")
    table.add_column(pubmsg, style="yellow", header_style="bold yellow")
    with console.status("Fetching packages"):
        response: Response = session.get(url)
    soup: Any
    if lxml and bs4:
        soup = bs4.BeautifulSoup(response.text, "lxml-xml")
    else:
        import xml.etree.ElementTree as ET  # pylint: disable=import-outside-toplevel

        soup = ET.fromstring(response.text)

    from datetime import timezone  # pylint: disable=import-outside-toplevel
    import humanize  # pylint: disable=import-outside-toplevel

    for index, package in enumerate(soup.find_all("item") if lxml else soup.iter("item"), 1):
        title = package.find("title").text
        if split_title:
            title = title.split()[0]
        author = package.find("author")
        description = package.find("description")
        link = package.find("link").text

        date: datetime = utc_to_local(datetime.strptime(package.find("pubDate").text, "%a, %d %b %Y %H:%M:%S GMT"), timezone.utc)

        row: list[str | None] = [f"{index}.", title]
        if show_author:
            row.append(author.text if author is not None else None)
        row.append(description.text if description is not None else "")
        if not hide_link:
            row.append(link)
        row.append(humanize.naturaltime(date))
        table.add_row(*row)
    console.print(table)
    if not lxml:
        console.print(
            "[bold yellow]:warning: WARNING: There is a known bug that occurs when lxml is not installed. It"
            "doesn't show descriptions in some cases. Please install lxml using `pip install lxml`."
        )


def _get_package_dependencies(info: dict[str, Any], requested_extras: set[str]) -> list[Requirement]:
    """Parse requires_dist from package info, filtering by markers and extras.

    Returns a list of packaging.requirements.Requirement objects that apply
    to the current environment and the requested extras.
    """
    from packaging.requirements import Requirement  # pylint: disable=import-outside-toplevel

    requires_dist: list[str] = info.get("requires_dist") or []
    deps: list[Requirement] = []
    for req_str in requires_dist:
        try:
            req: Requirement = Requirement(req_str)
        except Exception:
            logger.debug("Skipping unparseable requirement: %r", req_str, exc_info=True)
            continue
        if req.marker:
            # Only include if marker evaluates for current env + requested extras
            extra_envs: list[str | None] = [None] if not requested_extras else [None] + list(requested_extras)
            included: bool = False
            for extra in extra_envs:
                env: dict[str, str] = {"extra": extra} if extra else {}
                try:
                    if req.marker.evaluate(env):
                        included = True
                        break
                except Exception:
                    logger.debug("Failed to evaluate marker for %r", req_str, exc_info=True)
            if not included:
                continue
        deps.append(req)
    return deps



@app.command()
def description(
    package_name: str = Argument(..., help="Package to get the description for"),
    force_github: bool = Option(False, help="Forcefully get the description from github"),
    syntax_theme: str = Option("monokai", help="Override the default syntax highlighting theme"),
) -> None:
    """See the description for a package."""
    parsed_data: dict[str, Any] = fetch_pypi_json(package_name)["info"]
    if force_github:
        repos = find_github_repos(parsed_data)
        if len(repos) > 1:
            console.print("[red]:warning: WARNING:[/] I found multiple github repos. ")
            import questionary  # pylint: disable=import-outside-toplevel

            repo = questionary.select(
                "Please specify the repo you want to use.",
                choices=[questionary.Choice([("cyan", r)]) for r in repos],
            ).ask()
            if not repo:
                console.print("[dim gray]:ok: Cancelled![/]")
                raise typer.Exit()
        elif len(repos) == 1:
            repo = repos[0]
        else:
            console.print("[red]:x: I could not find a GitHub repository[/]")
            raise typer.Exit()
        readme, filename = _get_github_readme(repo)
        if not readme or not filename:
            console.print("[red]:x: I could not find a readme inside the GitHub repository[/]")
            raise typer.Exit()
        parsed_data["description"] = readme
        if filename.endswith((".md", ".md.txt")):
            parsed_data["description_content_type"] = "text/markdown"
        elif filename.endswith((".rst", ".rst.txt")):
            parsed_data["description_content_type"] = "text/x-rst"
        else:
            parsed_data["description_content_type"] = "text/markdown"
    if not parsed_data["description"] or parsed_data["description"] == "UNKNOWN":
        console.print("[red]:x: No description found on PyPI.[/]")
        repos = find_github_repos(parsed_data)
        if repos:
            if len(repos) == 1:
                repo = repos[0]
                console.print(f"[yellow]ℹ️ INFO:[/] However, I did find a github repo https://github.com/{repo}.\n")

                try:
                    import questionary  # pylint: disable=import-outside-toplevel
                except ImportError:
                    from rich.prompt import Confirm  # pylint: disable=import-outside-toplevel

                    resp = Confirm.ask("Do you want to get the description from there?")
                else:
                    resp = questionary.confirm("Do you want to get the description from there?").ask()

                if not resp:
                    console.print("[dim gray]:ok: Cancelled![/]")
                    raise typer.Exit()
            elif len(repos) > 1:
                console.print("[red]:warning: WARNING:[/] I did find some github repos. ")
                import questionary  # pylint: disable=import-outside-toplevel

                repo = questionary.select(
                    "Please specify the repo you want to see the description from (Ctrl+C to cancel).",
                    choices=[questionary.Choice([("cyan", r)]) for r in list(repos)],
                ).ask()
                if not repo:
                    console.print("[dim gray]:ok: Cancelled![/]")
                    raise typer.Exit()
            readme, filename = _get_github_readme(repo)
            if not readme or not filename:
                console.print("[red]:x: I could not find a readme inside the GitHub repository[/]")
                raise typer.Exit()
            parsed_data["description"] = readme
            if filename.endswith((".md", ".md.txt")):
                parsed_data["description_content_type"] = "text/markdown"
            elif filename.endswith((".rst", ".rst.txt")):
                parsed_data["description_content_type"] = "text/x-rst"
            else:
                parsed_data["description_content_type"] = "text/markdown"
        else:
            console.print(
                "[red]:x: The PyPI page doesn't have a description nor a GitHub repository that I could've used[/]"
            )
            raise typer.Exit()

    description: Any
    if parsed_data["description_content_type"] == "text/markdown":
        from rich.markdown import Markdown  # pylint: disable=import-outside-toplevel

        description = Markdown(parsed_data["description"], code_theme=syntax_theme)
    elif parsed_data["description_content_type"] == "text/x-rst":
        from rich_rst import RestructuredText  # pylint: disable=import-outside-toplevel

        description = RestructuredText(parsed_data["description"], code_theme=syntax_theme)
    else:
        from rich.text import Text  # pylint: disable=import-outside-toplevel

        description = Text(parsed_data["description"])
    console.print(Panel(description, title=f"Description for {package_name}", border_style="bold magenta"))


@app.command()
def new_packages(
    show_author: bool = Option(False, metavar="author", help="Show the project author or not"),
    hide_link: bool = Option(False, metavar="link", help="Show the project link or not"),
) -> None:
    """See the top 40 newly added packages."""
    _format_xml_packages(
        f"{base_url}/rss/packages.xml", "Newly Added Packages", "Published At", show_author, hide_link, split_title=True
    )


@app.command()
def new_releases(
    show_author: bool = Option(False, metavar="author", help="Show the project author or not"),
    hide_link: bool = Option(False, metavar="link", help="Show the project link or not"),
) -> None:
    """See the top 100 newly updated packages."""
    _format_xml_packages(
        f"{base_url}/rss/updates.xml", "Newly Released Packages", "Released At", show_author, hide_link
    )


@app.command()
def largest_files() -> None:
    """See the top 100 projects with the largest file size."""
    import humanize  # pylint: disable=import-outside-toplevel

    headers: dict[str, str] = {"User-Agent": "wasi_master/pypi_cli", "Accept": "application/json"}
    url: str = f"{base_url}/stats/"
    with console.status("Loading largest files..."):
        response: Response = session.get(url, headers=headers)
        data: dict[str, Any] = json.loads(response.text)
    packages: dict[str, dict[str, Any]] = data["top_packages"]
    packages = dict(sorted(packages.items(), key=lambda i: i[1]["size"], reverse=True))
    table: Table = Table(title="Top packages on PyPI based on their size", show_lines=True)
    table.add_column("Index", style="magenta", header_style="bold magenta")
    table.add_column("Package", style="green", header_style="bold green")
    table.add_column("Size", style="red", header_style="bold red")
    table.add_column("Link", style="cyan", header_style="bold blue")
    table.add_row(
        "-", "All Total", humanize.naturalsize(data["total_packages_size"], binary=True) + "\n", style="bold red"
    )
    for i, (name, project) in enumerate(packages.items(), 1):
        table.add_row(
            f"{i}.",
            f"[link={base_url}/project/{name}]{name}[/]",
            humanize.naturalsize(project["size"], binary=True),
            f"{base_url}/project/{name}",
        )
    console.print(table)


@app.command()
def search(
    package_name: str = Argument(..., help="The name of the package to search for"),
    page: int = Option(1, min=1, max=500, help="The page of the search results to show."),
    # classifier: List[str] = Option(
    #     None, help="Can be used multiple times to specify a list of classifiers to filter the results."
    # ),
) -> None:
    """Search for a package on PyPI. Currently not available"""
    console.print('[red]:warning: WARNING:[/] The search command is currently not available due to PyPI blocking the requests. Please use the [blue]rsearch[/] command instead.')
    raise typer.Exit()
    url = f"{base_url}/search/"
    parameters = {"q": package_name, "page": page}
    # if classifier:
    #     parameters["c"] = classifier
    with console.status(f"Searching for {package_name}..."):
        response = session.get(url, params=parameters)

    if response.status_code == 404:
        console.print("[bold:no_entry_sign: The specified page doesn't exist[/]")
        raise typer.Exit()

    with console.status("Parsing data..."):
        import bs4  # pylint: disable=import-outside-toplevel

        soup = bs4.BeautifulSoup(response.text, "lxml" if lxml else "html.parser")
        result_list = soup.find("h2", string="Search results", class_="sr-only")
        if not result_list:
            comment = soup.select(
                "div.split-layout.split-layout--table.split-layout--wrap-on-tablet > div:nth-child(1) > p"
            )
            console.print(f"[bold]{' '.join(comment[0].get_text().split())}[/]")
            raise typer.Exit()

        results: list[Package] = [Package(i) for i in result_list.find_all("a", class_="package-snippet")]

        pagination = soup.find(class_="button-group--pagination")
        amount_of_pages: int
        if not pagination:
            amount_of_pages = 1
        else:
            amount_of_pages = int(pagination.find_all(["span", "a"])[-2].get_text())

    table = Table(
        show_header=True,
        title=f"[bold]Search results for {package_name}[/]",
        show_lines=True,
        caption=f"Page {page} of {amount_of_pages}",
    )
    table.add_column("[purple]No.[/]", width=3, style="purple")
    # table.add_column("[white]Version[/]", style="bright_black")
    table.add_column("[green]Name[/]", justify="center", style="green")
    table.add_column("[yellow]Description[/]", justify="center", style="white")
    table.add_column("[cyan]Release date[/]", justify="right", style="cyan")

    for index, package in enumerate(results, 1):
        table.add_row(
            f"{index}.",
            # package.version,
            f"[link={base_url}/project/{package.name}]{package.name}[/]",
            package.description,
            package.date,
        )
    console.print(table)


@app.command()
def releases(
    package_name: str = Argument(
        ...,
        help="The name of package to show releases for",
    ),
    version: str = Option(None, help="Only show the release for this specific version"),
    show_links: bool = Option(False, metavar="link", help="Display the links to the releases"),
    json_output: bool = Option(False, "--json", help="Output the results as JSON instead of a table"),
) -> None:
    """See all the available releases for a package.

    The --link argument can be used to also show the link of the releases.
    This is turned off by default and the link is added as a hyperlink to the package name on supported terminals
    """
    if not version and "==" in package_name:
        package_name, _, version = package_name.partition("==")
    parsed_data: dict[str, Any] = fetch_pypi_json(package_name)
    import humanize  # pylint: disable=import-outside-toplevel

    all_releases: dict[str, list[dict[str, Any]]] = parsed_data["releases"]
    if version:
        if version not in all_releases:
            console.print(f"[red]:no_entry_sign: Version [green]{version}[/] not found for [green]{package_name}[/][/]")
            raise typer.Exit(code=1)
        all_releases = {version: all_releases[version]}

    if json_output:
        records: list[dict[str, Any]] = []
        for release_version, release_files in all_releases.items():
            release: dict[str, Any] | None = release_files[0] if release_files else None
            records.append(
                {
                    "version": release_version,
                    "upload_time": release["upload_time_iso_8601"] if release else None,
                    "size": release["size"] if release else None,
                    "url": release["url"] if release else None,
                }
            )
        print(json.dumps(records, indent=2))
        raise typer.Exit()

    table = Table()
    table.add_column("Version", style="green", header_style="green")
    table.add_column("Upload date", width=24, style="red", header_style="red")
    table.add_column("Size", style="yellow", header_style="yellow")
    if show_links is True:
        table.add_column("Link", style="cyan", header_style="blue")

    for release_version, release_files in all_releases.items():
        if not release_files:
            table.add_row(release_version)
            continue
        release = release_files[0]
        upload_time = _parse_iso_datetime(release["upload_time_iso_8601"])

        if show_links is True:
            table.add_row(
                f"[link={release['url']}] {release_version}[/]",
                upload_time.strftime("%c"),
                humanize.naturalsize(release["size"], binary=True),
                release["url"],
            )
        else:
            table.add_row(
                f"[link={release['url']}] {release_version}[/]",
                upload_time.strftime("%c"),
                humanize.naturalsize(release["size"], binary=True),
            )
    console.print(table)


@app.command()
def vulnerabilities(
    package_name: str = Argument(..., help="The name of the package to show vulnerabilities for"),
    version: str = Argument(
        None,
        help="The version of the package to show vulnerabilities for, defaults to latest, can be omitted if using package_name==version",
    ),
) -> None:
    """See all the known vulnerabilities for a package."""
    if not version and "==" in package_name:
        package_name, _, version = package_name.partition("==")
    parsed_data: dict[str, Any] = fetch_pypi_json(package_name, version)
    vulnerabilities: list[dict[str, Any]] = parsed_data.get("vulnerabilities") or []
    shown_version: str = version or parsed_data.get("info", {}).get("version", "latest")
    if not vulnerabilities:
        console.print(f"[green]:white_check_mark: No known vulnerabilities for {package_name} {shown_version}[/]")
        raise typer.Exit()
    table = Table(title=f"Known Vulnerabilities for {package_name}", show_lines=True)
    table.add_column("ID", style="red", header_style="bold red")
    table.add_column("Details", style="yellow", header_style="bold yellow")
    table.add_column("Aliases", style="magenta", header_style="bold magenta")
    table.add_column("Fixed in", style="green", header_style="bold green")
    for vulnerability in vulnerabilities:
        table.add_row(
            f"[link={vulnerability['link']}]{vulnerability['id']}[/]",
            vulnerability["details"],
            ", ".join(vulnerability["aliases"]) if vulnerability["aliases"] else "N/A",
            ", ".join(vulnerability["fixed_in"]) if vulnerability["fixed_in"] else "N/A",
        )
    console.print(table)

@app.command()
def wheels(
    package_name: str = Argument(..., help="The name of the package to show wheel info for"),
    version: str = Argument(
        None,
        help="The version of the package to show info for, defaults to latest, can be omitted if using package_name==version",
    ),
    supported_only: bool = Option(False, help="Only show wheels supported on the current platform"),
) -> None:
    """See detailed information about all the wheels of a release of a package"""
    if not version and "==" in package_name:
        package_name, _, version = package_name.partition("==")
    parsed_data: dict[str, Any] = fetch_pypi_json(package_name, version)

    from rich.text import Text  # pylint: disable=import-outside-toplevel
    import humanize  # pylint: disable=import-outside-toplevel

    data = parsed_data["urls"]

    from itertools import cycle  # pylint: disable=import-outside-toplevel

    colors: Iterator[str] = cycle(["green", "blue", "magenta", "cyan", "yellow", "red"])
    wheel_panels: list[Panel] = []
    if supported_only:
        data = filter(is_wheel_supported, data)
    from datetime import timezone  # pylint: disable=import-outside-toplevel

    for wheel in data:
        wheel_name = Text(wheel["filename"])
        # Maybe use the regex in https://github.com/jwodder/wheel-filename/blob/master/src/wheel_filename/__init__.py#L45-L53
        wheel_name.highlight_regex(
            r"^(?P<distribution>\w+)-(?P<version>[A-Za-z0-9\.\-]+)(?P<build_tag>-\w{0,3})?-(?P<python_tag>[a-z]{2}[0-9]{0,3})-(?P<abi_tag>\w+)-(?P<platform_tag>.+)(?P<file_extension>\.whl)$",
            style_prefix="wheel.",
        )
        wheel_panels.append(
            Panel(
                "\n".join(
                    filter(
                        None,
                        [
                            f"[blue]Comment:[/] {wheel['comment_text']}" if wheel["comment_text"] else None,
                            f"[magenta]Has Signature[/]: {wheel['has_sig']}",
                            f"[cyan]Package Type:[/] {wheel['packagetype']}",
                            f"[green]Requires Python:[/] {wheel['requires_python']}"
                            if not wheel["requires_python"] is None
                            else None,
                            f"[yellow]Size:[/] {humanize.naturalsize(wheel['size'], binary=True)}",
                            f"[bright_cyan]Yanked Reason[/]: {wheel['yanked_reason']}" if wheel["yanked"] else None,
                            f"[red]Upload Time[/]: {humanize.naturaltime(utc_to_local(_parse_iso_datetime(wheel['upload_time_iso_8601']), timezone.utc))}",
                        ],
                    )
                ),
                title=f"[white]{wheel_name}[/]" if not wheel_name.plain.endswith(".whl") else wheel_name,
                border_style=next(colors),
            )
        )
    from rich.columns import Columns  # pylint: disable=import-outside-toplevel

    console.print(Columns(wheel_panels))


@app.command()
def check(
    file_path: str = Argument(
        ...,
        help="The requirements.txt or pyproject.toml file to check",
    ),
    json_output: bool = Option(False, "--json", help="Output the results as JSON instead of a table"),
) -> None:
    """Check a requirements.txt or pyproject.toml file for updates, wheel support, and abandoned packages."""
    import os  # pylint: disable=import-outside-toplevel
    from datetime import timezone  # pylint: disable=import-outside-toplevel
    from concurrent.futures import ThreadPoolExecutor  # pylint: disable=import-outside-toplevel
    from packaging.version import parse as parse_version  # pylint: disable=import-outside-toplevel
    import humanize  # pylint: disable=import-outside-toplevel

    if not os.path.exists(file_path):
        console.print(f"[red]:no_entry_sign: File [green]{file_path}[/] not found[/]")
        raise typer.Exit(code=1)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content: str = f.read()
    except Exception as e:
        console.print(f"[red]:no_entry_sign: Failed to read [green]{file_path}[/]: {e}[/]")
        raise typer.Exit(code=1)

    requirements: list[Requirement]
    if file_path.endswith(".toml") or os.path.basename(file_path) == "pyproject.toml":
        requirements = parse_pyproject_toml(content)
    else:
        requirements = parse_requirements_txt(content)

    if not requirements:
        console.print("[yellow]:grey_exclamation: No requirements found to check.[/]")
        raise typer.Exit()

    seen: set[str] = set()
    deduped_requirements: list[Requirement] = []
    for req in requirements:
        name_lower: str = req.name.lower()
        if name_lower not in seen:
            seen.add(name_lower)
            deduped_requirements.append(req)

    def extract_version(specifier: SpecifierSet) -> str | None:
        for spec in specifier:
            if spec.operator in ("==", "===", "~="):
                return spec.version
        for spec in specifier:
            if spec.operator in (">=", ">", "<=", "<", "!="):
                return spec.version
        return None

    def fetch_package_info(req: Requirement) -> tuple[Requirement, dict[str, Any] | int | None]:
        url: str = f"{base_url}/pypi/{quote(req.name)}/json"
        try:
            res: Response = session.get(url)
            if res.status_code == 200:
                return req, json.loads(res.text)
            else:
                return req, res.status_code
        except Exception:
            return req, None

    results: list[tuple[Requirement, dict[str, Any] | int | None]] = []
    with console.status("Checking requirements against PyPI..."):
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures: list[Future[tuple[Requirement, dict[str, Any] | int | None]]] = [
                executor.submit(fetch_package_info, req) for req in deduped_requirements
            ]
            for future in futures:
                try:
                    results.append(future.result())
                except Exception:
                    logger.debug("Failed to check a requirement", exc_info=True)

    records: list[dict[str, Any]] = []
    for req, data in results:
        specified: str | None = extract_version(req.specifier)
        record: dict[str, Any] = {
            "name": req.name,
            "specified": str(req.specifier) if req.specifier else "*",
            "latest": None,
            "wheel_support": None,
            "last_updated": None,
            "abandoned": False,
            "outdated": False,
            "error": None,
            "_latest_dt": None,
        }

        if data is None or isinstance(data, int):
            record["error"] = "not_found" if data == 404 else "error"
            records.append(record)
            continue

        info: dict[str, Any] = data.get("info", {})
        record["latest"] = info.get("version", "Unknown")

        latest_dt: datetime | None = None
        for rel_list in data.get("releases", {}).values():
            for rel in rel_list:
                up_time = rel.get("upload_time_iso_8601")
                if up_time:
                    try:
                        dt = _parse_iso_datetime(up_time)
                        if latest_dt is None or dt > latest_dt:
                            latest_dt = dt
                    except Exception:
                        logger.debug("Failed to parse upload time %r for %s", up_time, req.name, exc_info=True)

        if latest_dt:
            if latest_dt.tzinfo is None:
                latest_dt = latest_dt.replace(tzinfo=timezone.utc)
            record["abandoned"] = (datetime.now(timezone.utc) - latest_dt).days > 730
            record["last_updated"] = latest_dt.isoformat()
            record["_latest_dt"] = latest_dt

        files: list[dict[str, Any]]
        if specified and specified in data.get("releases", {}):
            files = data["releases"][specified]
        else:
            files = data.get("urls", [])

        wheels: list[dict[str, Any]] = [f for f in files if f.get("packagetype") == "bdist_wheel" or f.get("filename", "").endswith(".whl")]
        if not wheels:
            record["wheel_support"] = "no_wheels"
        elif not any(is_wheel_supported(w) for w in wheels):
            record["wheel_support"] = "unsupported"
        else:
            record["wheel_support"] = "supported"

        if specified:
            try:
                record["outdated"] = parse_version(record["latest"]) > parse_version(specified)
            except Exception:
                logger.debug("Failed to compare versions for %s", req.name, exc_info=True)

        records.append(record)

    if json_output:
        for record in records:
            record.pop("_latest_dt", None)
        print(json.dumps(records, indent=2))
        raise typer.Exit()

    table = Table()
    table.add_column("Package", style="green", header_style="green")
    table.add_column("Specified", style="cyan", header_style="cyan")
    table.add_column("Latest", style="magenta", header_style="magenta")
    table.add_column("Wheel Support", header_style="yellow")
    table.add_column("Last Updated", header_style="blue")
    table.add_column("Status", header_style="red")

    wheel_labels: dict[str | None, str] = {
        "supported": "[green]Supported[/]",
        "no_wheels": "[yellow]No wheels[/]",
        "unsupported": "[red]Unsupported[/]",
        None: "N/A",
    }

    for record in records:
        if record["error"]:
            status_str: str = "[red]Not Found[/]" if record["error"] == "not_found" else "[orange1]Error[/]"
            table.add_row(record["name"], record["specified"], "N/A", "N/A", "N/A", status_str)
            continue

        status_parts: list[str] = []
        if record["abandoned"]:
            status_parts.append("[red][bold]Abandoned[/][/]")
        if record["outdated"]:
            status_parts.append("[yellow]Outdated[/]")
        if not status_parts:
            status_parts.append("[green]Up to date[/]")

        last_updated_str: str = "UNKNOWN"
        if record["_latest_dt"]:
            last_updated_str = humanize.naturaltime(utc_to_local(record["_latest_dt"], timezone.utc))

        table.add_row(
            record["name"],
            record["specified"],
            record["latest"],
            wheel_labels[record["wheel_support"]],
            last_updated_str,
            " & ".join(status_parts),
        )

    console.print(table)


@app.command()
def information(
    package_name: str = Argument(..., help="The name of the package to show information for"),
    version: str = Option(None, help="The version of the package to show info for"),
    show_classifiers: bool = Option(False, metavar="classifiers", help="Show the classifiers"),
    hide_project_urls: bool = Option(False, metavar="project_urls", help="Hide the project urls"),
    hide_requirements: bool = Option(False, metavar="requirements", help="Hide the requirements"),
    hide_github: bool = Option(False, metavar="github", help="Hide the github"),
    hide_stats: bool = Option(False, metavar="stats", help="Hide the stats"),
    hide_meta: bool = Option(False, metavar="meta", help="Hide the metadata"),
    full_description: bool = Option(False, help="Show the full description instead of truncating"),
    json_output: bool = Option(False, "--json", help="Output the package metadata as JSON instead of rendering it"),
) -> None:

    """See the information about a package."""
    if not version and "==" in package_name:
        package_name, _, version = package_name.partition("==")
    parsed_data: dict[str, Any] = fetch_pypi_json(package_name, version)

    if json_output:
        print(json.dumps(parsed_data["info"], indent=2))
        raise typer.Exit()

    info: dict[str, Any] = parsed_data["info"]
    releases: dict[str, list[dict[str, Any]]] = parsed_data.get("releases", {})
    urls: list[dict[str, Any]] = parsed_data["urls"]

    try:
        from packaging.version import parse as parse_version  # pylint:disable=import-outside-toplevel
    except ImportError:
        try:
            # distutils was removed in Python 3.12; only usable on older versions
            from distutils.version import LooseVersion as parse_version  # type: ignore[no-redef]  # pylint:disable=import-outside-toplevel
        except ImportError:
            parse_version = str  # type: ignore[assignment]

    from datetime import timezone  # pylint: disable=import-outside-toplevel

    natural_time: str
    if urls:
        release_time: datetime = utc_to_local(
            _parse_iso_datetime(urls[-1]["upload_time_iso_8601"]), timezone.utc
        )
        natural_time = release_time.strftime("%b %d, %Y")
    else:
        natural_time = "UNKNOWN"
    description = info["summary"]
    if not version:
        if info.get("version"):
            latest_version = info["version"]
        elif releases:
            versions = [v for v in map(parse_version, releases.keys()) if not getattr(v, "pre", False)]
            latest_version = max(versions) if versions else "Unknown"
        else:
            latest_version = "Unknown"
        version_comment: str = (
            "[green]Latest Version[/]"
            if str(latest_version) == str(info["version"])
            else f"[red]Newer version available ({latest_version})[/]"
        )
    else:
        version_comment = f"[green]Version[/]: {version}"

    repos: list[str] = find_github_repos(info)
    repo: str | None = repos[0] if repos else None

    from rich.text import Text  # pylint:disable=import-outside-toplevel

    title: Text = Text.from_markup(f"[bold cyan]{info['name']} {info['version']}[/]\n{description}", justify="left")
    message: Text = Text.from_markup(f"{version_comment}\nReleased: {natural_time}", justify="right")
    table: Table = Table.grid(expand=True)
    table.add_column(justify="left")
    table.add_column(justify="right")
    table.add_row(title, message)

    metadata: Table = Table.grid()
    metadata.add_column(justify="left")
    if info.get("project_urls") and not hide_project_urls:
        metadata.add_row(
            Panel(
                "\n".join(f"[yellow]{name}[/]: [link={url}][cyan]{url}[/][/link]" for name, url in info["project_urls"].items()),
                expand=True,
                border_style="magenta",
                title="Project URLs",
            )
        )
    if not hide_github:
        if repo:
            url = f"https://api.github.com/repos/{quote(repo)}"
            try:
                with console.status("Getting data from GitHub"):
                    resp = session.get(url, headers=_github_headers())
            except Exception:
                logger.debug("Failed to fetch GitHub data for %s", repo, exc_info=True)
                resp = None
            if resp is None:
                pass
            elif resp.status_code == 200:
                github_data = json.loads(resp.text)
                if github_data.get("message") and github_data["message"] == "Not Found":
                    metadata.add_row(
                        Panel(
                            f"[red underline]Repo Not Found[/]\n[cyan]Link[/]: {url}\n[light_green]Name[/]: {repo}\n",
                            expand=True,
                            border_style="green",
                            title="GitHub",
                        )
                    )
                else:
                    size = github_data.get("size", -1)
                    stars = github_data.get("stargazers_count", -1)
                    forks = github_data.get("forks_count", -1)
                    issues = github_data.get("open_issues", -1)
                    metadata.add_row(
                        Panel(
                            f"[light_green]Name[/]: [link=https://github.com/{repo}]{repo}[/]\n"
                            f"[light_green]Size[/]: {size:,} KB\n"
                            f"[light_green]Stargazers[/]: {stars:,}\n"
                            f"[light_green]Issues/Pull Requests[/]: {issues:,}\n"
                            f"[light_green]Forks[/]: {forks:,}",
                            expand=True,
                            border_style="green",
                            title="GitHub",
                        )
                    )
            else:
                metadata.add_row(
                        Panel(
                            f"Error {resp.status_code}",
                            expand=True,
                            border_style="green",
                            title="GitHub",
                        )
                    )
    if not hide_stats:
        stats_url = f"https://pypistats.org/api/packages/{package_name}/recent"
        try:
            with console.status("Getting statistics from PyPI Stats"):
                r = session.get(stats_url)
            parsed_stats = json.loads(r.text)
            if not isinstance(parsed_stats, dict):
                parsed_stats = None
        except Exception:
            logger.debug("Failed to fetch download stats for %s", package_name, exc_info=True)
            parsed_stats = None

        stats = parsed_stats.get("data") if parsed_stats else None
        if not isinstance(stats, dict):
            stats = None
        if stats:
            metadata.add_row(
                Panel(
                    f"[blue]Last Month[/]: {stats['last_month']:,}\n"
                    f"[blue]Last Week[/]: {stats['last_week']:,}\n"
                    f"[blue]Last Day[/]: {stats['last_day']:,}",
                    expand=True,
                    border_style="yellow",
                    title="Downloads",
                )
            )
    if not hide_requirements:
        reqs: str = ""
        for req in info["requires_dist"] or []:
            reqs += f"{req}\n"
        requirements: Text = Text(reqs or "No requirements found")
        requirements.highlight_regex(r"\b(?P<name>[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)\s*(?:\[\s*(?P<extras>[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?(?:\s*,\s*[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)*)\s*\])?\s*(?:@\s*(?P<url>[^\s;\n]+)|(?P<versionspec>\(?\s*(?:~=|===|==|!=|<=|>=|<|>)\s*[A-Za-z0-9_.!+*-]+\s*(?:,\s*(?:~=|===|==|!=|<=|>=|<|>)\s*[A-Za-z0-9_.!+*-]+\s*)*\)?))?\s*(?:;\s*(?P<marker>[^\n\r]+?))?\s*(?=\n|\r|$)", style_prefix="requirement.")
        if info["requires_dist"]:
            metadata.add_row(
                Panel(
                    requirements,
                    expand=True,
                    border_style="red",
                    title="Requirements",
                )
            )
    if not hide_meta:
        ownership_information: str | None
        if parsed_data.get("ownership"):
            ownership_information = ""
            roles: list[dict[str, str]] = parsed_data['ownership'].get("roles", [])
            for n, role in enumerate(roles, start=1):
                ownership_information += f"[dark_goldenrod]{role['role']}{f' #{n}' if len(roles) > 1 else ''}:[/] {role['user']}\n"
            if parsed_data["ownership"].get("organization"):
                ownership_information += f"[dark_goldenrod]Organization:[/] {parsed_data['ownership']['organization']}\n"
        else:
            ownership_information = None
        metadata.add_row(
            Panel(
                "\n".join(
                    i
                    for i in (
                        f"[dark_goldenrod]License[/]: {info['license']}",
                        f"[dark_goldenrod]Author[/]: {info['author']}",
                        f"[dark_goldenrod]Author Email[/]: {info['author_email']}" if info["author_email"] else "",
                        f"[dark_goldenrod]Maintainer[/]: {info['maintainer']}" if info["maintainer"] else "",
                        f"[dark_goldenrod]Maintainer Email[/]: {info['maintainer_email']}"
                        if info["maintainer_email"]
                        else "",
                        f"[dark_goldenrod]Requires Python[/]: {info['requires_python'] or None}",
                        ownership_information.strip() if ownership_information else None
                    )
                    if i
                ),
                expand=True,
                border_style="yellow1",
                title="Meta",
            )
        )
    if show_classifiers:
        metadata.add_row(
            Panel(
                _format_classifiers("\n".join(info["classifiers"])).strip(),
                expand=True,
                border_style="cyan",
                title="Classifiers",
            )
        )
    MIN_SIDEBAR_WIDTH: int = 30
    MIN_DESC_WIDTH: int = 45

    # Measure metadata width
    measurement = console.measure(metadata)
    max_needed: int = measurement.maximum

    use_stacked: bool
    measure_width: int
    if console.width < MIN_SIDEBAR_WIDTH + MIN_DESC_WIDTH:
        use_stacked = True
        measure_width = console.width
    else:
        use_stacked = False
        sidebar_width: int = min(max_needed, console.width - MIN_DESC_WIDTH, console.width // 2)
        sidebar_width = max(sidebar_width, min(max_needed, MIN_SIDEBAR_WIDTH))
        measure_width = sidebar_width

    # Measure metadata height to dynamically size the description
    from io import StringIO  # pylint: disable=import-outside-toplevel
    from rich.console import Console as _Console  # pylint: disable=import-outside-toplevel

    _buf: StringIO = StringIO()
    _temp: _Console = _Console(file=_buf, width=measure_width)
    _temp.print(metadata)
    metadata_height: int = _buf.getvalue().count("\n")
    max_desc_lines: int = max(40, metadata_height)

    desc_source: str = info["description"] or ""

    desc_renderable: Any
    if info["description_content_type"] == "text/markdown":
        from rich.markdown import Markdown  # pylint: disable=import-outside-toplevel

        desc_renderable = Markdown(desc_source)
    elif info["description_content_type"] == "text/x-rst":
        from rich_rst import RestructuredText  # pylint: disable=import-outside-toplevel

        desc_renderable = RestructuredText(desc_source)
    else:
        from rich.text import Text  # pylint: disable=import-outside-toplevel

        desc_renderable = Text(desc_source)

    # Truncate the rendered output rather than the source, since source lines
    # don't map to rendered lines (HTML blocks and comments render to nothing)
    truncation_notice: bool = False
    if not full_description:
        from rich.segment import Segment, Segments  # pylint: disable=import-outside-toplevel

        desc_panel_width: int = console.width if use_stacked else console.width - sidebar_width
        # Account for the description panel's borders and padding
        render_width: int = max(desc_panel_width - 4, 1)
        rendered_lines = console.render_lines(
            desc_renderable, console.options.update_width(render_width), pad=False
        )
        if len(rendered_lines) > max_desc_lines:
            segments: list[Segment] = []
            for line in rendered_lines[:max_desc_lines]:
                segments.extend(line)
                segments.append(Segment.line())
            desc_renderable = Segments(segments)
            truncation_notice = True

    from rich.console import Group  # pylint: disable=import-outside-toplevel

    if truncation_notice:
        from rich.text import Text  # pylint: disable=import-outside-toplevel

        notice: Text = Text(
            "\nDescription truncated. Use the 'description' command or the '--full-description' flag for the full description.",
            style="italic gray66",
            justify="center"
        )
        description = Panel(Group(desc_renderable, notice), title="Description", border_style="bold magenta")
    else:
        description = Panel(desc_renderable, title="Description", border_style="bold magenta")

    console.print(Panel(table, border_style="green"))
    if use_stacked:
        console.print(metadata)
        console.print(description)
    else:
        side_by_side: Table = Table.grid(padding=0)
        side_by_side.add_column(width=sidebar_width)
        side_by_side.add_column(width=console.width - sidebar_width)
        side_by_side.add_row(metadata, description)
        console.print(side_by_side)


@app.command()
def regex_search(
    regex: str = Argument(..., help="The regular expression to search with"),
    compact: bool = Option(False, help="Compact formatting"),
    limit: int = Option(50, help="Limit the number of results to show")
) -> None:
    """Search for packages that match the regular expression."""
    packages: list[str] = load_cache()

    import re  # pylint: disable=import-outside-toplevel

    # We explicitly set the limit to unlimited if it's -1
    max_matches: float = float('inf') if limit == -1 else limit

    # We compile the regex because it's twice as fast (https://imgur.com/a/MoUyEMg)
    try:
        _regex: re.Pattern[str] = re.compile(regex)
    except re.error as exc:
        console.print(f"[red]:no_entry_sign: Invalid regular expression: {exc}[/]")
        raise typer.Exit(code=2)
    if compact:
        matches: list[str] = []
        for package in packages:
            if _regex.match(package):
                matches.append(f"[link={base_url}/project/{package}]{package}[/]")
                if len(matches) >= max_matches:
                    break
        console.print(", ".join(matches))
    else:
        table: Table = Table(show_header=True, show_lines=True)
        table.add_column("[purple]No.[/]", style="purple")
        table.add_column("[green]Package[/]")
        table.add_column("[blue]Link[/]", style="cyan")
        match_count: int = 0
        for package in packages:
            if _regex.match(package):
                match_count += 1
                if match_count > max_matches:
                    break
                table.add_row(
                    f"{match_count}.",
                    f"[link={base_url}/project/{package}]{package}[/]",
                    f"{base_url}/project/{package}",
                )
        table.title = f"{table.row_count} matches for [#ffffff on #000000]{regex}[/]"
        console.print(table)
        # Whatever the limit is if the user tries to see more than 50 items at once the compact option is recommended to avoid cluttering the terminal with too much information
        if table.row_count > 50:
            console.print(
                f"[yellow]:warning: WARNING:[/] There are more than 50 matches, consider using the --compact flag"
            )


@app.command()
def read_the_docs(
    package_name: str = Argument(..., help="The name or link to the docs of the package to show the documentation for"),
    query: str = Argument(
        None, help="The query you want to read the docs for, if not passed goes to the main docs page"
    ),
    url_only: bool = Option(True, help="Only print the url to the console instead of opening it in a browser"),
) -> None:
    """Search the documentation for an item of a package."""
    import webbrowser  # pylint: disable=import-outside-toplevel

    docs_mapping: dict[str, str] = {
        "py": "https://docs.python.org/3/search.html",
        "python": "https://docs.python.org/3/search.html",
        "python3": "https://docs.python.org/3/search.html",
        "py2": "https://docs.python.org/2/search.html",
        "python2": "https://docs.python.org/2/search.html",
        "pil": "https://pillow.readthedocs.io/en/stable/search.html",
        "pillow": "https://pillow.readthedocs.io/en/stable/search.html",
        "aiohttp": "https://docs.aiohttp.org/en/stable/search.html",
        "attrs": "https://www.attrs.org/en/stable/search.html",
        "babel": "https://babel.readthedocs.io/en/latest/search.html",
        "boto3": "https://boto3.amazonaws.com/v1/documentation/api/latest/search.html",
        "cachetools": "https://cachetools.readthedocs.io/en/latest/search.html",
        "cffi": "https://cffi.readthedocs.io/en/latest/search.html",
        "chardet": "https://chardet.readthedocs.io/en/latest/search.html",
        "cryptography": "https://cryptography.io/en/latest/search.html",
        "cv2": "http://docs.opencv.org/2.4/search.html",
        "discord.py": "https://discordpy.readthedocs.io/en/latest/search.html",
        "django": "http://docs.djangoproject.com/en/dev/search",
        "dnspython": "https://dnspython.readthedocs.io/en/latest/search.html",
        "flask": "https://flask.palletsprojects.com/en/1.1.x/search",
        "h5py": "http://docs.h5py.org/en/latest/search.html",
        "importlib-metadata": "https://importlib-metadata.readthedocs.io/en/latest/search.html",
        "importlib-resources": "https://importlib-resources.readthedocs.io/en/latest/search.html",
        "importlib_metadata": "https://importlib-metadata.readthedocs.io/en/latest/search.html",
        "importlib_resources": "https://importlib-resources.readthedocs.io/en/latest/search.html",
        "matplotlib": "https://matplotlib.org/stable/search.html",
        "natsort": "https://natsort.readthedocs.io/en/master/search.html",
        "numpy": "http://docs.scipy.org/doc/numpy/search.html",
        "oauthlib": "https://oauthlib.readthedocs.io/en/latest/search.html",
        "packaging": "https://packaging.pypa.io/en/latest/search.html",
        "pandas": "https://pandas.pydata.org/docs/search.html",
        "psutil": "https://psutil.readthedocs.io/en/latest/search.html",
        "pydash": "https://pydash.readthedocs.io/en/latest/search.html",
        "pyjwt": "https://pyjwt.readthedocs.io/en/latest/search.html",
        "pyopenssl": "https://www.pyopenssl.org/en/latest/search.html",
        "pyparsing": "https://pyparsing-docs.readthedocs.io/en/latest/search.html",
        "pyqt": "https://doc.qt.io/qtforpython/search.html",
        "pyramid": "https://docs.pylonsproject.org/projects/pyramid/en/latest/search.html",
        "pyrsistent": "https://pyrsistent.readthedocs.io/en/latest/search.html",
        "pytest": "https://docs.pytest.org/en/stable/search.html",
        "pytest-regressions": "https://pytest-regressions.readthedocs.io/en/latest/search.html",
        "python-dateutil": "https://dateutil.readthedocs.io/en/stable/search.html",
        "pytorch": "https://pytorch.org/docs/stable/search.html",
        "requests": "https://requests.readthedocs.io/en/master/search.html",
        "requests-oauthlib": "https://requests-oauthlib.readthedocs.io/en/latest/search.html",
        "scikit-learn": "https://scikit-learn.org/stable/search.html",
        "scipy": "https://docs.scipy.org/doc/scipy/search.html",
        "six": "https://six.readthedocs.io/search.html",
        "slumber": "https://slumber.readthedocs.io/en/v0.6.0/search.html",
        "sphinx": "https://www.sphinx-doc.org/en/master/search.html",
        "yarl": "https://yarl.readthedocs.io/en/latest/search.html",
        "zipp": "https://zipp.readthedocs.io/en/latest/search.html",
    }

    url: str | None
    if package_name[:4] == "http":
        url = package_name
    else:
        if package_name in docs_mapping:
            url = docs_mapping[package_name]
        else:
            import questionary  # pylint: disable=import-outside-toplevel

            resp: bool | None = questionary.confirm(
                "Docs not available. Do you want to search pypi to find the documentation?"
            ).ask()
            if resp:
                parsed_data = fetch_pypi_json(package_name)
                url = (parsed_data["info"].get("project_urls") or {}).get("Documentation", None)
                if not url:
                    console.print("[bold]:x: Documentation url not found on PyPI[/]")
                    raise typer.Exit()
                else:
                    import os.path  # pylint: disable=import-outside-toplevel

                    if "readthedocs.io" in url:
                        url = os.path.join(url, "en/stable/")
                    url = os.path.join(url, "search.html")
            else:
                console.print("[dim grey]:ok: Cancelled![/]")
                raise typer.Exit()

    if not query:
        if url_only:
            console.print(url.replace("search.html", ""), style="cyan")
            raise typer.Exit()
        webbrowser.open(url.replace("search.html", ""))
        raise typer.Exit()
    search_page: str = url + "?q=" + quote(query)
    if url_only:
        console.print(search_page, style="cyan")
        raise typer.Exit()
    webbrowser.open(search_page)


@app.command()
def browse(
    package_name: str = Argument(..., help="The name of the package to show links for"),
    url_only: bool = Option(
        False,
        help="If this is set then it will only show the urls instead of interactively opening them in the browser",
    ),
) -> None:
    """Browse for a package's URLs"""
    import webbrowser  # pylint: disable=import-outside-toplevel

    import questionary  # pylint: disable=import-outside-toplevel

    link_style: questionary.Style = questionary.Style([("name", "bold red"), ("separator", "gray"), ("url", "cyan")])

    parsed_data: dict[str, Any] = fetch_pypi_json(package_name)
    info: dict[str, Any] = parsed_data["info"]

    urls: dict[str, str | None] = dict(info.get("project_urls") or {})
    urls["Project URL"] = info.get("project_url")
    urls["Home Page"] = info.get("home_page")
    urls["Release URL"] = info.get("release_url")
    urls["Mail to"] = ("mailto:" + info["maintainer_email"]) if info.get("maintainer_email") else None

    if url_only:
        console.print("\n".join(f"[red]{name:15}[/] [grey46]-[/] [cyan]{url}[/]" for name, url in urls.items() if url))
        raise typer.Exit()

    answer: str | None = questionary.select(
        "Which link do you want to to open?",
        choices=[
            questionary.Choice(
                title=[("class:name", f"{name:15}"), ("class:separator", " - "), ("class:url", url)], value=url
            )
            for name, url in urls.items()
            if url
        ],
        style=link_style,
    ).ask()
    if answer:
        webbrowser.open(answer)


@app.command()
def cache_refresh() -> None:
    """Refresh the cache."""
    _refresh_cache()


@app.command()
def cache_clear() -> None:
    """Clear the cache."""
    _clear_cache()


@app.command()
def cache_info() -> None:
    """See information about the cache"""
    import os.path  # pylint: disable=import-outside-toplevel
    import humanize  # pylint: disable=import-outside-toplevel

    packages_cache: str = os.path.join(get_cache_dir(), "packages.txt")
    requests_cache: str = os.path.join(get_cache_dir(), "requests.sqlite")
    packages_size: int | None
    packages_last_refreshed: float | None
    requests_size: int | None
    try:
        packages_size = os.path.getsize(packages_cache)
        packages_last_refreshed = os.path.getmtime(packages_cache)
    except FileNotFoundError:
        packages_size = None
        packages_last_refreshed = None
        console.print("[bold yellow]:no_entry_sign: Packages cache not available[/]")
    try:
        requests_size = os.path.getsize(requests_cache)
    except FileNotFoundError:
        requests_size = None
        console.print("[bold yellow]:no_entry_sign: Requests cache not available[/]")
        if not packages_size:
            console.print("[bold red]:warning::no_entry_sign: No cache available![/]")
            # If both the caches are unavailable, then we can't do anything
            raise typer.Exit()

    console.print(f"ℹ️ Packages cache size: {humanize.naturalsize(packages_size or 0, binary=True)}")

    console.print(f"ℹ️ Requests cache size: {humanize.naturalsize(requests_size or 0, binary=True)}")
    if packages_last_refreshed:
        from datetime import datetime

        console.print(
            f"⏰ Requests cache last updated: {humanize.naturaltime(datetime.fromtimestamp(packages_last_refreshed))}"
        )

    if requests_size and hasattr(session, "cache"):
        table: Table = Table(title="All cached requests")
        table.add_column("Index", style="dim magenta", header_style="bold magenta")
        table.add_column("Link", style="cyan", header_style="bold cyan")
        table.add_column("Created", style="green", header_style="bold green")
        table.add_column("Expires", style="green", header_style="bold green")
        # requests-cache >= 0.8 exposes responses via `cache.responses`; older
        # versions made the cache itself a mapping.
        cached_responses = getattr(session.cache, "responses", session.cache)

        from datetime import datetime, timezone  # pylint: disable=import-outside-toplevel

        def natural_time(dt: datetime | None) -> str:
            if dt is None:
                return "never"
            # requests-cache may return timezone-aware datetimes, which humanize
            # cannot compare against its naive "now" default.
            now = datetime.now(timezone.utc) if dt.tzinfo else None
            return humanize.naturaltime(dt, when=now)

        for n, response in enumerate(cached_responses.values()):
            table.add_row(f"{n}.", response.url, natural_time(response.created_at), natural_time(response.expires))
        console.print(table)


@app.command()
def version(
    package_name: str = Argument(
        None, help="The name or link to the docs of the package to show the documentation for"
    ),
    limit: int = Option(10, help="Limit the number of versions to show"),
    no_pre_releases: bool = Option(False, help="If set then it will not show pre-releases"),
    show_installed_version: bool = Option(False, help="If set then it will show the version that is installed too"),
) -> None:
    """Show the cli's or another package's version and exit"""
    if not package_name:
        import sys
        from . import __version__  # pylint: disable=import-outside-toplevel

        console.print(f"Python version: {sys.version}")
        console.print(f"Current version of [yellow]pypi-command-line[/] is [red]{__version__}[/]")
        with console.status("Getting latest version"):
            latest_version: str | None = get_latest_version()
        if latest_version is None:
            console.print("[yellow]:warning: Could not fetch the latest version from PyPI[/]")
        else:
            console.print(f"Latest  version of [yellow]pypi-command-line[/] is [red]{latest_version}[/]")
        raise typer.Exit()

    parsed_data: dict[str, Any] = fetch_pypi_json(package_name)

    try:
        from packaging.version import parse as parse_version  # pylint:disable=import-outside-toplevel
    except ImportError:
        if no_pre_releases:
            console.print(
                "[red]:no_entry_sign: Install packaging (`pip install packaging`) to use the --no-pre-releases flag[/]"
            )
            raise typer.Exit()
        try:
            # distutils was removed in Python 3.12; only usable on older versions
            from distutils.version import LooseVersion as parse_version  # type: ignore[no-redef]  # pylint:disable=import-outside-toplevel
        except ImportError:
            console.print(
                "[red]:no_entry_sign: Install packaging (`pip install packaging`) to use the version command[/]"
            )
            raise typer.Exit(code=1)

    versions: Iterator[Any] = map(parse_version, parsed_data["releases"].keys())
    if no_pre_releases:
        versions = filter(lambda x: not x.is_prerelease, versions)
    latest_versions: list[Any] = sorted(versions, reverse=True)[:limit]

    minimal_output: bool = limit == 1
    installed_version: str | None = _get_installed_version(package_name) if show_installed_version else None

    output: str
    if minimal_output:
        output = f"[green]{package_name}[/] -"
    else:
        version_info: str = ""
        if show_installed_version:
            if installed_version is None:
                version_info = " [red](Not Installed)[/]"
            else:
                version_info = f" [dark_orange](Installed Version: {installed_version})[/]"
        output = f"Top {limit} latest versions of [green]{package_name}[/]{version_info}{' [yellow](excluding pre-releases)[/]' if no_pre_releases else ''}:\n"

    from datetime import timezone  # pylint: disable=import-outside-toplevel
    import humanize  # pylint: disable=import-outside-toplevel

    for n, version in enumerate(latest_versions, start=1):
        output += f" {f'[magenta]{n}.[/] ' if not minimal_output else ''}"

        if limit == 1 and show_installed_version and installed_version is not None:
            output += f"[yellow]{installed_version}[/]->[blue]{version}[/]"
        else:
            output += f"[blue]{version}[/]"

        try:
            upload_time = utc_to_local(
                _parse_iso_datetime(parsed_data["releases"][str(version)][0]["upload_time_iso_8601"]),
                timezone.utc,
            )
            output += f" [red]{humanize.naturaltime(upload_time)}[/] [cyan]({upload_time.strftime('%a %b %d %H:%M:%S %Y')})[/]"
        except Exception:
            logger.debug("Failed to determine upload time for %s %s", package_name, version, exc_info=True)
        finally:
            output += "\n"
    console.print(output.strip())

@app.command()
def compare(
    package_names: list[str] = Argument(..., help="The names of the packages to compare"),
    json_output: bool = Option(False, "--json", help="Output the results as JSON instead of a table"),
) -> None:
    """Compare multiple packages side-by-side."""
    from concurrent.futures import ThreadPoolExecutor  # pylint: disable=import-outside-toplevel

    with console.status("Fetching comparison data..."):
        with ThreadPoolExecutor(max_workers=8) as executor:
            fetched_data: list[dict[str, str] | None] = list(executor.map(fetch_comparison_data, package_names))
    results: list[dict[str, str]] = [pkg for pkg in fetched_data if pkg is not None]

    if json_output:
        from rich.text import Text  # pylint: disable=import-outside-toplevel

        # Strip the rich markup used for error values so the JSON stays plain
        records: list[dict[str, str]] = [
            {key: Text.from_markup(value).plain if isinstance(value, str) else value for key, value in pkg.items()}
            for pkg in results
        ]
        print(json.dumps(records, indent=2))
        raise typer.Exit()

    table: Table = Table(
        title="[bold]PyPI Package Comparison[/bold]",
        show_header=True,
        show_lines=True,
    )

    table.add_column("[cyan]Metric[/]", style="cyan", header_style="cyan")
    for pkg in results:
        table.add_column(f"[green]{pkg['name']}[/]", justify="center", style="white")

    metrics: list[tuple[str, str]] = [
        ("Latest Version", "version"),
        ("Latest Release", "release_date"),
        ("GitHub Stars", "stars"),
        ("Open Issues", "open_issues"),
        ("Downloads (Month)", "downloads"),
        ("Requires Python", "python_version"),
    ]

    for metric_name, key in metrics:
        row: list[str] = [metric_name]
        for pkg in results:
            row.append(pkg[key])
        table.add_row(*row)

    console.print(table)

@app.command()
def dependencies(
    package_name: str = Argument(..., help="The name of the package to explore (e.g. [green]requests[/] or [green]requests[security][/])"),
    level: int = Option(5, "--level", "-l", help="Maximum depth of the dependency tree to display", show_default=True),
    no_cache: bool = Option(False, "--no-cache", help="Bypass cache when fetching dependency data"),
) -> None:
    """Explore the dependency tree of a PyPI package.

    Fetches and displays a rich, visual tree of a package's dependencies
    and sub-dependencies up to [bold]n[/bold] levels deep.

    [bold]Examples:[/bold]
      [bold]pypi dependencies requests[/]
      [bold]pypi dependencies \"requests[security]\" --level 2[/]
    """
    from concurrent.futures import ThreadPoolExecutor  # pylint: disable=import-outside-toplevel
    from packaging.requirements import Requirement  # pylint: disable=import-outside-toplevel
    from rich.tree import Tree  # pylint: disable=import-outside-toplevel
    from rich.text import Text  # pylint: disable=import-outside-toplevel

    # ── Parse package name and extras ────────────────────────────────────────
    # Support "requests[security]" syntax as argument
    root_extras: set[str] = set()
    bracket_pos: int = package_name.find("[")
    if bracket_pos != -1 and package_name.endswith("]"):
        root_extras = {e.strip() for e in package_name[bracket_pos + 1 : -1].split(",")}
        package_name = package_name[:bracket_pos]

    # ── Cache for fetched metadata ────────────────────────────────────────────
    # Maps lowercase package name → parsed JSON info dict (or None on failure)
    fetched: dict[str, dict[str, Any] | None] = {}

    # ── Fetch helper ─────────────────────────────────────────────────────────
    fetch_session: Session = _make_plain_session() if no_cache else session

    def fetch_info(name: str) -> tuple[str, dict[str, Any] | None]:
        """Fetch /pypi/<name>/json from PyPI; return (name, info_dict or None)."""
        try:
            url: str = f"{base_url}/pypi/{quote(name)}/json"
            resp: Response = fetch_session.get(url)
            if resp.status_code == 200:
                data: dict[str, Any] = json.loads(resp.text)
                return name.lower(), data.get("info")
            return name.lower(), None
        except Exception:
            logger.debug("Failed to fetch dependency info for %s", name, exc_info=True)
            return name.lower(), None

    # ── Formatting helpers ────────────────────────────────────────────────────
    def _format_req_label(req: Requirement) -> Text:
        """Return a styled rich Text label for a single Requirement."""
        t: Text = Text()
        t.append(req.name, style="bold #92EC5A")           # package name – green
        if req.extras:
            t.append("[", style="#9263FB")
            t.append(", ".join(sorted(req.extras)), style="#9263FB")
            t.append("]", style="#9263FB")
        if req.specifier:
            t.append(str(req.specifier), style="#33F1C8")   # version spec – teal
        if req.marker:
            t.append(f" ; {req.marker}", style="dim #F2C259")  # marker – muted gold
        return t

    # ── BFS traversal ─────────────────────────────────────────────────────────
    # We fetch the root package first (synchronously for status display), then
    # explore level-by-level with ThreadPoolExecutor.

    # Step 1 – fetch root
    with console.status(f"[bold cyan]Fetching[/] [green]{package_name}[/] from PyPI…"):
        _, root_info = fetch_info(package_name)

    if root_info is None:
        console.print(f"[red]:no_entry_sign: Package [green]{package_name}[/] not found on PyPI.[/]")
        raise typer.Exit(code=1)

    fetched[package_name.lower()] = root_info

    # ── Build the tree root ───────────────────────────────────────────────────
    root_label: Text = Text()
    root_label.append("📦 ", style="")
    root_label.append(root_info["name"], style="bold #4AA0FC")      # blue
    root_label.append(f" {root_info['version']}", style="bold #F2C259")  # gold
    if root_extras:
        root_label.append("[", style="#9263FB")
        root_label.append(", ".join(sorted(root_extras)), style="#9263FB")
        root_label.append("]", style="#9263FB")
    if root_info.get("summary"):
        root_label.append(f"  {root_info['summary'][:60]}", style="dim")

    tree: Tree = Tree(root_label, guide_style="dim cyan")

    # ── BFS queue: each entry is (parent_rich_node, req, extras, current_depth)
    # We group by level to enable concurrent fetching at each level.
    # queue items: (parent_node, req_object, extras_set, depth)
    current_level_items: list[tuple[Tree, Requirement, set[str], int]] = [
        (tree, req, req.extras or set(), 1)
        for req in _get_package_dependencies(root_info, root_extras)
    ]

    # Track visited to avoid infinite loops (circular deps)
    visited: set[str] = {package_name.lower()}

    for depth in range(1, level + 1):
        if not current_level_items:
            break

        # Collect names we still need to fetch at this level
        names_to_fetch: list[str] = [
            req.name
            for (_, req, _, _) in current_level_items
            if req.name.lower() not in fetched
        ]
        names_to_fetch = list(dict.fromkeys(n.lower() for n in names_to_fetch))  # deduplicate

        if names_to_fetch:
            with console.status(
                f"[bold cyan]Fetching[/] [dim]{len(names_to_fetch)} package(s)[/] at depth [yellow]{depth}[/]…"
            ):
                with ThreadPoolExecutor(max_workers=min(16, len(names_to_fetch))) as executor:
                    for name, fetched_info in executor.map(fetch_info, names_to_fetch):
                        fetched[name] = fetched_info

        next_level_items: list[tuple[Tree, Requirement, set[str], int]] = []

        for parent_node, req, req_extras, _ in current_level_items:
            pkg_key: str = req.name.lower()
            info: dict[str, Any] | None = fetched.get(pkg_key)

            if pkg_key in visited:
                # Circular dependency — show it but don't recurse further
                circ_label: Text = Text()
                circ_label.append("🔁 ", style="")
                circ_label.append(req.name, style="bold #FF7F30")
                if req.specifier:
                    circ_label.append(str(req.specifier), style="#33F1C8")
                circ_label.append("  (circular)", style="dim")
                parent_node.add(circ_label)
                continue

            visited.add(pkg_key)

            if info is None:
                # Not found or fetch error
                err_label: Text = Text()
                err_label.append("❌ ", style="")
                err_label.append(req.name, style="bold red")
                if req.specifier:
                    err_label.append(str(req.specifier), style="#33F1C8")
                err_label.append("  (not found)", style="dim red")
                parent_node.add(err_label)
                continue

            # Build label with resolved version
            node_label: Text = Text()
            node_label.append("📦 " if depth == 1 else "  ", style="")
            node_label.append(req.name, style="bold #92EC5A")
            if req_extras:
                node_label.append("[", style="#9263FB")
                node_label.append(", ".join(sorted(req_extras)), style="#9263FB")
                node_label.append("]", style="#9263FB")
            if req.specifier:
                node_label.append(str(req.specifier), style="#33F1C8")
            # Show resolved version dimly
            resolved_ver: str = info.get("version", "?")
            node_label.append(f"  → {resolved_ver}", style="dim #4AA0FC")
            if req.marker:
                node_label.append(f"  ; {req.marker}", style="dim #F2C259")

            child_node: Tree = parent_node.add(node_label)

            # Queue children for the next level (if we haven't hit max depth)
            if depth < level:
                child_deps: list[Requirement] = _get_package_dependencies(info, req_extras)
                for child_req in child_deps:
                    next_level_items.append((child_node, child_req, child_req.extras or set(), depth + 1))

        current_level_items = next_level_items

    # ── Final summary line ────────────────────────────────────────────────────
    total_pkgs: int = len(visited) - 1  # exclude root itself
    console.print()
    console.print(tree)
    console.print()
    console.print(
        f"[dim]Explored [bold cyan]{total_pkgs}[/bold cyan] unique package(s) "
        f"across [bold yellow]{min(depth, level)}[/bold yellow] level(s) of depth.[/dim]"
    )


@app.callback()
def main(
    cache: bool = Option(True, help="Whether to use cache or not"),
    repository: str = Option(
        None, help="The repository to fetch the information from. Either 'testpypi' or a full URL like 'https://test.pypi.org'"
    ),
    timeout: float = Option(
        DEFAULT_TIMEOUT, help="Timeout in seconds for network requests", min=0.1
    ),
    verbose: bool = Option(
        False, "--verbose", "-v", help="Show debug logs for errors that are otherwise silently ignored"
    ),
) -> None:
    """
    A beautiful command line interface for the Python Package Index
    """
    global _timeout
    _timeout = timeout
    if verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(name)s: %(message)s")
        logger.setLevel(logging.DEBUG)
    if not cache:
        global session
        session = _make_plain_session()
    if repository:
        global base_url
        if repository == "testpypi":
            base_url = "https://test.pypi.org"
        else:
            from urllib.parse import urlparse  # pylint: disable=import-outside-toplevel

            parsed: ParseResult = urlparse(repository)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                console.print(
                    f"[red]:no_entry_sign: Invalid repository '{repository}'. "
                    "Use 'testpypi' or a full URL like 'https://test.pypi.org'[/]"
                )
                raise typer.Exit(code=2)
            base_url = repository.rstrip("/")


def run() -> None:
    """Redefine typer.run() to use our custom Typer class."""  # noqa D402
    app()



if __name__ == "__main__":
    run()
