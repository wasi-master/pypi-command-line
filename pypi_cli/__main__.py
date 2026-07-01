"""The main file."""
from typing import Callable

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
    import json
else:
    json.JSONDecodeError = ValueError

base_url = "https://pypi.org"

try:
    from requests_cache.session import CachedSession
except ImportError:
    from requests import Session

    session = Session()
    session.headers.update({"User-Agent": "wasi_master/pypi_cli", "Accept": "application/json"})
else:
    import os.path  # pylint: disable=import-outside-toplevel

    cache_path = os.path.join(os.path.dirname(__file__), "cache", "requests")
    session = CachedSession(
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
        headers={"User-Agent": "wasi_master/pypi_cli", "Accept": "application/json"},
        cache_control=True,
    )

try:
    import lxml
except ImportError:
    lxml = None


def __color_error_message():
    """Override click.UsageError.show to show colored output"""
    from click._compat import get_text_stderr  # pylint: disable=import-outside-toplevel
    from rich.markup import escape  # pylint: disable=import-outside-toplevel

    def show(self, file=None):
        if file is None:
            file = get_text_stderr()
        hint = ""
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
            style = Style([("link", "cyan"), ("command", "blue"), ("cancel", "gray")])
            print("\n")
            resp = questionary.select(
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

class AliasedGroup(Group):
    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        alias_mapping = {**dict.fromkeys(["rtd", "docs", "documentation"], "read-the-docs"), "rs": "regex-search", "rsearch": "regex-search", "vuln": "vulnerabilities", "deps": "dependencies", "dep": "dependencies", "d": "dependencies", "b": "browse", "s": "rsearch", "i": "info", "c": "compare", "cmp": "compare"}
        if cmd_name in alias_mapping:
            return click.Group.get_command(self, ctx, alias_mapping[cmd_name])
        commands = self.list_commands(ctx)
        matches = [x for x in commands if x.startswith(cmd_name)]
        if not matches:
            processor = lambda x: x.replace("-", "").lower()
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
                    import thefuzz.fuzz  # pylint: disable=import-outside-toplevel
                    import thefuzz.process  # pylint: disable=import-outside-toplevel
                    import warnings  # pylint: disable=import-outside-toplevel

                    warnings.filterwarnings("error")
                    try:
                        get_closest_match = lambda cmd: [
                            i[0]
                            for i in thefuzz.process.extractBests(
                                cmd, commands, score_cutoff=50, processor=processor, limit=5
                            )
                        ]
                    except UserWarning:
                        console.print(
                            "[yellow]WARNING:[/] Using slow [red]thefuzz[/] and [red]]difflib.SequenceMatcher[/]. "
                            "Consider installing `=[red]rapidfuzz[/] or [red]python-levenstein[/]"
                        )
                except ImportError:
                    import difflib  # pylint: disable=import-outside-toplevel

                    get_closest_match = lambda cmd: difflib.get_close_matches(cmd, commands, n=5, cutoff=0.5) or [None]
        if len(matches) == 0:
            closest_matches = get_closest_match(cmd_name)
            if not closest_matches:
                # No match is more than 50% similar to the used name
                return None

            try:
                import questionary  # pylint: disable=import-outside-toplevel
            except ImportError:
                console.print(
                    f"""[cyan]ℹ️ Info:[/] Found invalid command '{cmd_name}', did you mean any of these: {', '.join(f"'[red]{match}[/]'" for match in closest_matches)}"""
                )
                raise typer.Exit()
            else:
                console.print(
                    f"""[cyan]ℹ️ Info:[/] Found invalid command '{cmd_name}', closest matches: {', '.join(f"'[red]{match}[/]'" for match in closest_matches)}"""
                )
                resp = questionary.select(
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
        formatted_matches = ", ".join(sorted(f"[red]{match}[/]" for match in matches))
        try:
            import questionary
        except ImportError:
            ctx.fail(f"Found Too many matches for '{cmd_name}': {formatted_matches}")
        else:
            import difflib  # pylint: disable=import-outside-toplevel

            console.print(f"[red]:warning: Attention:[/] Found Too many matches for '{cmd_name}': {formatted_matches}")
            command = questionary.select(
                "Select one to continue",
                choices=difflib.get_close_matches(cmd_name, matches, cutoff=0.0),
                style=questionary.Style([("text", "red"), ("highlighted", "bg:ansibrightred")]),
            ).ask()
            if not command:
                raise typer.Exit()
            return click.Group.get_command(self, ctx, command)

    def resolve_command(self, ctx, args):
        # always return the full command name
        _, cmd, args = super().resolve_command(ctx, args)
        return cmd.name, cmd, args


class PypiTyper(typer.Typer):
    """A custom subclassed version of typer.Typer to allow rich help."""

    def __init__(
        self,
        *args,
        cls=AliasedGroup,
        **kwargs,
    ) -> None:
        """Initialise with a RichGroup class as the default."""
        super().__init__(*args, cls=cls, **kwargs)

    def command(
        self,
        *args,
        cls=Command,
        **kwargs,
    ) -> Callable[[CommandFunctionType], CommandFunctionType]:
        return super().command(*args, cls=cls, **kwargs)



# We instantiate a custom typer app
app = PypiTyper()
console = Console(
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

    def __init__(self, soup):
        """Instantiate a package object gotten from scraping the search results.

        Parameters
        ----------
        soup : bs4.BeautifulSoup
            The soup that was gotten from PyPI
        """
        self.name = soup.find(class_="package-snippet__name").get_text()
        time = soup.find(class_="package-snippet__created")
        self.date = time.get_text().strip()
        self.released = datetime.strptime(time.find("time")["datetime"][:-5], "%Y-%m-%dT%H:%M:%S")
        self.description = soup.find(class_="package-snippet__description").get_text()

def utc_to_local(utc_dt, tzinfo):
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


def remove_dot_git(text):
    """Remove the .git suffix from a URL."""
    if text.endswith(".git"):
        return text[:-4]
    return text


def _format_classifiers(_classifiers: str):
    """Format classifiers gotten from the API."""
    from collections import defaultdict
    classifier_dict = defaultdict(list)
    for classifier in _classifiers.splitlines():
        topic, content = map(str.strip, classifier.split("::", 1))
        classifier_dict[topic].append(content)
    return "".join(
        f"[bold]{topic}[/]\n" + "".join(f"  {c}\n" for c in contents)
        for topic, contents in classifier_dict.items()
    )


def get_latest_version():
    import re

    r = session.get("https://img.shields.io/pypi/v/pypi-command-line")
    return re.search(r"<text.+>v(.*?)</text>", r.text).group(1)


def load_cache():
    import os  # pylint: disable=import-outside-toplevel

    cache_file = os.path.join(os.path.dirname(__file__), "cache", "packages.txt")

    try:
        last_refreshed = os.path.getmtime(cache_file)
    except FileNotFoundError:
        return fill_cache(msg="Generating cache")
    else:
        import time  # pylint: disable=import-outside-toplevel

        if time.time() - last_refreshed > 86400:
            return fill_cache(msg="Cache is too old (>1d). Refreshing cache")
        with open(cache_file, "r", encoding="utf-8") as f:
            return f.read().splitlines()


def fill_cache(msg="Fetching cache"):
    """Fill the cache with the packages."""
    import os  # pylint: disable=import-outside-toplevel

    import requests  # pylint: disable=import-outside-toplevel
    from rich.progress import Progress  # pylint: disable=import-outside-toplevel

    all_packages_url = f"{base_url}/simple/"
    cache_path = os.path.join(os.path.dirname(__file__), "cache")
    if not os.path.exists(cache_path):
        os.makedirs(cache_path)
    cache_file = os.path.join(os.path.dirname(__file__), "cache", "packages.txt")

    chunks = []
    with Progress(transient=True) as progress:
        response = requests.get(all_packages_url, stream=True)
        content_length = response.headers.get("content-length")
        if content_length is not None:
            total_length = int(content_length)
            task = progress.add_task(msg, total=total_length)
            for data in response.iter_content(chunk_size=32768):
                chunks.append(data)
                progress.advance(task, len(data))
            response_data = b"".join(chunks).decode("utf-8")
        else:
            response_data = response.content.decode("utf-8")

    import re  # pylint: disable=import-outside-toplevel

    packages = re.findall(r"<a[^>]*>([^<]+)<\/a>", response_data)
    with open(cache_file, "w", encoding="utf-8") as f:
        f.write("\n".join(packages))
    return packages



def fetch_comparison_data(package_name: str):
    if not package_name:
        return None

    # Parse version if present
    version = None
    if "==" in package_name:
        package_name, _, version = package_name.partition("==")

    url = f"{base_url}/pypi/{quote(package_name)}{f'/{quote(version)}' if version else ''}/json"
    try:
        response = session.get(url)
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
        parsed_data = json.loads(response.text)
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

    info = parsed_data.get("info", {})
    releases = parsed_data.get("releases", {})
    urls = parsed_data.get("urls", [])

    latest_version = info.get("version", "Unknown")

    # Extract release date
    release_date = "Unknown"
    from datetime import timezone  # pylint: disable=import-outside-toplevel
    try:
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
        pass

    # Extract Python version support
    python_version = info.get("requires_python") or "Unknown"

    # Extract GitHub repo URL
    import re  # pylint: disable=import-outside-toplevel
    repos = re.findall(
        r"https://(?:www\.)?github\.com/(?P<repo>[A-Za-z0-9_.-]{0,38}/[A-Za-z0-9_.-]{0,100})(?:\.git)?", str(info)
    )
    if len(repos) > 1 and "project_urls" in info:
        repos = list(
            set(
                re.findall(
                    r"https://(?:www\.)?github\.com/(?P<repo>[A-Za-z0-9_.-]{0,38}/[A-Za-z0-9_.-]{0,100})(?:\.git)?",
                    str(info["project_urls"]),
                )
            )
        )
    repo = remove_dot_git(repos[0]) if repos else None

    stars = "N/A"
    open_issues = "N/A"
    if repo:
        github_url = f"https://api.github.com/repos/{quote(repo)}"
        try:
            resp = session.get(github_url)
            if resp.status_code == 200:
                github_data = json.loads(resp.text)
                if not (github_data.get("message") and github_data["message"] == "Not Found"):
                    stars_val = github_data.get("stargazers_count")
                    issues_val = github_data.get("open_issues")
                    if stars_val is not None:
                        stars = f"{stars_val:,}"
                    if issues_val is not None:
                        open_issues = f"{issues_val:,}"
        except Exception as e:
            pass

    # Extract monthly downloads from pypistats
    downloads = "N/A"
    stats_url = f"https://pypistats.org/api/packages/{quote(package_name)}/recent"
    try:
        r = session.get(stats_url)
        if r.status_code == 200:
            parsed_stats = json.loads(r.text)
            if isinstance(parsed_stats, dict) and "data" in parsed_stats:
                last_month_downloads = parsed_stats["data"].get("last_month")
                if last_month_downloads is not None:
                    downloads = f"{last_month_downloads:,}"
    except Exception:
        pass

    return {
        "name": info.get("name", package_name),
        "version": latest_version,
        "release_date": release_date,
        "stars": stars,
        "open_issues": open_issues,
        "downloads": downloads,
        "python_version": python_version,
    }


def parse_requirements_txt(content: str):
    packages = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        if " #" in line:
            line = line.split(" #", 1)[0].strip()
        parts = []
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
            pass
    return packages


def parse_pyproject_toml(content: str):
    tomllib = None
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            try:
                import toml as tomllib
            except ImportError:
                pass

    if tomllib is None:
        return _fallback_parse_pyproject(content)

    try:
        data = tomllib.loads(content)
    except Exception:
        return []

    packages = []
    project = data.get("project", {})
    dependencies = project.get("dependencies", [])
    for dep in dependencies:
        try:
            from packaging.requirements import Requirement
            packages.append(Requirement(dep))
        except Exception:
            pass

    optional_dependencies = project.get("optional-dependencies", {})
    for group, deps in optional_dependencies.items():
        for dep in deps:
            try:
                from packaging.requirements import Requirement
                packages.append(Requirement(dep))
            except Exception:
                pass

    tool = data.get("tool", {})
    poetry = tool.get("poetry", {})

    poetry_deps = []
    if "dependencies" in poetry:
        poetry_deps.append(poetry["dependencies"])

    group_data = poetry.get("group", {})
    for group_name, group_val in group_data.items():
        if "dependencies" in group_val:
            poetry_deps.append(group_val["dependencies"])

    for dep_dict in poetry_deps:
        for pkg_name, val in dep_dict.items():
            if pkg_name.lower() == "python":
                continue
            if isinstance(val, dict):
                version_spec = val.get("version", "")
            else:
                version_spec = val

            req_str = pkg_name
            if version_spec:
                if version_spec == "*":
                    pass
                elif version_spec.startswith("^"):
                    v = version_spec[1:]
                    parts = v.split(".")
                    if parts[0] == "0" and len(parts) > 1:
                        upper = f"0.{int(parts[1])+1}.0"
                    else:
                        upper = f"{int(parts[0])+1}.0.0"
                    req_str = f"{pkg_name}>={v},<{upper}"
                elif version_spec.startswith("~"):
                    v = version_spec[1:]
                    parts = v.split(".")
                    if len(parts) > 1:
                        upper = f"{parts[0]}.{int(parts[1])+1}.0"
                    else:
                        upper = f"{int(parts[0])+1}.0.0"
                    req_str = f"{pkg_name}>={v},<{upper}"
                else:
                    if version_spec[0].isdigit():
                        req_str = f"{pkg_name}=={version_spec}"
                    else:
                        req_str = f"{pkg_name}{version_spec}"
            try:
                from packaging.requirements import Requirement
                packages.append(Requirement(req_str))
            except Exception:
                pass

    return packages


def _fallback_parse_pyproject(content: str):
    packages = []
    lines = content.splitlines()
    in_dependencies = False
    in_poetry_dependencies = False
    current_section = ""
    for line in lines:
        line_stripped = line.strip()
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
                    pass
            if "]" in line_stripped and not "[" in line_stripped:
                if current_section == "project":
                    in_dependencies = False
            continue

        if in_poetry_dependencies:
            if "=" in line_stripped:
                parts = line_stripped.split("=", 1)
                pkg_name = parts[0].strip().strip('"\'')
                if pkg_name.lower() == "python":
                    continue
                val = parts[1].strip()
                import re
                ver_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', val)
                if ver_match:
                    version_spec = ver_match.group(1)
                else:
                    str_match = re.search(r'^["\']([^"\']+)["\']', val)
                    version_spec = str_match.group(1) if str_match else ""

                req_str = pkg_name
                if version_spec:
                    if version_spec == "*":
                        pass
                    elif version_spec.startswith("^"):
                        v = version_spec[1:]
                        parts = v.split(".")
                        if parts[0] == "0" and len(parts) > 1:
                            upper = f"0.{int(parts[1])+1}.0"
                        else:
                            upper = f"{int(parts[0])+1}.0.0"
                        req_str = f"{pkg_name}>={v},<{upper}"
                    elif version_spec.startswith("~"):
                        v = version_spec[1:]
                        parts = v.split(".")
                        if len(parts) > 1:
                            upper = f"{parts[0]}.{int(parts[1])+1}.0"
                        else:
                            upper = f"{int(parts[0])+1}.0.0"
                        req_str = f"{pkg_name}>={v},<{upper}"
                    else:
                        if version_spec[0].isdigit():
                            req_str = f"{pkg_name}=={version_spec}"
                        else:
                            req_str = f"{pkg_name}{version_spec}"
                try:
                    from packaging.requirements import Requirement
                    packages.append(Requirement(req_str))
                except Exception:
                    pass
    return packages



def _refresh_cache():
    with console.status("Getting current cache"):
        old_cache = load_cache()
    new_cache = fill_cache(msg="Fetching new cache")
    changed = len(new_cache) - len(old_cache)
    console.print(f"[yellow]:repeat: Updated the cache, number of new packages till last refresh:[/] [red]{changed}[/]")


def _clear_cache():
    try:
        session.cache.clear()
    except AttributeError:
        pass
    else:
        console.print(f"[cyan]ℹ️ Info:[/] Emptied cache, now trying to delete the cache file")

    import os

    folder = os.path.join(os.path.dirname(__file__), "cache")
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path):
                with session.cache_disabled():
                    os.remove(file_path)
        except Exception as exc:
            console.print(f"[red]:x: Failed to delete {file_path}. Reason: {exc}[/]")


def _get_github_readme(repo):
    readme = session.get(f"https://api.github.com/repos/{repo}/readme").json()
    if readme.get("message") == "Not Found":
        console.print(f"[red]:x: Could not find readme for[/] [yellow]{repo}[/]")
        raise typer.Exit()
    msg = readme.get("message")
    if msg is not None and "API rate limit exceeded" in msg:
        console.print(f"[red]:x: API rate limit exceeded for GitHub[/]")
        raise typer.Exit()
    content = session.get(f"https://raw.githubusercontent.com/{repo}/master/{readme['path']}")
    if content.status_code == 200:
        if "API rate limit exceeded" in content.text:
            console.print(f"[red]:x: API rate limit exceeded for GitHub[/]")
            raise typer.Exit()
        return content.text, readme["path"]
    return None, None


def _format_xml_packages(url, title, pubmsg, show_author, hide_link, *, split_title=False):
    try:
        import bs4  # pylint: disable=import-outside-toplevel
    except ImportError:
        bs4 = None
    table = Table(title=title, show_lines=True)
    table.add_column("Index", style="magenta", header_style="bold magenta")
    table.add_column("Name", style="green", header_style="bold green")
    if show_author:
        table.add_column("Author", style="red", header_style="bold red")
    table.add_column("Description", style="white", header_style="bold white")
    if not hide_link:
        table.add_column("Link", style="cyan", header_style="bold blue")
    table.add_column(pubmsg, style="yellow", header_style="bold yellow")
    with console.status("Fetching packages"):
        response = session.get(url)
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

        date = utc_to_local(datetime.strptime(package.find("pubDate").text, "%a, %d %b %Y %H:%M:%S GMT"), timezone.utc)
        
        row = [f"{index}.", title]
        if show_author:
            row.append(author.text if author is not None else None)
        row.append(description.text if description is not None else "")
        if not hide_link:
            row.append(link)
        row.append(humanize.naturaltime(utc_to_local(date, timezone.utc)))
        table.add_row(*row)
    console.print(table)
    if not lxml:
        console.print(
            "[bold yellow]:warning: WARNING: There is a known bug that occurs when lxml is not installed. It"
            "doesn't show descriptions in some cases. Please install lxml using `pip install lxml`."
        )


def _get_package_dependencies(info: dict, requested_extras: set) -> list:
    """Parse requires_dist from package info, filtering by markers and extras.

    Returns a list of packaging.requirements.Requirement objects that apply
    to the current environment and the requested extras.
    """
    from packaging.requirements import Requirement  # pylint: disable=import-outside-toplevel

    requires_dist = info.get("requires_dist") or []
    deps = []
    for req_str in requires_dist:
        try:
            req = Requirement(req_str)
        except Exception:
            continue
        if req.marker:
            # Only include if marker evaluates for current env + requested extras
            extra_envs = [None] if not requested_extras else [None] + list(requested_extras)
            included = False
            for extra in extra_envs:
                env = {"extra": extra} if extra else {}
                try:
                    if req.marker.evaluate(env):
                        included = True
                        break
                except Exception:
                    pass
            if not included:
                continue
        deps.append(req)
    return deps



@app.command()
def description(
    package_name: str = Argument(..., help="Package to get the description for"),
    force_github: bool = Option(False, help="Forcefully get the description from github"),
    syntax_theme: str = Option("monokai", help="Override the default syntax highlighting theme"),
):
    """See the description for a package."""
    url = f"{base_url}/pypi/{quote(package_name)}/json"
    with console.status("Getting data from PyPI"):
        response = session.get(url)

    if response.status_code != 200:
        if response.status_code == 404:
            console.print(f"[red]:no_entry_sign: Project [green]{package_name}[/] not found[/]")
        console.print(f"[orange]:grey_exclamation: Some error occurred. response code {response.status_code}[/]")
        raise typer.Exit()

    parsed_data = json.loads(response.text)["info"]
    if force_github:
        import re  # pylint: disable=import-outside-toplevel

        repos = set(
            re.findall(r"https://(?:www\.)?github\.com/([A-Za-z0-9_.-]{0,38}/[A-Za-z0-9_.-]{0,100})", str(parsed_data))
        )
        if len(repos) > 1:
            console.print("[red]:warning: WARNING:[/] I found multiple github repos. ")
            import questionary  # pylint: disable=import-outside-toplevel

            repo = questionary.select(
                "Please specify the repo you want to use.",
                choices=[questionary.Choice([("cyan", r)]) for r in list(repos)],
            ).ask()
        elif len(repos) == 1:
            repo = next(iter(repos))
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
        import re  # pylint: disable=import-outside-toplevel

        repos = set(
            re.findall(r"https://(?:www\.)?github\.com/([A-Za-z0-9_.-]{0,38}/[A-Za-z0-9_.-]{0,100})", str(parsed_data))
        )
        if repos:
            if len(repos) == 1:
                repo = next(iter(repos))
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
):
    """See the top 40 newly added packages."""
    _format_xml_packages(
        f"{base_url}/rss/packages.xml", "Newly Added Packages", "Published At", show_author, hide_link, split_title=True
    )


@app.command()
def new_releases(
    show_author: bool = Option(False, metavar="author", help="Show the project author or not"),
    hide_link: bool = Option(False, metavar="link", help="Show the project link or not"),
):
    """See the top 100 newly updated packages."""
    _format_xml_packages(
        f"{base_url}/rss/updates.xml", "Newly Released Packages", "Released At", show_author, hide_link
    )


@app.command()
def largest_files():
    """See the top 100 projects with the largest file size."""
    import humanize  # pylint: disable=import-outside-toplevel

    headers = {"User-Agent": "wasi_master/pypi_cli", "Accept": "application/json"}
    url = f"{base_url}/stats/"
    with console.status("Loading largest files..."):
        response = session.get(url, headers=headers)
        print(response.text)
        data = json.loads(response.text)
    packages = data["top_packages"]
    packages = dict(sorted(packages.items(), key=lambda i: i[1]["size"], reverse=True))
    table = Table(title="Top packages on PyPI based on their size", show_lines=True)
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
):
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
        print(response.url)
        print(soup.prettify())
        if not result_list:
            comment = soup.select(
                "div.split-layout.split-layout--table.split-layout--wrap-on-tablet > div:nth-child(1) > p"
            )
            console.print(f"[bold]{' '.join(comment[0].get_text().split())}[/]")
            raise typer.Exit()

        results = [Package(i) for i in result_list.find_all("a", class_="package-snippet")]

        pagination = soup.find(class_="button-group--pagination")
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
    version: str = Option(None, help="The version of the package to show releases for"),
    show_links: bool = Option(False, metavar="link", help="Display the links to the releases"),
):
    """See all the available releases for a package.

    The --link argument can be used to also show the link of the releases.
    This is turned off by default and the link is added as a hyperlink to the package name on supported terminals
    """
    if not version and "==" in package_name:
        package_name, _, version = package_name.partition("==")
    url = f"{base_url}/pypi/{quote(package_name)}/json"
    with console.status("Getting data from PyPI"):
        response = session.get(url)

    if response.status_code != 200:
        if response.status_code == 404:
            console.print(f"[red]:no_entry_sign: Project [green]{package_name}[/] not found[/]")
        console.print(f"[orange]:grey_exclamation: Some error occurred. response code {response.status_code}[/]")
        raise typer.Exit()

    parsed_data = json.loads(response.text)
    import humanize  # pylint: disable=import-outside-toplevel

    table = Table()
    table.add_column("Version", style="green", header_style="green")
    table.add_column("Upload date", width=24, style="red", header_style="red")
    table.add_column("Size", style="yellow", header_style="yellow")
    if show_links is True:
        table.add_column("Link", style="cyan", header_style="blue")

    for version, releases in parsed_data["releases"].items():
        if not releases:
            table.add_row(version)
            continue
        release = releases[0]
        upload_time = _parse_iso_datetime(release["upload_time_iso_8601"])

        if show_links is True:
            table.add_row(
                f"[link={release['url']}] {version}[/]",
                upload_time.strftime("%c"),
                humanize.naturalsize(release["size"], binary=True),
                release["url"],
            )
        else:
            table.add_row(
                f"[link={release['url']}] {version}[/]",
                upload_time.strftime("%c"),
                humanize.naturalsize(release["size"], binary=True),
            )
    console.print(table)


@app.command()
def vulnerabilities(
    package_name: str = Argument(..., help="The name of the package to show vulnerabilities for"),
    version: str = Argument(..., help="The version of the package to show vulnerabilities for"),
):
    """See all the known vulnerabilities for a package."""

    url = f"{base_url}/pypi/{quote(package_name)}/{quote(version)}/json"
    with console.status("Getting data from PyPI"):
        response = session.get(url)

    if response.status_code != 200:
        if response.status_code == 404:
            console.print(f"[red]:no_entry_sign: Project [green]{package_name}[/] not found[/]")
        console.print(f"[orange]:grey_exclamation: Some error occurred. response code {response.status_code}[/]")
        raise typer.Exit()

    parsed_data = json.loads(response.text)
    vulnerabilities = parsed_data["vulnerabilities"]
    if not vulnerabilities:
        console.print(f"[green]:white_check_mark: No known vulnerabilities for {package_name} {version}[/]")
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
):
    """See detailed information about all the wheels of a release of a package"""
    if not version and "==" in package_name:
        package_name, _, version = package_name.partition("==")
    url = f"{base_url}/pypi/{quote(package_name)}{f'/{quote(version)}' if version else ''}/json"
    with console.status("Getting data from PyPI"):
        response = session.get(url)

    if response.status_code != 200:
        if response.status_code == 404:
            console.print("[red]:no_entry_sign: Project or version not found[/]")
        console.print(f"[orange]:grey_exclamation: Some error occurred. response code {response.status_code}[/]")
        raise typer.Exit()

    parsed_data = json.loads(response.text)

    from rich.text import Text  # pylint: disable=import-outside-toplevel
    import humanize  # pylint: disable=import-outside-toplevel

    data = parsed_data["urls"]

    from itertools import cycle  # pylint: disable=import-outside-toplevel

    colors = cycle(["green", "blue", "magenta", "cyan", "yellow", "red"])
    wheel_panels = []
    if supported_only:
        from packaging.tags import parse_tag, sys_tags  # pylint: disable=import-outside-toplevel
        from wheel_filename import InvalidFilenameError, parse_wheel_filename

        def is_wheel_supported(wheel):
            try:
                parsed_wheel_file = parse_wheel_filename(wheel["filename"])
            except InvalidFilenameError:
                return True
            for tag in parsed_wheel_file.tag_triples():
                if any(tag in sys_tags() for tag in list(parse_tag(tag))):
                    return True
            return False

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
):
    """Check a requirements.txt or pyproject.toml file for updates, wheel support, and abandoned packages."""
    import os  # pylint: disable=import-outside-toplevel
    from datetime import timezone  # pylint: disable=import-outside-toplevel
    from concurrent.futures import ThreadPoolExecutor  # pylint: disable=import-outside-toplevel
    from packaging.version import parse as parse_version  # pylint: disable=import-outside-toplevel
    from packaging.tags import parse_tag, sys_tags  # pylint: disable=import-outside-toplevel
    from wheel_filename import InvalidFilenameError, parse_wheel_filename  # pylint: disable=import-outside-toplevel
    import humanize  # pylint: disable=import-outside-toplevel

    if not os.path.exists(file_path):
        console.print(f"[red]:no_entry_sign: File [green]{file_path}[/] not found[/]")
        raise typer.Exit(code=1)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        console.print(f"[red]:no_entry_sign: Failed to read [green]{file_path}[/]: {e}[/]")
        raise typer.Exit(code=1)

    if file_path.endswith(".toml") or os.path.basename(file_path) == "pyproject.toml":
        requirements = parse_pyproject_toml(content)
    else:
        requirements = parse_requirements_txt(content)

    if not requirements:
        console.print("[yellow]:grey_exclamation: No requirements found to check.[/]")
        raise typer.Exit()

    seen = set()
    deduped_requirements = []
    for req in requirements:
        name_lower = req.name.lower()
        if name_lower not in seen:
            seen.add(name_lower)
            deduped_requirements.append(req)

    def extract_version(specifier):
        for spec in specifier:
            if spec.operator in ("==", "===", "~="):
                return spec.version
        for spec in specifier:
            if spec.operator in (">=", ">", "<=", "<", "!="):
                return spec.version
        return None

    def fetch_package_info(req):
        url = f"{base_url}/pypi/{quote(req.name)}/json"
        try:
            res = session.get(url)
            if res.status_code == 200:
                return req, json.loads(res.text)
            else:
                return req, res.status_code
        except Exception:
            return req, None

    results = []
    with console.status("Checking requirements against PyPI..."):
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(fetch_package_info, req) for req in deduped_requirements]
            for future in futures:
                try:
                    results.append(future.result())
                except Exception:
                    pass

    table = Table()
    table.add_column("Package", style="green", header_style="green")
    table.add_column("Specified", style="cyan", header_style="cyan")
    table.add_column("Latest", style="magenta", header_style="magenta")
    table.add_column("Wheel Support", header_style="yellow")
    table.add_column("Last Updated", header_style="blue")
    table.add_column("Status", header_style="red")

    def is_wheel_supported(wheel):
        try:
            parsed_wheel_file = parse_wheel_filename(wheel["filename"])
        except InvalidFilenameError:
            return True
        for tag in parsed_wheel_file.tag_triples():
            if any(tag in sys_tags() for tag in list(parse_tag(tag))):
                return True
        return False

    for req, data in results:
        specified = extract_version(req.specifier)
        specified_str = str(req.specifier) if req.specifier else "*"

        if data is None or isinstance(data, int):
            status_str = "[red]Not Found[/]" if data == 404 else "[orange]Error[/]"
            table.add_row(
                req.name,
                specified_str,
                "N/A",
                "N/A",
                "N/A",
                status_str,
            )
            continue

        info = data.get("info", {})
        latest_version = info.get("version", "Unknown")

        latest_dt = None
        for rel_list in data.get("releases", {}).values():
            for rel in rel_list:
                up_time = rel.get("upload_time_iso_8601")
                if up_time:
                    try:
                        dt = _parse_iso_datetime(up_time)
                        if latest_dt is None or dt > latest_dt:
                            latest_dt = dt
                    except Exception:
                        pass

        last_updated_str = "UNKNOWN"
        is_abandoned = False
        if latest_dt:
            if latest_dt.tzinfo is None:
                latest_dt = latest_dt.replace(tzinfo=timezone.utc)
            is_abandoned = (datetime.now(timezone.utc) - latest_dt).days > 730
            last_updated_str = humanize.naturaltime(utc_to_local(latest_dt, timezone.utc))

        files = None
        if specified and specified in data.get("releases", {}):
            files = data["releases"][specified]
        else:
            files = data.get("urls", [])

        wheel_status = "[green]Supported[/]"
        wheels = [f for f in files if f.get("packagetype") == "bdist_wheel" or f.get("filename", "").endswith(".whl")]
        if not wheels:
            wheel_status = "[yellow]No wheels[/]"
        elif not any(is_wheel_supported(w) for w in wheels):
            wheel_status = "[red]Unsupported[/]"

        status_parts = []
        is_outdated = False
        if specified:
            try:
                is_outdated = parse_version(latest_version) > parse_version(specified)
            except Exception:
                pass

        if is_abandoned:
            status_parts.append("[red][bold]Abandoned[/][/]")

        if is_outdated:
            status_parts.append("[yellow]Outdated[/]")

        if not status_parts:
            status_parts.append("[green]Up to date[/]")

        status_str = " & ".join(status_parts)

        table.add_row(
            req.name,
            specified_str,
            latest_version,
            wheel_status,
            last_updated_str,
            status_str,
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
):

    """See the information about a package."""
    if not version and "==" in package_name:
        package_name, _, version = package_name.partition("==")
    url = f"{base_url}/pypi/{quote(package_name)}{f'/{quote(version)}' if version else ''}/json"
    with console.status("Getting data from PyPI"):
        response = session.get(url)


    if response.status_code != 200:
        if response.status_code == 404:
            console.print(f"[red]:no_entry_sign: Project [green]{package_name}[/] not found[/]")
        console.print(f"[orange]:grey_exclamation: Some error occurred. response code {response.status_code}[/]")
        raise typer.Exit()

    parsed_data = json.loads(response.text)

    info = parsed_data["info"]
    releases = parsed_data.get("releases", {})
    urls = parsed_data["urls"]

    try:
        from packaging.version import parse as parse_version  # pylint:disable=import-outside-toplevel
    except ImportError:
        from distutils.version import LooseVersion as parse_version  # pylint:disable=import-outside-toplevel

    from datetime import timezone  # pylint: disable=import-outside-toplevel

    if urls:
        release_time = utc_to_local(
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
        version_comment = (
            "[green]Latest Version[/]"
            if str(latest_version) == str(info["version"])
            else f"[red]Newer version available ({latest_version})[/]"
        )
    else:
        version_comment = f"[green]Version[/]: {version}"

    import re  # pylint: disable=import-outside-toplevel

    repos = re.findall(
        r"https://(?:www\.)?github\.com/(?P<repo>[A-Za-z0-9_.-]{0,38}/[A-Za-z0-9_.-]{0,100})(?:\.git)?", str(info)
    )
    if len(repos) > 1:
        repos = list(
            set(
                re.findall(
                    r"https://(?:www\.)?github\.com/(?P<repo>[A-Za-z0-9_.-]{0,38}/[A-Za-z0-9_.-]{0,100})(?:\.git)?",
                    str(info["project_urls"]),
                )
            )
        )
    repo = remove_dot_git(repos[0]) if repos else None

    from rich.text import Text  # pylint:disable=import-outside-toplevel

    title = Text.from_markup(f"[bold cyan]{info['name']} {info['version']}[/]\n{description}", justify="left")
    message = Text.from_markup(f"{version_comment}\nReleased: {natural_time}", justify="right")
    table = Table.grid(expand=True)
    table.add_column(justify="left")
    table.add_column(justify="right")
    table.add_row(title, message)

    metadata = Table.grid()
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
            with console.status("Getting data from GitHub"):
                resp = session.get(url)
            if resp.status_code == 200:
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
        with console.status("Getting statistics from PyPI Stats"):
            r = session.get(stats_url)
        try:
            parsed_stats = json.loads(r.text)
            if not isinstance(parsed_stats, dict):
                parsed_stats = None
        except (json.JSONDecodeError, AssertionError, ValueError):
            parsed_stats = None

        stats = parsed_stats["data"] if parsed_stats else None
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
        reqs = ""
        for req in info["requires_dist"] or []:
            reqs += f"{req}\n"
        requirements = Text(reqs or "No requirements found")
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
        if parsed_data.get("ownership"):
            ownership_information = ""
            roles = parsed_data['ownership'].get("roles", [])
            for n, role in enumerate(roles, start=1):
                ownership_information += f"[dark_goldenrod]{role['role']}{f' #{n}' if len(roles) > 1 else ''}:[/] {role['user']}\n"
            if parsed_data.get("ownership").get("organization"):
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
    MIN_SIDEBAR_WIDTH = 30
    MIN_DESC_WIDTH = 45

    # Measure metadata width
    measurement = console.measure(metadata)
    max_needed = measurement.maximum

    if console.width < MIN_SIDEBAR_WIDTH + MIN_DESC_WIDTH:
        use_stacked = True
        measure_width = console.width
    else:
        use_stacked = False
        sidebar_width = min(max_needed, console.width - MIN_DESC_WIDTH, console.width // 2)
        sidebar_width = max(sidebar_width, min(max_needed, MIN_SIDEBAR_WIDTH))
        measure_width = sidebar_width

    # Measure metadata height to dynamically size the description
    from io import StringIO  # pylint: disable=import-outside-toplevel
    from rich.console import Console as _Console  # pylint: disable=import-outside-toplevel

    _buf = StringIO()
    _temp = _Console(file=_buf, width=measure_width)
    _temp.print(metadata)
    metadata_height = _buf.getvalue().count("\n")
    max_desc_lines = max(40, metadata_height)

    # Truncate the raw description source if needed
    truncation_notice = False
    desc_source = info["description"] or ""
    if not full_description:
        lines = desc_source.splitlines()
        if len(lines) > max_desc_lines:
            desc_source = "\n".join(lines[:max_desc_lines])
            truncation_notice = True

    if info["description_content_type"] == "text/markdown":
        from rich.markdown import Markdown  # pylint: disable=import-outside-toplevel

        desc_renderable = Markdown(desc_source)
    elif info["description_content_type"] == "text/x-rst":
        from rich_rst import RestructuredText  # pylint: disable=import-outside-toplevel

        desc_renderable = RestructuredText(desc_source)
    else:
        from rich.text import Text  # pylint: disable=import-outside-toplevel

        desc_renderable = Text(desc_source)

    from rich.console import Group  # pylint: disable=import-outside-toplevel

    if truncation_notice:
        from rich.text import Text  # pylint: disable=import-outside-toplevel

        notice = Text(
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
        side_by_side = Table.grid(padding=0)
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
    packages = load_cache()

    import re  # pylint: disable=import-outside-toplevel

    # We explicitly set the limit to unlimited if it's -1
    limit = float('inf') if limit == -1 else limit

    # We compile the regex because it's twice as fast (https://imgur.com/a/MoUyEMg)
    _regex = re.compile(regex)
    if compact:
        matches = []
        for package in packages:
            if _regex.match(package):
                matches.append(f"[link={base_url}/project/{package}]{package}[/]")
                if len(matches) >= limit:
                    break
        console.print(", ".join(matches))
    else:
        table = Table(show_header=True, show_lines=True)
        table.add_column("[purple]No.[/]", style="purple")
        table.add_column("[green]Package[/]")
        table.add_column("[blue]Link[/]", style="cyan")
        matches = 0
        for package in packages:
            if _regex.match(package):
                matches += 1
                if matches > limit:
                    break
                table.add_row(
                    f"{matches}.",
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
):
    """Search the documentation for an item of a package."""
    import webbrowser  # pylint: disable=import-outside-toplevel

    docs_mapping = {
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

    if package_name[:4] == "http":
        url = package_name
    else:
        if package_name in docs_mapping:
            url = docs_mapping[package_name]
        else:
            import questionary  # pylint: disable=import-outside-toplevel

            resp = questionary.confirm(
                "Docs not available. Do you want to search pypi to find the documentation?"
            ).ask()
            if resp:
                url = f"{base_url}/pypi/{quote(package_name)}/json"
                with console.status("Getting data from PyPI"):
                    response = session.get(url)

                if response.status_code != 200:
                    if response.status_code == 404:
                        console.print(f"[red]:no_entry_sign: Project [green]{package_name}[/] not found[/]")
                    console.print(
                        f"[orange]:grey_exclamation: Some error occurred. response code {response.status_code}[/]"
                    )
                    raise typer.Exit()

                parsed_data = json.loads(response.text)
                url = parsed_data["info"].get("project_urls", {}).get("Documentation", None)
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
    search_page = url + "?q=" + quote(query)
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
):
    """Browse for a package's URLs"""
    import webbrowser  # pylint: disable=import-outside-toplevel

    import questionary  # pylint: disable=import-outside-toplevel

    link_style = questionary.Style([("name", "bold red"), ("separator", "gray"), ("url", "cyan")])

    url = f"{base_url}/pypi/{quote(package_name)}/json"

    with console.status("Getting data from PyPI"):
        response = session.get(url)

    if response.status_code != 200:
        if response.status_code == 404:
            console.print(f"[red]:no_entry_sign: Project [green]{package_name}[/] not found[/]")
        console.print(f"[orange]:grey_exclamation: Some error occurred. response code {response.status_code}[/]")
        raise typer.Exit()

    parsed_data = json.loads(response.text)
    info = parsed_data["info"]

    urls = info["project_urls"]
    urls["Project URL"] = info.get("project_url")
    urls["Home Page"] = info.get("project_url")
    urls["Release URL"] = info.get("release_url")
    urls["Mail to"] = ("mailto:" + info["maintainer_email"]) if info.get("maintainer_email") else None

    if url_only:
        console.print("\n".join(f"[red]{name:15}[/] [grey46]-[/] [cyan]{url}[/]" for name, url in urls.items() if url))
        raise typer.Exit()

    answer = questionary.select(
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
def cache_refresh():
    """Refresh the cache."""
    _refresh_cache()


@app.command()
def cache_clear():
    """Clear the cache."""
    _clear_cache()


@app.command()
def cache_info():
    """See information about the cache"""
    import os.path  # pylint: disable=import-outside-toplevel
    import humanize  # pylint: disable=import-outside-toplevel

    packages_cache = os.path.join(os.path.dirname(__file__), "cache", "packages.txt")
    requests_cache = os.path.join(os.path.dirname(__file__), "cache", "requests.sqlite")
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

    if requests_size:
        table = Table(title="All cached requests")
        table.add_column("Index", style="dim magenta", header_style="bold magenta")
        table.add_column("Link", style="cyan", header_style="bold cyan")
        table.add_column("Created", style="green", header_style="bold green")
        table.add_column("Expires", style="green", header_style="bold green")
        for n, response in enumerate(session.cache.values()):
            table.add_row(
                f"{n}.", response.url, humanize.naturaltime(response.created_at), humanize.naturaltime(response.expires)
            )
        console.print(table)


@app.command()
def version(
    package_name: str = Argument(
        None, help="The name or link to the docs of the package to show the documentation for"
    ),
    limit: int = Option(10, help="Limit the number of versions to show"),
    no_pre_releases: bool = Option(False, help="If set then it will not show pre-releases"),
    show_installed_version: bool = Option(False, help="If set then it will show the version that is installed too"),
):
    """Show the cli's or another package's version and exit"""
    if not package_name:
        import sys
        from .__init__ import __version__  # pylint: disable=import-outside-toplevel

        console.print(f"Python version: {sys.version}")
        console.print(f"Current version of [yellow]pypi-command-line[/] is [red]{__version__}[/]")
        with console.status("Getting latest version"):
            latest_version = get_latest_version()
        console.print(f"Latest  version of [yellow]pypi-command-line[/] is [red]{latest_version}[/]")
        raise typer.Exit()

    url = f"{base_url}/pypi/{quote(package_name)}/json"
    with console.status("Getting latest versions from PyPI"):
        response = session.get(url)

    if response.status_code != 200:
        if response.status_code == 404:
            console.print(f"[red]:no_entry_sign: Project [green]{package_name}[/] not found[/]")
        console.print(f"[orange]:grey_exclamation: Some error occurred. response code {response.status_code}[/]")
        raise typer.Exit()

    parsed_data = json.loads(response.text)

    try:
        from packaging.version import parse as parse_version  # pylint:disable=import-outside-toplevel
    except ImportError:
        if no_pre_releases:
            console.print(
                "[red]:no_entry_sign: Install packaging (`pip install packaging`) to use the --no-pre-releases flag[/]"
            )
            raise typer.Exit()
        from distutils.version import LooseVersion as parse_version  # pylint:disable=import-outside-toplevel

    versions = map(parse_version, parsed_data["releases"].keys())
    if no_pre_releases:
        versions = filter(lambda x: not x.is_prerelease, versions)
    latest_versions = sorted(versions, reverse=True)[:limit]

    minimal_output = limit == 1

    if minimal_output:
        output = f"[green]{package_name}[/] -"
    else:
        version_info = ""
        if show_installed_version:
            import pkg_resources

            try:
                installed_version = pkg_resources.get_distribution(package_name).version
            except Exception:
                version_info = " [red](Not Installed)[/]"
            else:
                version_info = f" [dark_orange](Installed Version: {installed_version})[/]"
        output = f"Top {limit} latest versions of [green]{package_name}[/]{version_info}{' [yellow](excluding pre-releases)[/]' if no_pre_releases else ''}:\n"

    from datetime import timezone  # pylint: disable=import-outside-toplevel
    import humanize  # pylint: disable=import-outside-toplevel

    for n, version in enumerate(latest_versions, start=1):
        output += f" {f'[magenta]{n}.[/] ' if not minimal_output else ''}"

        if limit == 1 and show_installed_version:
            import pkg_resources

            try:
                installed_version = pkg_resources.get_distribution(package_name).version
            except Exception:
                output += f"[blue]{version}[/]"
            else:
                output += f"[yellow]{installed_version}[/]->[blue]{version}[/]"
        else:
            output += f"[blue]{version}[/]"

        try:
            upload_time = utc_to_local(
                _parse_iso_datetime(parsed_data["releases"][str(version)][0]["upload_time_iso_8601"]),
                timezone.utc,
            )
            output += f" [red]{humanize.naturaltime(upload_time)}[/] [cyan]({upload_time.strftime('%a %b %d %H:%M:%S %Y')})[/]"
        except Exception as e:
            print(e)
        finally:
            output += "\n"
    console.print(output.strip())

@app.command()
def compare(
    package_names: list[str] = Argument(..., help="The names of the packages to compare"),
):
    """Compare multiple packages side-by-side."""
    from concurrent.futures import ThreadPoolExecutor  # pylint: disable=import-outside-toplevel

    with console.status("Fetching comparison data..."):
        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(fetch_comparison_data, package_names))

    table = Table(
        title="[bold]PyPI Package Comparison[/bold]",
        show_header=True,
        show_lines=True,
    )

    table.add_column("[cyan]Metric[/]", style="cyan", header_style="cyan")
    for pkg in results:
        table.add_column(f"[green]{pkg['name']}[/]", justify="center", style="white")

    metrics = [
        ("Latest Version", "version"),
        ("Latest Release", "release_date"),
        ("GitHub Stars", "stars"),
        ("Open Issues", "open_issues"),
        ("Downloads (Month)", "downloads"),
        ("Requires Python", "python_version"),
    ]

    for metric_name, key in metrics:
        row = [metric_name]
        for pkg in results:
            row.append(pkg[key])
        table.add_row(*row)

    console.print(table)

@app.command()
def dependencies(
    package_name: str = Argument(..., help="The name of the package to explore (e.g. [green]requests[/] or [green]requests[security][/])"),
    level: int = Option(5, "--level", "-l", help="Maximum depth of the dependency tree to display", show_default=True),
    no_cache: bool = Option(False, "--no-cache", help="Bypass cache when fetching dependency data"),
):
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
    root_extras: set = set()
    bracket_pos = package_name.find("[")
    if bracket_pos != -1 and package_name.endswith("]"):
        root_extras = {e.strip() for e in package_name[bracket_pos + 1 : -1].split(",")}
        package_name = package_name[:bracket_pos]

    # ── Cache for fetched metadata ────────────────────────────────────────────
    # Maps lowercase package name → parsed JSON info dict (or None on failure)
    fetched: dict[str, dict | None] = {}

    # ── Fetch helper ─────────────────────────────────────────────────────────
    def fetch_info(name: str) -> tuple[str, dict | None]:
        """Fetch /pypi/<name>/json from PyPI; return (name, info_dict or None)."""
        _session = session
        if no_cache:
            from requests import Session  # pylint: disable=import-outside-toplevel
            s = Session()
            s.headers.update({"User-Agent": "wasi_master/pypi_cli", "Accept": "application/json"})
            _session = s
        try:
            url = f"{base_url}/pypi/{quote(name)}/json"
            resp = _session.get(url)
            if resp.status_code == 200:
                data = json.loads(resp.text)
                return name.lower(), data.get("info")
            return name.lower(), None
        except Exception:
            return name.lower(), None

    # ── Formatting helpers ────────────────────────────────────────────────────
    def _format_req_label(req: Requirement) -> Text:
        """Return a styled rich Text label for a single Requirement."""
        t = Text()
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
    root_label = Text()
    root_label.append("📦 ", style="")
    root_label.append(root_info["name"], style="bold #4AA0FC")      # blue
    root_label.append(f" {root_info['version']}", style="bold #F2C259")  # gold
    if root_extras:
        root_label.append("[", style="#9263FB")
        root_label.append(", ".join(sorted(root_extras)), style="#9263FB")
        root_label.append("]", style="#9263FB")
    if root_info.get("summary"):
        root_label.append(f"  {root_info['summary'][:60]}", style="dim")

    tree = Tree(root_label, guide_style="dim cyan")

    # ── BFS queue: each entry is (parent_rich_node, req, extras, current_depth)
    # We group by level to enable concurrent fetching at each level.
    # queue items: (parent_node, req_object, extras_set, depth)
    Level = list  # alias for readability
    current_level_items: Level = [
        (tree, req, req.extras or set(), 1)
        for req in _get_package_dependencies(root_info, root_extras)
    ]

    # Track visited to avoid infinite loops (circular deps)
    visited: set[str] = {package_name.lower()}

    for depth in range(1, level + 1):
        if not current_level_items:
            break

        # Collect names we still need to fetch at this level
        names_to_fetch = [
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
                    for name, info in executor.map(fetch_info, names_to_fetch):
                        fetched[name] = info

        next_level_items: Level = []

        for parent_node, req, req_extras, _ in current_level_items:
            pkg_key = req.name.lower()
            info = fetched.get(pkg_key)

            if pkg_key in visited:
                # Circular dependency — show it but don't recurse further
                circ_label = Text()
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
                err_label = Text()
                err_label.append("❌ ", style="")
                err_label.append(req.name, style="bold red")
                if req.specifier:
                    err_label.append(str(req.specifier), style="#33F1C8")
                err_label.append("  (not found)", style="dim red")
                parent_node.add(err_label)
                continue

            # Build label with resolved version
            node_label = Text()
            node_label.append("📦 " if depth == 1 else "  ", style="")
            node_label.append(req.name, style="bold #92EC5A")
            if req_extras:
                node_label.append("[", style="#9263FB")
                node_label.append(", ".join(sorted(req_extras)), style="#9263FB")
                node_label.append("]", style="#9263FB")
            if req.specifier:
                node_label.append(str(req.specifier), style="#33F1C8")
            # Show resolved version dimly
            resolved_ver = info.get("version", "?")
            node_label.append(f"  → {resolved_ver}", style="dim #4AA0FC")
            if req.marker:
                node_label.append(f"  ; {req.marker}", style="dim #F2C259")

            child_node = parent_node.add(node_label)

            # Queue children for the next level (if we haven't hit max depth)
            if depth < level:
                child_deps = _get_package_dependencies(info, req_extras)
                for child_req in child_deps:
                    next_level_items.append((child_node, child_req, child_req.extras or set(), depth + 1))

        current_level_items = next_level_items

    # ── Final summary line ────────────────────────────────────────────────────
    total_pkgs = len(visited) - 1  # exclude root itself
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
    repository: str = Option(None, help="The repository to fetch the information from"),
):
    """
    A beautiful command line interface for the Python Package Index
    """
    if not cache:
        from requests import Session

        global session
        session = Session()
        session.headers.update({"User-Agent": "wasi_master/pypi_cli", "Accept": "application/json"})
    if repository:
        global base_url
        if repository == "testpypi":
            base_url = "https://test.pypi.org"
        else:
            base_url = repository


def run():
    """Redefine typer.run() to use our custom Typer class."""  # noqa D402
    app()



if __name__ == "__main__":
    run()
