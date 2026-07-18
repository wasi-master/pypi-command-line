---
layout: page
title: Usage instructions for pypi-command-line
description: pypi-command-line is a powerful, colorful, beautiful command line interface for pypi.org that is well maintained
---
<!-- markdownlint-disable MD024 MD025 MD033-->

# Usage

!!! note

    You'll have to install the package first. See <https://wasi-master.github.io/pypi-command-line/install> for instructions.

!!! tip "Tips"

    - The demos are interactive [asciinema](https://asciinema.org) recordings, press the *play* button to watch them</br>
    - You can *pause*, *seek*, and use the <kbd>f</kbd> key (or the button in the bottom right corner) to watch them in *full screen*</br>
    - Since the recordings are plain text you can also *select and copy* any text from them while paused

## **Options**

## -h, --help

Sends a help message, each command also has this flag that you can use to see the help about that specific command

### **Demo**

<div class="asciinema-demo" data-cast="../assets/demos/pypi-help.cast"></div>

Command specific help:

<div class="asciinema-demo" data-cast="../assets/demos/pypi-command-help.cast"></div>

### **Usage**

> pypi -h

> pypi --help

For command specific help: ([`info`](#information) in this case)
> pypi info --help

## --install-completion

Installs autocompletion for the current shell.

### **Demo**

<div class="asciinema-demo" data-cast="../assets/demos/pypi-install-completion.cast"></div>

### **Usage**

> pypi --install-completion

## --show-completion

See code for autocompletion for the current shell, to copy it or customize the installation.

### **Demo**

The output will be different depending on the shell

<div class="asciinema-demo" data-cast="../assets/demos/pypi-show-completion.cast"></div>

### **Usage**

> pypi --show-completion

## --no-cache

If used, disabled the cache for the current command, for more information about the cache see [notes](https://wasi-master.github.io/pypi-command-line/notes#cache)

??? example "Demo"

    <div class="asciinema-demo" data-cast="../assets/demos/pypi-no-cache.cast"></div>

### **Usage**

> pypi --no-cache <command>

## --repository

Specify a base url for the repository from which the results are taken from. Such as [testpypi](https://test.pypi.org)

The value must either be the shorthand `testpypi` or a full `http://`/`https://` URL. Anything else is rejected with an error and exit code 2.

??? example "Demo"

    <div class="asciinema-demo" data-cast="../assets/demos/pypi-repository.cast"></div>

### **Usage**

> pypi --repository testpypi <command>

> pypi --repository https://test.pypi.org <command>

## --timeout

Set the timeout in seconds for network requests made by any command. The default is 15 seconds and the value must be at least 0.1. If a server does not respond within the timeout, the command fails with a network error message instead of hanging.

??? example "Demo"

    <div class="asciinema-demo" data-cast="../assets/demos/pypi-timeout.cast"></div>

### **Usage**

> pypi --timeout 5 <command>

## --verbose

Show debug logs for errors that are otherwise silently ignored, such as unparseable requirements, failed GitHub or download-statistics lookups, and invalid timestamps. Useful for troubleshooting when a command shows `N/A` or skips data.

??? example "Demo"

    <div class="asciinema-demo" data-cast="../assets/demos/pypi-verbose.cast"></div>

### **Usage**

> pypi --verbose <command>

## **Commands**

!!! tip "Command aliases"

    Every command can also be invoked by its aliases (listed in an "Aliases" section under each command below), or by any unambiguous prefix of its name (for example `pypi desc` for `pypi description`).

## version

See the latest version of any package or pypi-command-line if no package was specified

How this works is if you specify a package name then it shows the top *limit* latest versions of that specified package, otherwise it shows the current version of pypi-command-line and the latest version of pypi-command-line

### **Aliases**

These shorthands can be used instead of the full command name: `v`, `ver`

### **Demo**

Seeing the current and latest version of pypi-command-line:

<div class="asciinema-demo" data-cast="../assets/demos/pypi-version.cast"></div>

Seeing the latest versions of another package (django in this case) along with the installed version:

<div class="asciinema-demo" data-cast="../assets/demos/pypi-version-package.cast"></div>

Omitting the pre-releases:

<div class="asciinema-demo" data-cast="../assets/demos/pypi-version-no-pre-releases.cast"></div>

### **Usage**

> pypi version [PACKAGE_NAME]

### **Options**

- `PACKAGE_NAME`

    The name of the package to show the latest version(s) for. [<span style="color: cyan">default:</span> pypi-command-line]

- `--limit INTEGER`

    Limit the number of versions to show [<span style="color: cyan">default:</span> 10]

- `--no-pre-releases`

    If set then it will not show pre-releases

- `--show-installed-versions`

    If set then it will show the version that is installed too

- `-h`, `--help`

    Show the help message.

## browse

Browse for a package's URLs.

This gets the package information, and shows a list containing it's project urls. If the project has a maintainer email set then it also shows that as a mailto<sup>[<a title="mailto is a Uniform Resource Identifier (URI) scheme for email addresses. It is used to produce hyperlinks on websites that allow users to send an email to a specific address directly from an HTML document, without having to copy it and entering it into an email client." href="https://en.wikipedia.org/wiki/Mailto" target="_blank">?</a>]</sup> that you can press to send a email via your default email client. This gets all the project urls from PyPI and then shows them, there is a known bug where PyPI in some cases shows UNKNOWN for some url so that also gets shown.

### **Aliases**

These shorthands can be used instead of the full command name: `b`

### **Demo**

You can move through the links with the arrow keys and cancel using ++ctrl+c++ if you don't find your desired link

<div class="asciinema-demo" data-cast="../assets/demos/pypi-browse.cast"></div>

Using `--url-only` to just print the urls instead of opening anything:

<div class="asciinema-demo" data-cast="../assets/demos/pypi-browse-url-only.cast"></div>

### **Usage**

> pypi browse PACKAGE_NAME

### **Options**

- `PACKAGE_NAME`

    The name of the package to show the urls for. <span style="color: red">[required]</span>

- `--url-only`

    Only show urls of the package instead of showing an interactive dialog to open in a web browser.

- `-h`, `--help`

    Show the help message.

## cache-clear

Clears the local packages and requests cache, see [notes](https://wasi-master.github.io/pypi-command-line/notes#cache) for more information about the cache.

### **Aliases**

These shorthands can be used instead of the full command name: `cc`

### **Demo**

<div class="asciinema-demo" data-cast="../assets/demos/pypi-cache-clear.cast"></div>

### **Usage**

> pypi cache-clear

### **Errors and Warnings**

- #### <span style="color: red">E:</span> Failed to delete `#!html <file_path>`

    Shown when it cannot delete a file due to some other process using it or not having enough permissions

## cache-information

Shows the size for the packages cache and the size and additionally the websites cached with their creation date and expiry date, see [notes](https://wasi-master.github.io/pypi-command-line/notes#cache) for more information about the cache.

### **Aliases**

These shorthands can be used instead of the full command name: `ci`

### **Demo**

<div class="asciinema-demo" data-cast="../assets/demos/pypi-cache-information.cast"></div>

### **Errors and Warnings**

- #### <span style="color: yellow">W:</span> Packages cache not available

    Shown when the packages cache doesn't exist due to it not being created yet or being deleted recently. You can rebuild that cache using [`cache-refresh`](#cache-refresh)


- #### <span style="color: yellow">W:</span> Requests cache not available

    Shown when the requests cache doesn't exist due to the `requests-cache` package not being installed

### **Usage**

> pypi cache-info

## cache-refresh

Reloads the packages cache and shows the number of new packages added after the last refresh, see [notes](https://wasi-master.github.io/pypi-command-line/notes#cache) for more information about the cache.

### **Aliases**

These shorthands can be used instead of the full command name: `cr`

### **Demo**

<div class="asciinema-demo" data-cast="../assets/demos/pypi-cache-refresh.cast"></div>

### **Usage**

> pypi cache-refresh

## check

Check a requirements.txt or pyproject.toml file for updates, compatibility, and abandoned status.

This command parses the project's requirement file, fetches information from PyPI, and prints a table indicating whether the packages are outdated, abandoned, or have missing/unsupported wheel files on the current system.

### **Aliases**

These shorthands can be used instead of the full command name: `chk`

### **Demo**

<div class="asciinema-demo" data-cast="../assets/demos/pypi-check.cast"></div>

Getting the results as JSON with `--json`:

<div class="asciinema-demo" data-cast="../assets/demos/pypi-check-json.cast"></div>

### **Usage**

> pypi check FILE_PATH

### **Options**

- `FILE_PATH`

    The path to the `requirements.txt` or `pyproject.toml` file to check. <span style="color: red">[required]</span>

- `--json`

    Output the results as JSON instead of a table. Each entry contains `name`, `specified`, `latest`, `wheel_support` (`supported`, `no_wheels`, or `unsupported`), `last_updated` (ISO 8601), `abandoned`, `outdated`, and `error` (`null`, `not_found`, or `error`). Useful for scripting, for example:

    ```bash
    pypi check requirements.txt --json | jq '.[] | select(.outdated) | .name'
    ```

## compare

Compare multiple libraries against each other

This command compares the latest version, latest release date, github stars, open issues, downloads, and python version requirements across a given list of packages

### **Aliases**

These shorthands can be used instead of the full command name: `c`, `cmp`

### **Demo**

<div class="asciinema-demo" data-cast="../assets/demos/pypi-compare.cast"></div>

Getting the results as JSON with `--json`:

<div class="asciinema-demo" data-cast="../assets/demos/pypi-compare-json.cast"></div>

### **Usage**

> pypi compare PACKAGE1 PACKAGE2...

### Options

- `PACKAGE_NAME...`
    The list of packages to compare seperated by spaces

## description

Shows the description of a package as gotten from PyPI or GitHub.

This first gets the information about the package and then finds the description. If the package has a description it gets the description format, if it's reStructuredText or Markdown then it shows the description formatted according to the format.

If it doesn't get a description in PyPI then it looks for github repos mentioned in the json response gotten from the pypi api. this makes sure it gets the repo if it is supplied no matter where it is. If it finds multiple repos then it asks the user to pick one. Then it uses the github api to find the name of the readme file of the repo, this uses the api instead of manually finding it just in case. Then it reads the contents from the readme file and determines the format using the file extension then it shows the description formatted according to the format.

### **Aliases**

These shorthands can be used instead of the full command name: `desc`, `readme`

### **Demo**

<div class="asciinema-demo" data-cast="../assets/demos/pypi-description.cast"></div>

Demo of forcefully getting the description from github with `--force-github`

<div class="asciinema-demo" data-cast="../assets/demos/pypi-description-force-github.cast"></div>

Demo of using a custom syntax highlighting theme for code blocks with `--syntax-theme`

<div class="asciinema-demo" data-cast="../assets/demos/pypi-description-syntax-theme.cast"></div>

### **Usage**

> pypi description [OPTIONS] PACKAGE_NAME

### **Options**

- `PACKAGE_NAME`

    Package to get the description for <span style="color: red">[required]</span>

- `--force-github`

    Forcefully get the description from github </br>
    This will make sure that it doesn't get the description from pypi but get it from github by reading the readme file of that project's repository

- `--syntax-theme`

    Specify a custom syntax highlighting theme for code blocks</br>
    This has to be a pygments supported syntax highlighting theme or `ansi_dark` or `ansi_light` which will use the colors from your terminal theme.
    For a list of pygments themes see [this link](https://stylishthemes.github.io/Syntax-Themes/pygments/)

- `-h`, `--help`

    Show the help message.

### Errors and Warnings

- #### <span style="color: red">E:</span> Project not found

    Shown when the pypi api returns a 404 response meaning a package with the specified name most likely doesn't exist

- #### <span style="color: red">E:</span> ReadMe not found

    Shown when `--force-github` is enabled or the PyPI page doesn't have a description and the github page also doesn't have a readme

- #### <span style="color: yellow">W:</span> Multiple github repos

    Shown when `--force-github` is enabled or the PyPI page doesn't have a description. If this is shown it will ask you to pick one

## dependencies

Shows the a rich, visual tree of a package's dependencies and sub-dependencies up to n levels deep.

Examples:
    pypi dependencies requests
    pypi dependencies \"requests[security]\" --level 2

### **Aliases**

These shorthands can be used instead of the full command name: `d`, `dep`, `deps`, `tree`

### **Demo**

<div class="asciinema-demo" data-cast="../assets/demos/pypi-dependencies.cast"></div>

Limiting the depth of the tree with `--level` and using extras:

<div class="asciinema-demo" data-cast="../assets/demos/pypi-dependencies-level.cast"></div>

### **Usage**

> pypi dependencies [OPTIONS] PACKAGE_NAME

### **Options**

- `PACKAGE_NAME`

    The name of the package to show dependencies for <span style="color: red">[required]</span>

- `--limit INTEGER`

    Limit the number of levels of dependencies to show [<span style="color: cyan">default:</span> 10]

### Errors and Warnings

- #### <span style="color: red">E:</span> Project not found

    Shown when the pypi api returns a 404 response meaning a package with the specified name most likely doesn't exist


## information

The information command gets data from [PyPI](https://pypi.org) and [GitHub](https://github.com) and [PyPIStats](https://pypistats.org) and shows them to the console

### **Aliases**

These shorthands can be used instead of the full command name: `i`, `info`, `show`

### **Demo**

<div class="asciinema-demo" data-cast="../assets/demos/pypi-information.cast"></div>

You can also see classifiers if you want to

<div class="asciinema-demo" data-cast="../assets/demos/pypi-information-classifiers.cast"></div>

Hiding the parts you don't care about with the `--hide-*` flags:

<div class="asciinema-demo" data-cast="../assets/demos/pypi-information-hide.cast"></div>

Getting the raw package metadata as JSON with `--json`:

<div class="asciinema-demo" data-cast="../assets/demos/pypi-information-json.cast"></div>

### **Usage**

> pypi information [OPTIONS] PACKAGE_NAME

### **Options**

- PACKAGE_NAME <span style="color: red">[required]</span>
  The name of the package to show information for
  This can also include the version with this format: `package_name==version`

- `--version TEXT`

    The version of the package to show information for

- `--show-classifiers`

    Show the classifiers (see the demo above for an example)

- `--hide-project-urls`

    Hide the project urls

- `--hide-requirements`

    Hide the requirements

- `--hide-github`

    Hide the github

- `--hide-stats`

    Hide the stats

- `--hide-meta`

    Hide the metadata

- `-h`, `--help`

    Show the help message.

### **Errors and Warnings**

- #### <span style="color: red">E:</span> Project not found

    Shown when the pypi api returns a 404 response meaning a package with the specified name most likely doesn't exist

## largest-files

This command shows the all time largest pypi packages. The layout is similar to the [one found in PyPI](https://pypi.org/stats/)

### **Aliases**

These shorthands can be used instead of the full command name: `lf`

### **Demo**

<div class="asciinema-demo" data-cast="../assets/demos/pypi-largest-files.cast"></div>

### **Usage**

> pypi information [OPTIONS]

### **Options**

- `-h`, `--help`

    Show the help message.

### **Errors and Warnings**

- #### <span style="color: red">E:</span> Project not found

    Shown when the pypi api returns a 404 response meaning a package with the specified name most likely doesn't exist

## new-packages

Shows the top 40 newly added packages. Meaning that the first ever version of those packages were uploaded from pypi a short while ago.

### **Aliases**

These shorthands can be used instead of the full command name: `np`

### **Demo**

<div class="asciinema-demo" data-cast="../assets/demos/pypi-new-packages.cast"></div>

Showing the author and hiding the link with `--show-author` and `--hide-link`:

<div class="asciinema-demo" data-cast="../assets/demos/pypi-new-packages-flags.cast"></div>

### **Usage**

> pypi new-packages [OPTIONS]

### **Options**

- `-h`, `--help`

    Show the help message.

- `--show-author`

    If used this also shows the author </br>
    This usually shows the author's email.

- `--hide-link`

    If used it does not show the project link

### **Errors and Warnings**

- #### <span style="color: yellow">W:</span> `lxml` not installed

    There is a known bug that occurs when lxml is not installed. It doesn't show descriptions in some cases. Please install lxml using `pip install lxml`.

## new-releases

Shows the top 100 newly updated packages. Meaning that the latest version of those packages were uploaded from pypi short while ago.

### **Aliases**

These shorthands can be used instead of the full command name: `nr`

### **Demo**

<div class="asciinema-demo" data-cast="../assets/demos/pypi-new-releases.cast"></div>

Showing the author and hiding the link with `--show-author` and `--hide-link`:

<div class="asciinema-demo" data-cast="../assets/demos/pypi-new-releases-flags.cast"></div>

### **Usage**

> pypi new-releases [OPTIONS]

### **Options**

- `-h`, `--help`

    Show the help message.

- `--show-author`

    If used, it shows the project author too</br>
    This usually shows the author's email.

- `--hide-link`

    If used, it shows the project link too

### **Errors and Warnings**

- #### <span style="color: yellow">W:</span> `lxml` not installed

    There is a known bug that occurs when lxml is not installed. It doesn't show descriptions in some cases. Please install lxml using `pip install lxml`.

## releases

Shows all the available releases for a package.

The --link argument can be used to also show the link of the releases. This
is turned off by default and the link is added as a hyperlink to the package
name on supported terminals

### **Aliases**

These shorthands can be used instead of the full command name: `rel`

### **Demo**

<div class="asciinema-demo" data-cast="../assets/demos/pypi-releases.cast"></div>

Only showing a specific version with `--version`:

<div class="asciinema-demo" data-cast="../assets/demos/pypi-releases-version.cast"></div>

Also showing the release links with `--show-links`:

<div class="asciinema-demo" data-cast="../assets/demos/pypi-releases-links.cast"></div>

Getting the results as JSON with `--json`:

<div class="asciinema-demo" data-cast="../assets/demos/pypi-releases-json.cast"></div>

### **Usage**

> pypi releases [OPTIONS] PACKAGE_NAME

### **Options**

- `PACKAGE_NAME`

    The name of the package to show releases for</br>
    This can also include the version with this format: `package_name==version`

- `-h`, `--help`

    Show the help message.

- `--version TEXT`

    The version of the package to show information for

- `--show-links`

    If enabled it shows the wheel links too

### **Errors and Warnings**

- #### <span style="color: red">E:</span> Project not found

    Shown when the pypi api returns a 404 response meaning a package with the specified name most likely doesn't exist

## regex-search

Regex stands for Regular Expressions. It allows you to search for all packages in PyPI and only show ones that match a specific [Regular Expression](https://en.wikipedia.org/wiki/Regular_expression "A regular expression (shortened as regex or regexp) is a sequence of characters that specifies a search pattern. Usually such patterns are used by string-searching algorithms. For more info click here")

If the packages cache is empty it then loads the packages first, the cache is kept for 1 day meaning your data is at most 1 day old. if you want to refresh you may do so by using the [cache-refresh](#cache-refresh) command. For more information about this cache see [notes](https://wasi-master.github.io/pypi-command-line/notes#cache).

### **Aliases**

These shorthands can be used instead of the full command name: `rs`, `rsearch`, `s`

### **Demo**

<div class="asciinema-demo" data-cast="../assets/demos/pypi-regex-search.cast"></div>

Compact formatting with `--compact` and limiting the number of results with `--limit`:

<div class="asciinema-demo" data-cast="../assets/demos/pypi-regex-search-compact.cast"></div>

### **Usage**

> pypi regex-search [OPTIONS] REGEX

### **Options**

- `REGEX`
    The regular expression to search with  <span style="color: red">[required]</span>

- `--compact`
    Compact formatting </br>
    This removes the table and just shows the package names separated by commas, it also adds hyperlinks on supported terminals

- `-h`, `--help`
    Show the help message.

## read-the-docs

Searches the documentation for a certain package.

This just gets the documentation url and opens it's search results page with the given query

### **Aliases**

These shorthands can be used instead of the full command name: `rtd`, `docs`, `documentation`

### **Demo**

<div class="asciinema-demo" data-cast="../assets/demos/pypi-read-the-docs.cast"></div>

Searching the docs for a specific query:

<div class="asciinema-demo" data-cast="../assets/demos/pypi-read-the-docs-query.cast"></div>

### **Usage**

> pypi read-the-docs [OPTIONS] PACKAGE_NAME [QUERY]

### **Options**

- `PACKAGE_NAME`

    The name or link to the docs of the package to show the documentation for  [<span style="color: red">required</span>]

- `QUERY`

    The query you want to read the docs for, if not passed it opens the main docs page

- `--url-only`

    Only print the url to the console instead of opening it in a browser[<span style="color: cyan">default:</span> url-only]

- `-h`, `--help`

    Show the help message.

### **Errors and Warnings**

- #### <span style="color: yellow">W:</span> Docs not available

    Shown when the docs are not in the list of already known docs and needs to be gotten from PyPI, it will ask you if you want to get it from pypi

- #### <span style="color: red">E:</span> Documentation url not found on PyPI

    Shown when the docs are not in the list of already known docs and not given on PyPI


### **Errors and Warnings**

- #### <span style="color: red">E:</span> Project not found

    Shown when the pypi api returns a 404 response meaning a package with the specified name most likely doesn't exist

## search

Search for a package on PyPI. <span style="color: red">NOTE: This command is currently unavailable due to API Issues</span>

### **Demo**

<div class="asciinema-demo" data-cast="../assets/demos/pypi-search.cast"></div>

### **Usage**

> pypi search [OPTIONS] PACKAGE_NAME

### **Options**

- `PACKAGE_NAME`

    The name of the package to show wheels for <span style="color: red">[required]</span></br>

- `--page INTEGER RANGE`

    The page of the search results to show. [<span style="color: cyan">default:</span> 1; <span style="color: green">should be greater than 1 and less than 500</span>]

- -h, --help

    Shows the help message.

### **Errors and Warnings**

#### <span style="color: red">E:</span> Project not found

Shown when the pypi api returns a 404 response meaning the page number specified most likely doesn't exist

## vulnerabilities

See the known vulnerabilities for a package.

### **Aliases**

These shorthands can be used instead of the full command name: `vuln`, `vulns`

### **Demo**

<div class="asciinema-demo" data-cast="../assets/demos/pypi-vulnerabilities.cast"></div>

### **Usage**

> pypi vulnerabilities PACKAGE_NAME VERSION

### **Options**

- `PACKAGE_NAME`

    The name of the package to show vulnerability info for <span style="color: red">[required]</span>

- `VERSION`

    The version of the package to show info for <span style="color: red">[required]</span>

- `-h, `--help`

    Shows the help message.

### **Errors and Warnings**

#### <span style="color: red">E:</span> Project not found

Shown when the pypi api returns a 404 response meaning the page number specified most likely doesn't exist

## wheels

See the available wheels of a release on PyPI. The wheel names are color coded and the information is colored too.

### **Aliases**

These shorthands can be used instead of the full command name: `w`, `whl`

### **Demo**

<div class="asciinema-demo" data-cast="../assets/demos/pypi-wheels.cast"></div>

Only showing the wheels supported on the current platform with `--supported-only`:

<div class="asciinema-demo" data-cast="../assets/demos/pypi-wheels-supported-only.cast"></div>

### **Usage**

> pypi wheels [OPTIONS] PACKAGE_NAME [VERSION]

### **Options**

- `PACKAGE_NAME`

    The name of the package to show wheel info for  <span style="color: red">[required]</span>

- `VERSION`

    The version of the package to show info for, defaults to latest

- `-h, `--help`

    Shows the help message.

- --supported-only

    Only show wheels supported on the current platform

### Wheel Name Syntax

The wheel filename is `{distribution}-{version}(-{build tag})?-{python tag}-{abi tag}-{platform tag}.whl`.

![Image showing a wheel](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/wheel.png)

> <span style="color: #92EC5A;">distribution</span>

- Distribution name, e.g. 'pypi_command_line', 'django'.

> <span style="color: #F2C259;">version</span>

- Distribution version, e.g. 1.0.

> <span style="color: #FF7F30;">build tag (<b>Optional</b>)</span>

- build number. Must start with a digit. Acts as a tie-breaker if two wheel file names are the same in all other respects (i.e. name, version, and other tags). Sort as an empty tuple if unspecified, else sort as a two-item tuple with the first item being the initial digits as an `int`, and the second item being the remainder of the tag as a `str`.

> <span style="color: #FF6EF8;">language implementation and version tag</span>

- E.g. 'py27', 'py2', 'py3'.

> <span style="color: #9263FB;">abi tag</span>

- E.g. 'p33m', 'abi3', 'none'.

> <span style="color: #33F1C8;">platform tag</span>

- E.g. 'linux_x86_64', 'any'.

> <span style="color: #33F1C8;">file extension</span>

- E.g. '.whl'.

For example, <code><span style="color: #92EC5A;">distribution</span>-<span style="color: #F2C259;">1.0.0-<span style="color: #FF7F30;">1</span></span>-<span style="color: #FF6EF8;">py27</span>-<span style="color: #9263FB;">none</span>-<span style="color: #33F1C8;">any</span>.<span style="color: #4AA0FC;">whl</span></code> is the <span style="color: #FF7F30;">first build</span> of a package called <span style="color: #92EC5A;">'distribution'</span> with <span style="color: #F2C259;">version 1.0.0</span>, and is compatible with <span style="color: #FF6EF8;">Python 2.7</span> (any Python 2.7 implementation), with <span style="color: #9263FB;">no ABI</span> (pure Python), on <span style="color: #33F1C8;">any CPU architecture</span>.

The last three components of the filename before the extension are called "compatibility tags." The compatibility tags express the package's basic interpreter requirements and are detailed in [PEP 425](https://www.python.org/dev/peps/pep-0425/).

\- Data gotten from <https://www.python.org/dev/peps/pep-0427/#file-name-convention>

### **Errors and Warnings**

- #### <span style="color: red">E:</span> Project not found

    Shown when the pypi api returns a 404 response meaning the project name specified doesn't exist.

- #### <span style="color: red">E:</span> Version not found

    Shown when the specified version was not found.
