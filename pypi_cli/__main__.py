"""The main file."""
import json
from datetime import datetime
from urllib.parse import quote

import click
import humanize
import rich
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme
from typer import Argument, Option

try:
    import click_help_colors
    from click_help_colors import HelpColorsCommand, HelpColorsGroup
except ImportError:
    click_help_colors = None

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
                return

    click.exceptions.UsageError.show = show


if click_help_colors is not None:

    class CustomHelpColorsGroup(HelpColorsGroup):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self.help_headers_color = "red"
            self.help_options_color = "yellow"
            self.context_settings = {"help_option_names": ["-h", "--help"]}

    class CustomHelpColorsCommand(HelpColorsCommand):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self.help_headers_color = "red"
            self.help_options_color = "yellow"

    Group = CustomHelpColorsGroup
    Command = CustomHelpColorsCommand
else:
    Group = click.Group
    Command = click.Command


class AliasedGroup(Group):
    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        alias_mapping = {**dict.fromkeys(["rtd", "docs", "documentation"], "read-the-docs"), "rs": "rsearch"}
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
    """A custom subclassed version of typer.Typer to allow colored help"""

    def __init__(self, *args, cls=AliasedGroup, **kwargs) -> None:
        super().__init__(*args, cls=cls, **kwargs)

    def command(self, *args, cls=Command, **kwargs) -> typer.Typer.command:
        return super().command(*args, cls=cls, **kwargs)


# We instantiate a cutom typer app
app = PypiTyper()
console = Console(
    theme=Theme(
        {
            "markdown.link": "#6088ff",
            "wheel.distribution": "#92EC5A",
            "wheel.version": "#F2C259",
            "wheel.build_tag": "#FFF075",
            "wheel.python_tag": "#FF6EF8",
            "wheel.abi_tag": "#9263FB",
            "wheel.platform_tag": "#33F1C8",
            "wheel.file_extension": "#4AA0FC",
        }
    ),
    emoji=True,
    emoji_variant="emoji",
    tab_size=4,
)
__color_error_message()  # makes the error messages colored


class Package:
    """Represents a package gotten from scraping the search results."""

    __slots__ = ("name", "version", "date", "released", "description")

    def __init__(self, soup):
        """Instantiate a package object gotten from scraping the search results.

        Parameters
        ----------
        soup : bs4.BeautifulSoup
            The soup that was gotten from PyPI
        """
        self.name = soup.find(class_="package-snippet__name").get_text()
        self.version = soup.find(class_="package-snippet__version").get_text()
        time = soup.find(class_="package-snippet__released")
        self.date = time.get_text().strip()
        self.released = datetime.strptime(time.find("time")["datetime"][:-5], "%Y-%m-%dT%H:%M:%S")
        self.name = soup.find(class_="package-snippet__name").get_text()
        self.description = soup.find(class_="package-snippet__description").get_text()


def utc_to_local(utc_dt, tzinfo):
    """Convert a datetime from utc to local time."""
    return utc_dt.replace(tzinfo=tzinfo).astimezone(tz=None).replace(tzinfo=None)


def remove_dot_git(text):
    """Remove the .git suffix from a URL."""
    if text.endswith(".git"):
        return text[:-4]
    return text


def _format_classifiers(_classifiers: str):
    """Format classifiers gotten from the API."""
    classifier_dict = {}
    output = ""
    for classifier in _classifiers.splitlines():
        topic, content = map(str.strip, classifier.split("::", 1))
        try:
            classifier_dict[topic].append(content)
        except KeyError:
            classifier_dict[topic] = [content]
    for topic, classifiers in classifier_dict.items():
        output += f"[bold]{topic}[/]\n"
        for classifier in classifiers:
            output += f"  {classifier}\n"
    return output


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
        with open(cache_file, "r") as cache_file:
            return cache_file.read().splitlines()


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

    with Progress(transient=True) as progress:
        response = requests.get(all_packages_url, stream=True)
        response_data = ""
        content_length = response.headers.get("content-length")
        if content_length is not None:
            total_length = int(content_length)
            task = progress.add_task(msg, total=total_length)
            downloaded = 0
            for data in response.iter_content(chunk_size=32768):
                downloaded += len(data)
                response_data += data.decode("utf-8")
                progress.advance(task, 32768)
        else:
            response_data = response.content.decode("utf-8")

    import re  # pylint: disable=import-outside-toplevel

    packages = re.findall(r"<a[^>]*>([^<]+)<\/a>", response_data)
    with open(cache_file, "w", encoding="utf-8") as cache_file:
        cache_file.write("\n".join(packages))
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
    import os
    import shutil

    folder = os.path.join(os.path.dirname(__file__), "cache")
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as exc:
            console.print(f"[red]:x: Failed to delete {file_path}. Reason: {exc}[/]")


def _get_github_readme(repo):
    readme = session.get(f"https://api.github.com/repos/{repo}/readme").json()
    if readme.get("message") == "Not Found":
        console.print(f"[red]:x: Could not find readme for[/] [yellow]{repo}[/]")
        raise typer.Exit()
    content = session.get(f"https://raw.githubusercontent.com/{repo}/master/{readme['path']}")
    if content.status_code == 200:
        return content.text, readme["path"]
    return None, None


def _format_xml_packages(url, title, pubmsg, _author, _link, *, split_title=False):
    try:
        import bs4  # pylint: disable=import-outside-toplevel
    except ImportError:
        bs4 = None
    table = Table(title=title, show_lines=True)
    table.add_column("Index", style="magenta", header_style="bold magenta")
    table.add_column("Name", style="green", header_style="bold green")
    if _author:
        table.add_column("Author", style="red", header_style="bold red")
    table.add_column("Description", style="white", header_style="bold white")
    if _link:
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

    for index, package in enumerate(soup.find_all("item") if lxml else soup.iter("item"), 1):
        title = package.find("title").text
        if split_title:
            title = title.split()[0]
        author = package.find("author")
        description = package.find("description")
        link = package.find("link").text

        date = utc_to_local(datetime.strptime(package.find("pubDate").text, "%a, %d %b %Y %H:%M:%S GMT"), timezone.utc)
        if _link and _author:
            table.add_row(
                f"{index}.",
                title,
                author.text if author else None,
                description.text if description else "",
                link,
                humanize.naturaltime(utc_to_local(date, timezone.utc)),
            )
        elif _link and not _author:
            table.add_row(
                f"{index}.",
                title,
                description.text if description else "",
                link,
                humanize.naturaltime(utc_to_local(date, timezone.utc)),
            )
        elif not _link and not _author:
            table.add_row(
                f"{index}.",
                title,
                description.text if description else "",
                humanize.naturaltime(utc_to_local(date, timezone.utc)),
            )
    console.print(table)
    if not lxml:
        console.print(
            "[bold yellow]:warning: WARNING: There is a known bug that occurs when lxml is not installed. It"
            "doesn't show descriptions in some cases. Please install lxml using `pip install lxml`."
        )


@app.command()
def description(
    package_name: str = Argument(..., help="Package to get the description for"),
    force_github: bool = Option(False, help="Forcefully get the description from github"),
):
    """See the description for a package."""
    url = f"{base_url}/pypi/{quote(package_name)}/json"
    with console.status("Getting data from PyPI"):
        response = session.get(url)

    if response.status_code != 200:
        if response.status_code == 404:
            rich.print("[red]:no_entry_sign: Project not found[/]")
        rich.print(f"[orange]:grey_exclamation: Some error occured. response code {response.status_code}[/]")
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
                console.print(f"[yellow]ℹ️ INFO:[/] However, I did find a github repo[/] https://github.com/{repo}.\n")

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
                    "Please specify the repo you want to see the descripton from (Ctrl+C to cancel).",
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

        description = Markdown(parsed_data["description"])
    elif parsed_data["description_content_type"] == "text/x-rst":
        from rich_rst import RestructuredText  # pylint: disable=import-outside-toplevel

        description = RestructuredText(parsed_data["description"])
    else:
        from rich.text import Text  # pylint: disable=import-outside-toplevel

        description = Text(parsed_data["description"])
    console.print(Panel(description, title=f"Description for {package_name}", border_style="bold magenta"))


@app.command()
def new_packages(
    _author: bool = Option(False, metavar="author", help="Show the project author or not"),
    _link: bool = Option(True, metavar="link", help="Show the project link or not"),
):
    """See the top 40 newly added packages."""
    _format_xml_packages(
        f"{base_url}/rss/packages.xml", "Newly Added Packages", "Published At", _author, _link, split_title=True
    )


@app.command()
def new_releases(
    _author: bool = Option(False, metavar="author", help="Show the project author or not"),
    _link: bool = Option(True, metavar="link", help="Show the project link or not"),
):
    """See the top 100 newly updated packages."""
    _format_xml_packages(f"{base_url}/rss/updates.xml", "Newly Released Packages", "Released At", _author, _link)


@app.command()
def largest_files():
    """See the top 100 projects with the largest file size."""

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
    """Search for a package on PyPI."""
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
        result_list = soup.find(attrs={"aria-label": "Search results"}, class_="unstyled")
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
    table.add_column("[white]Version[/]", style="bright_black")
    table.add_column("[green]Name[/]", justify="center", style="green")
    table.add_column("[yellow]Description[/]", justify="center", style="white")
    table.add_column("[cyan]Release date[/]", justify="right", style="cyan")

    for index, package in enumerate(results, 1):
        table.add_row(
            f"{index}.",
            package.version,
            f"[link={base_url}/project/{package.name}]{package.name}[/]",
            package.description,
            package.date,
        )
    console.print(table)


@app.command()
def releases(
    package_name: str = Argument(
        ...,
        help="The name of package to show releases for, this can "
        "also include the version with this syntax: `package_name==version`",
    ),
    version: str = Option(None, help="The version of the package to show releases for"),
    _link: bool = Option(False, metavar="link", help="Display the links to the releases"),
):
    """See all the available releases for a package.

    The --link argument can be used to also show the link of the releases.
    This is turned off by default and the link is added as a hyperlink to the package name on supported terminals
    """
    if not version and "==" in package_name:
        package_name, _, version = package_name.partition("==")
    url = f"{base_url}/pypi/{quote(package_name)}{f'/{quote(version)}' if version else ''}/json"
    with console.status("Getting data from PyPI"):
        response = session.get(url)

    if response.status_code != 200:
        if response.status_code == 404:
            rich.print("[red]:no_entry_sign: Project not found[/]")
        rich.print(f"[orange]:grey_exclamation: Some error occured. response code {response.status_code}[/]")
        raise typer.Exit()

    parsed_data = json.loads(response.text)

    table = Table()
    table.add_column("Version", style="green", header_style="green")
    table.add_column("Upload date", width=24, style="red", header_style="red")
    table.add_column("Size", style="yellow", header_style="yellow")
    if _link is True:
        table.add_column("Link", style="cyan", header_style="blue")

    for version, releases in parsed_data["releases"].items():
        if not releases:
            table.add_row(version)
            continue
        release = releases[0]
        try:
            upload_time = datetime.strptime(release["upload_time_iso_8601"], "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            upload_time = datetime.strptime(release["upload_time_iso_8601"], "%Y-%m-%dT%H:%M:%SZ")

        if _link is True:
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
            rich.print("[red]:no_entry_sign: Project or version not found[/]")
        rich.print(f"[orange]:grey_exclamation: Some error occured. response code {response.status_code}[/]")
        raise typer.Exit()

    parsed_data = json.loads(response.text)

    from packaging.version import parse as parse_version  # pylint: disable=import-outside-toplevel
    from rich.text import Text  # pylint: disable=import-outside-toplevel

    # def is_wheel_supported(wheel_name):
    #     try:
    #         tag = parse_tag("-".join(wheel_name.split("-")[2:]))
    #     except Exception as e:
    #         return "white"
    #     if not tag:
    #         return "white"
    #     else:
    #         if list(tag)[-1] in sys_tags():
    #             return "green"
    #         else:
    #             return "red"

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
                            f"[red]Upload Time[/]: {humanize.naturaltime(utc_to_local(datetime.strptime(wheel['upload_time_iso_8601'], '%Y-%m-%dT%H:%M:%S.%fZ'), timezone.utc))}",
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
def information(
    package_name: str = Argument(..., help="The name of the package to show information for"),
    version: str = Option(None, help="The version of the package to show info for"),
    show_classifiers: bool = Option(False, metavar="classifiers", help="Show the classifiers"),
    hide_project_urls: bool = Option(False, metavar="project_urls", help="Hide the project urls"),
    hide_requirements: bool = Option(False, metavar="requirements", help="Hide the requirements"),
    hide_github: bool = Option(False, metavar="github", help="Hide the github"),
    hide_stats: bool = Option(False, metavar="stats", help="Hide the stats"),
    hide_meta: bool = Option(False, metavar="meta", help="Hide the metadata"),
):
    """See the information about a package."""
    if not version and "==" in package_name:
        package_name, _, version = package_name.partition("==")
    url = f"{base_url}/pypi/{quote(package_name)}{f'/{quote(version)}' if version else ''}/json"
    with console.status("Getting data from PyPI"):
        response = session.get(url)

    if response.status_code != 200:
        if response.status_code == 404:
            rich.print("[red]:no_entry_sign: Project not found[/]")
        rich.print(f"[orange]:grey_exclamation: Some error occured. response code {response.status_code}[/]")
        raise typer.Exit()

    parsed_data = json.loads(response.text)

    info = parsed_data["info"]
    releases = parsed_data["releases"]
    urls = parsed_data["urls"]

    try:
        from packaging.version import parse as parse_version  # pylint:disable=import-outside-toplevel
    except ImportError:
        from distutils.version import LooseVersion as parse_version  # pylint:disable=import-outside-toplevel

    # HACK: should use fromisotime
    release_time = datetime.strptime(urls[-1]["upload_time_iso_8601"], "%Y-%m-%dT%H:%M:%S.%fZ")
    natural_time = release_time.strftime("%b %d, %Y")
    description = info["summary"]
    latest_version = list(sorted(map(parse_version, releases.keys()), reverse=True))[0]
    version_comment = (
        "[green]Latest Version[/]"
        if str(latest_version) == str(info["version"])
        else f"[red]Newer version available ({latest_version})[/]"
    )
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
                "\n".join(f"[yellow]{name}[/]: [cyan]{url}[/]" for name, url in info["project_urls"].items()),
                expand=False,
                border_style="magenta",
                title="Project URLs",
            )
        )
    if not hide_github:
        if repo:
            url = f"https://api.github.com/repos/{quote(repo)}"
            with console.status("Getting data from GitHub"):
                resp = session.get(url)
            github_data = json.loads(resp.text)
            if github_data.get("message") and github_data["message"] == "Not Found":
                metadata.add_row(
                    Panel(
                        f"[red underline]Repo Not Found[/]\n[cyan]Link[/]: {url}\n[light_green]Name[/]: {repo}\n",
                        expand=False,
                        border_style="green",
                        title="GitHub",
                    )
                )
            else:
                size = github_data["size"]
                stars = github_data["stargazers_count"]
                forks = github_data["forks_count"]
                issues = github_data["open_issues"]
                metadata.add_row(
                    Panel(
                        f"[light_green]Name[/]: [link=https://github.com/{repo}]{repo}[/]\n"
                        f"[light_green]Size[/]: {size:,} KB\n"
                        f"[light_green]Stargazers[/]: {stars:,}\n"
                        f"[light_green]Issues/Pull Requests[/]: {issues:,}\n"
                        f"[light_green]Forks[/]: {forks:,}",
                        expand=False,
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
            assert isinstance(parsed_stats, dict)
        except (json.JSONDecodeError, AssertionError):
            parsed_stats = None

        stats = parsed_stats["data"] if parsed_stats else None
        if stats:
            metadata.add_row(
                Panel(
                    f"[blue]Last Month[/]: {stats['last_month']:,}\n"
                    f"[blue]Last Week[/]: {stats['last_week']:,}\n"
                    f"[blue]Last Day[/]: {stats['last_day']:,}",
                    expand=False,
                    border_style="yellow",
                    title="Downloads",
                )
            )
    if not hide_requirements:
        if info["requires_dist"]:
            metadata.add_row(
                Panel(
                    "\n".join(
                        f"[light_red link={base_url}/project/{name.split()[0]}]{name}[/]"
                        for name in info["requires_dist"]
                    ),
                    expand=False,
                    border_style="red",
                    title="Requirements",
                )
            )
    if not hide_meta:
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
                    )
                    if i
                ),
                expand=False,
                border_style="yellow1",
                title="Meta",
            )
        )
    if show_classifiers:
        metadata.add_row(
            Panel(
                _format_classifiers("\n".join(info["classifiers"])).strip(),
                expand=False,
                border_style="cyan",
                title="Classifiers",
            )
        )
    console.print(Panel(table, border_style="green"))
    console.print(metadata)


@app.command()
def regex_search(
    regex: str = Argument(..., help="The regular expression to search with"),
    compact: bool = Option(False, help="Compact formatting"),
) -> None:
    """Search for packages that match the regular expression."""
    packages = load_cache()

    import re  # pylint: disable=import-outside-toplevel

    # We compile the regex because it's twice as fast (https://imgur.com/a/MoUyEMg)
    _regex = re.compile(regex)
    if compact:
        matches = []
        for package in packages:
            if _regex.match(package):
                matches.append(f"[link={base_url}/project/{package}]{package}[/]")
        console.print(", ".join(matches))
    else:
        table = Table(show_header=True, show_lines=True, title=f"Matches for {regex}")
        table.add_column("[purple]No.[/]", style="purple")
        table.add_column("[green]Package[/]")
        table.add_column("[blue]Link[/]", style="cyan")
        matches = 0
        for package in packages:
            if _regex.match(package):
                matches += 1
                table.add_row(
                    f"{matches}.",
                    f"[link={base_url}/project/{package}]{package}[/]",
                    f"{base_url}/project/{package}",
                )
        console.print(table)
        if table.row_count > 50:
            console.print(
                "[yellow]:warning: WARNING:[/] There are more than 50 matches, consider using the --compact flag"
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
                        rich.print("[red]:no_entry_sign: Project not found[/]")
                    rich.print(
                        f"[orange]:grey_exclamation: Some error occured. response code {response.status_code}[/]"
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

    link_style = questionary.Style([("name", "bold red"), ("seperator", "gray"), ("url", "cyan")])

    url = f"{base_url}/pypi/{quote(package_name)}/json"

    with console.status("Getting data from PyPI"):
        response = session.get(url)

    if response.status_code != 200:
        if response.status_code == 404:
            rich.print("[red]:no_entry_sign: Project not found[/]")
        rich.print(f"[orange]:grey_exclamation: Some error occured. response code {response.status_code}[/]")
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
                title=[("class:name", f"{name:15}"), ("class:seperator", " - "), ("class:url", url)], value=url
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
):
    """Show the cli's or another package's version and exit"""
    if not package_name:
        from .__init__ import __version__  # pylint: disable=import-outside-toplevel

        console.print(f"Current version of [yellow]pypi-command-line[/] is [red]{__version__}[/]")
        with console.status("Getting latest version"):
            latest_version = get_latest_version()
        console.print(f"Latest  version of [yellow]pypi-command-line[/] is [red]{latest_version}[/]")
        raise typer.Exit()

    url = f"{base_url}/pypi/{quote(package_name)}/json"
    with console.status("Getting data from PyPI"):
        response = session.get(url)

    if response.status_code != 200:
        if response.status_code == 404:
            rich.print("[red]:no_entry_sign: Project not found[/]")
        rich.print(f"[orange]:grey_exclamation: Some error occured. response code {response.status_code}[/]")
        raise typer.Exit()

    parsed_data = json.loads(response.text)

    try:
        from packaging.version import parse as parse_version  # pylint:disable=import-outside-toplevel
    except ImportError:
        from distutils.version import LooseVersion as parse_version  # pylint:disable=import-outside-toplevel

    latest_versions = list(sorted(map(parse_version, parsed_data["releases"].keys()), reverse=True))[:limit]
    output = f"Top {limit} latest versions of [green]{package_name}[/] ordered by version number:\n"
    for n, version in enumerate(latest_versions, start=1):
        output += f" [magenta]{n}.[/] [white]{version}[/]\n"
    console.print(output)


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

        session = Session()
        session.headers.update({"User-Agent": "wasi_master/pypi_cli", "Accept": "application/json"})
    if repository:
        global base_url
        if repository == "testpypi":
            base_url = "https://test.pypi.org"
        else:
            base_url = repository


def run():
    """Run the CLI."""
    app()


if __name__ == "__main__":
    run()
