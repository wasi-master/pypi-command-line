"""The main file."""
import json
from datetime import datetime
from urllib.parse import quote

import humanize
import requests
import rich
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme
from typer import Argument, Option

# We instantiate a typer app and a rich console for later use
app = typer.Typer(add_completion=False)
console = Console(theme=Theme({"markdown.link": "#6088ff"}))
# We will use these headers for every request
headers = {"User-Agent": "wasi_master/pypi_cli"}


class Package:
    """Represents a package gotten from scraping the search results."""

    def __init__(self, soup):
        """Instantiates a package

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


def utc_to_local(utc_dt):
    """Convert a datetime from utc to local time."""
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)


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


def load_cache(cache_file):
    import os  # pylint: disable=import-outside-toplevel

    try:
        last_refreshed = os.path.getmtime(cache_file)
    except FileNotFoundError:
        return fill_cache(cache_file, msg="Generating cache")
    else:
        import time  # pylint: disable=import-outside-toplevel

        if time.time() - last_refreshed > 86400:
            return fill_cache(cache_file, msg="Cache is too old (>1d). Refreshing cache")
        with open(cache_file, "r") as cache_file:
            return cache_file.read().splitlines()


def fill_cache(cache_file, msg="Fetching cache"):
    """Fill the cache with the packages."""
    from rich.progress import Progress  # pylint: disable=import-outside-toplevel

    all_packages_url = "https://pypi.org/simple/"

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
    with open(cache_file, "w") as cache_file:
        cache_file.write("\n".join(packages))
    return packages


def refresh_cache():
    import os.path  # pylint: disable=import-outside-toplevel

    cache_file = os.path.join(os.path.dirname(__file__), "cache.txt")
    with console.status("Getting current cache"):
        old_cache = load_cache(cache_file)
    new_cache = fill_cache(cache_file, msg="Fetching new cache")
    changed = len(new_cache) - len(old_cache)
    console.print(f"[yellow]Updated the cache, number of new packages:[/] [red]{changed}[/]")


# 1. It first checks if the repository has a readme file. If it doesn't, it raises an exception.
# 2. If it does, it gets the readme file's content and the path to the file.
# 3. If the content is not found, it raises an exception.
# 4. If the content is found, it returns the content and the path to the file.
def _get_github_readme(repo):
    readme = requests.get(f"https://api.github.com/repos/{repo}/readme").json()
    if readme.get("message") == "Not Found":
        console.print("[/]Could not find readme[/]")
        raise typer.Exit()
    content = requests.get(f"https://raw.githubusercontent.com/{repo}/master/{readme['path']}")
    if content.status_code == 200:
        return content.text, readme["path"]
    return None, None


def _format_xml_packages(url, title, pubmsg, _author, _link, *, split_title=False):
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
        response = requests.get(url, headers=headers)
    soup = bs4.BeautifulSoup(response.text, "lxml-xml")
    from datetime import timezone  # pylint: disable=import-outside-toplevel

    for index, package in enumerate(soup.find_all("item"), 1):
        title = package.find("title").text
        if split_title:
            title = title.split()[0]
        author = package.find("author")
        description = package.find("description")
        link = package.find("link").text

        date = utc_to_local(datetime.strptime(package.find("pubDate").text, "%a, %d %b %Y %H:%M:%S GMT")).replace(
            tzinfo=None
        )
        if _link and _author:
            table.add_row(
                f"{index}.",
                title,
                author.text if author else None,
                description.text if description else "",
                link,
                humanize.naturaltime(date),
            )
        elif _link and not _author:
            table.add_row(
                f"{index}.",
                title,
                description.text if description else "",
                link,
                humanize.naturaltime(date),
            )
        elif not _link and not _author:
            table.add_row(
                f"{index}.",
                title,
                description.text if description else "",
                humanize.naturaltime(date),
            )
    console.print(table)


@app.command()
def desc(
    package_name: str = Argument(..., help="Package to get the description for"),
    force_github: bool = Argument(False, help="Forcefully get the description from github"),
):
    """See the description for a package."""
    url = f"https://pypi.org/pypi/{quote(package_name)}/json"
    with console.status("Getting data from PyPI"):
        response = requests.get(url, headers=headers)
    parsed_data = json.loads(response.text)["info"]
    if force_github:
        import re  # pylint: disable=import-outside-toplevel

        repo = re.findall(r"https://(www\.)?github\.com/([A-Za-z0-9_.-]{0,38}/[A-Za-z0-9_.-]{0,100})", str(parsed_data))
        repo = repo[0][1] if repo else None
        if not repo:
            console.print("[red]I could not find a GitHub repository[/]")
            raise typer.Exit()
        readme, filename = _get_github_readme(repo)
        if not readme or not filename:
            console.print("[red]I could not find a readme inside the GitHub repository[/]")
            raise typer.Exit()
        parsed_data["description"] = readme
        if filename.endswith((".md", ".md.txt")):
            parsed_data["description_content_type"] = "text/markdown"
        elif filename.endswith((".rst", ".rst.txt")):
            parsed_data["description_content_type"] = "text/x-rst"
        else:
            parsed_data["description_content_type"] = "text/markdown"
    if not parsed_data["description"] or parsed_data["description"] == "UNKNOWN":
        console.print("[red]No description found on PyPI.[/]")
        import re  # pylint: disable=import-outside-toplevel

        repo = re.findall(r"https://(www\.)?github\.com/([A-Za-z0-9_.-]{0,38}/[A-Za-z0-9_.-]{0,100})", str(parsed_data))
        repo = repo[0][1] if repo else None
        if repo:
            import questionary  # pylint: disable=import-outside-toplevel

            console.print(f"[yellow]However, I did find a github repo[/] https://github.com/{repo}.\n")
            resp = questionary.confirm("Do you want to get the description from there?").ask()
            if not resp:
                console.print("[dim gray]Cancelled![/]")
                raise typer.Exit()
            readme, filename = _get_github_readme(repo)
            if not readme or not filename:
                console.print("[red]I could not find a readme inside the GitHub repository[/]")
                raise typer.Exit()
            parsed_data["description"] = readme
            if filename.endswith((".md", ".md.txt")):
                parsed_data["description_content_type"] = "text/markdown"
            elif filename.endswith((".rst", ".rst.txt")):
                parsed_data["description_content_type"] = "text/x-rst"
            else:
                parsed_data["description_content_type"] = "text/markdown"

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
    _author: bool = Option(False, metavar="author", help="Show the project author of not"),
    _link: bool = Option(True, metavar="link", help="Show the project link of not"),
):
    """See the top 40 newly added packages."""
    import bs4  # pylint: disable=import-outside-toplevel

    _format_xml_packages(
        "https://pypi.org/rss/packages.xml",
        "Newly Added Packages",
        "Published At",
        _author,
        _link,
        split_title=True,
    )


@app.command()
def new_releases(
    _author: bool = Option(False, metavar="author", help="Show the project author of not"),
    _link: bool = Option(True, metavar="link", help="Show the project link of not"),
):
    """See the top 100 newly updated packages."""
    import bs4  # pylint: disable=import-outside-toplevel

    _format_xml_packages(
        "https://pypi.org/rss/updates.xml",
        "Newly Released Packages",
        "Released At",
        _author,
        _link,
    )


@app.command()
def largest_files():
    """See the top 100 projects with the largest file size."""

    headers = {"User-Agent": "wasi_master/pypi_cli", "Accept": "application/json"}
    url = "https://pypi.org/stats/"
    with console.status("Loading largest files..."):
        response = requests.get(url, headers=headers)
        data = json.loads(response.text)
    packages = data["top_packages"]
    packages = dict(sorted(packages.items(), key=lambda i: i[1]["size"], reverse=True))
    table = Table(
        title="Top packages on PyPI based on their size",
        show_lines=True,
    )
    table.add_column("Index", style="magenta", header_style="bold magenta")
    table.add_column("Package", style="green", header_style="bold green")
    table.add_column("Size", style="red", header_style="bold red")
    table.add_column("Link", style="cyan", header_style="bold blue")
    table.add_row(
        "-",
        "All Total",
        humanize.naturalsize(data["total_packages_size"], binary=True) + "\n",
        style="bold red",
    )
    for i, (name, project) in enumerate(packages.items(), 1):
        table.add_row(
            f"{i}.",
            f"[link=https://pypi.org/project/{name}]{name}[/]",
            humanize.naturalsize(project["size"], binary=True),
            f"https://pypi.org/project/{name}",
        )
    console.print(table)


@app.command()
def search(
    name: str = Argument(..., help="The name of the package to search for"),
    page: int = Option(1, min=1, max=500, help="The page of the search results to show."),
    # classifier: List[str] = Option(
    #     None, help="Can be used multiple times to specify a list of classifiers to filter the results."
    # ),
):
    """Search for a package on PyPI."""
    url = "https://pypi.org/search/"
    parameters = {
        "q": name,
        "page": page,
    }
    # if classifier:
    #     parameters["c"] = classifier
    with console.status(f"Searching for {name}..."):
        response = requests.get(url, headers=headers, params=parameters)

    if response.status_code == 404:
        console.print("[bold]The specified page doesn't exist[/]")
        raise typer.Exit()

    with console.status("Parsing data..."):
        import bs4  # pylint: disable=import-outside-toplevel

        soup = bs4.BeautifulSoup(response.text, "lxml")
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
        title=f"[bold]Search results for {name}[/]",
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
            f"[link=https://pypi.org/project/{package.name}]{package.name}[/]",
            package.description,
            package.date,
        )
    console.print(table)


@app.command()
def releases(
    package_name: str = Argument(..., help="The name of package to show releases for"),
    _link: bool = Option(False, metavar="link", help="Display the links to the releases"),
):
    """See all the available releases for a package.

    The --link argument can be used to also show the link of the releases.
    This is turned off by default and the link is added as a hyperlink to the package name on supported terminals
    """
    url = f"https://pypi.org/pypi/{quote(package_name)}/json"
    with console.status("Getting data from PyPI"):
        response = requests.get(url, headers=headers)
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
def info(
    package_name: str = Argument(...),
    version: str = Option(None),
    show_classifiers: bool = Option(False, metavar="classifiers", help="Show the classifiers"),
    hide_project_urls: bool = Option(False, metavar="project_urls", help="Hide the project urls"),
    hide_requirements: bool = Option(False, metavar="requirements", help="Hide the requirements"),
    hide_github: bool = Option(False, metavar="github", help="Hide the github"),
    hide_stats: bool = Option(False, metavar="stats", help="Hide the stats"),
    hide_meta: bool = Option(False, metavar="meta", help="Hide the metadata"),
):
    """See the information about a package."""
    url = f"https://pypi.org/pypi/{quote(package_name)}{f'/{version}' if version else ''}/json"
    with console.status("Getting data from PyPI"):
        response = requests.get(url, headers=headers)

    if response.status_code != 200:
        if response.status_code == 404:
            rich.print("[red]Project not found[/]")
        rich.print(f"[orange]Some error occured. response code {response.status_code}[/]")
        raise typer.Exit()

    parsed_data = json.loads(response.text)

    info = parsed_data["info"]
    releases = parsed_data["releases"]
    urls = parsed_data["urls"]

    from packaging.version import parse as parse_version  # pylint:disable=import-outside-toplevel

    # HACK: should use fromisotime
    release_time = datetime.strptime(urls[-1]["upload_time_iso_8601"], "%Y-%m-%dT%H:%M:%S.%fZ")
    natural_time = release_time.strftime("%b %d, %Y")
    description = info["summary"]
    latest_version = list(sorted(map(parse_version, releases.keys()), reverse=True))[0]
    latest_stable_version = list(sorted(map(parse_version, releases.keys()), reverse=True))[0]
    version_comment = (
        "[green]Latest Version[/]"
        if str(latest_version) == str(info["version"])
        else f"[red]Newer version available ({latest_version})[/]"
    )
    import re  # pylint: disable=import-outside-toplevel

    repo = re.findall(
        r"https://(www\.)?github\.com/([A-Za-z0-9_.-]{0,38}/[A-Za-z0-9_.-]{0,100})(?:\.git)?",
        str(info),
    )
    repo = remove_dot_git(repo[0][1]) if repo else None

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
                resp = requests.get(url, headers=headers)
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
                        f"[light_green link=https://github.com/{repo}]Name[/]: {repo}\n"
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
            r = requests.get(stats_url)
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
                        f"[light_red link=https://pypi.org/project/{name.split()[0]}]{name}[/]"
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


@app.command("rsearch")
def regex_search(
    regex: str = Argument(..., help="The regular expression to search with"),
    compact: bool = Option(False, help="Compact formatting"),
) -> None:
    """Search for packages that match the regular expression."""
    import os  # pylint: disable=import-outside-toplevel

    cache_path = os.path.join(os.path.dirname(__file__), "cache.txt")
    packages = load_cache(cache_path)

    import re  # pylint: disable=import-outside-toplevel

    # We compile the regex because it's twice as fast (https://imgur.com/a/MoUyEMg)
    _regex = re.compile(regex)
    if compact:
        matches = []
        with console.status("Finding matches with regex"):
            for package in packages:
                if _regex.match(package):
                    matches.append(f"[link=https://pypi.org/project/{package}]{package}[/]")
        console.print(", ".join(matches))
    else:
        table = Table(show_header=True, show_lines=True, title=f"Matches for {regex}")
        table.add_column("[purple]No.[/]", style="purple")
        table.add_column("[green]Package[/]")
        table.add_column("[blue]Link[/]", style="cyan")
        matches = 0
        with console.status("Finding matches with regex"):
            for package in packages:
                if _regex.match(package):
                    matches += 1
                    table.add_row(
                        f"{matches}.",
                        f"[link=https://pypi.org/project/{package}]{package}[/]",
                        f"https://pypi.org/project/{package}",
                    )
        console.print(table)
        if table.row_count > 50:
            console.print("[yellow]There are more than 50 matches, consider using the --compact flag")


@app.command()
def rtfd(
    package_name: str = Argument(..., help="The name or link to the docs of the package to show the documentation for"),
    query: str = Argument(..., help="The query you want to read the docs for"),
):
    """Search the documentation for an item of a package."""
    import webbrowser  # pylint: disable=import-outside-toplevel

    docs_mapping = {
        **dict.fromkeys(["py", "python", "python3"], "https://docs.python.org/3/search.html"),
        **dict.fromkeys(["py2", "python2"], "https://docs.python.org/2/search.html"),
        **dict.fromkeys(["pil", "pillow"], "https://pillow.readthedocs.io/en/stable/search.html"),
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

            resp = questionary.confirm("Docs not available.Do you want to search pypi to find the documentation?").ask()
            if resp:
                url = f"https://pypi.org/pypi/{quote(package_name)}/json"
                with console.status("Getting data from PyPI"):
                    response = requests.get(url, headers=headers)

                if response.status_code != 200:
                    if response.status_code == 404:
                        rich.print("[red]Project not found[/]")
                    rich.print(f"[orange]Some error occured. response code {response.status_code}[/]")
                    raise typer.Exit()

                parsed_data = json.loads(response.text)
                url = parsed_data["info"].get("project_urls", {}).get("Documentation", None)
                if not url:
                    console.print("[bold]Documentation url not found on PyPI[/]")
                    raise typer.Exit()
                else:
                    url = url + "/search.html"
            else:
                console.print("[dim grey]Cancelled![/]")
                raise typer.Exit()

    search_page = url + "?q=" + quote(query)
    webbrowser.open(search_page)


@app.command()
def browse(package_name: str = Argument(...)):
    """Browse for a package's URLs"""
    import questionary  # pylint: disable=import-outside-toplevel
    import webbrowser  # pylint: disable=import-outside-toplevel

    link_style = questionary.Style(
        [
            ("name", "bold red"),
            ("seperator", "gray"),
            ("url", "cyan"),
        ]
    )

    url = f"https://pypi.org/pypi/{quote(package_name)}/json"
    with console.status("Getting data from PyPI"):
        response = requests.get(url, headers=headers)

    if response.status_code != 200:
        if response.status_code == 404:
            rich.print("[red]Project not found[/]")
        rich.print(f"[orange]Some error occured. response code {response.status_code}[/]")
        raise typer.Exit()

    parsed_data = json.loads(response.text)
    info = parsed_data["info"]

    urls = info["project_urls"]
    urls["Project URL"] = info.get("project_url")
    urls["Home Page"] = info.get("project_url")
    urls["Release URL"] = info.get("release_url")
    urls["Mail to"] = ("mailto:" + info["maintainer_email"]) if info.get("maintainer_email") else None

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
def refresh():
    """Refresh the cache."""
    refresh_cache()


def run():
    """Run the CLI."""
    app()


if __name__ == "__main__":
    run()
