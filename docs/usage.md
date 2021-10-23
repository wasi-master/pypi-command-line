---
layout: page
title: Usage
---
<!-- markdownlint-disable MD024 MD025 MD033-->

# Usage

> Note: You'll have to install the package first. See <https://wasi-master.github.io/pypi-command-line/install> for instructions.

# Options

## -h, --help

Sends a help message, each command also has this flag that you can use to see the help about that specific command

### **Usage**

> pypi -h

> pypi --help

For comamnd specific help ([`search`](#search) in this case)
> pypi search --help

## --install-completion

Installs autocompletion for the current shell.

### **Demo**

![Demo of the command](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/pypi%20--install-completion.gif)

### **Usage**

> pypi --install-completion

## --show-completion

See code for autocompletion for the current shell, to copy it or customize the installation.

### **Demo**

The output will be different depending on the shell

![Demo of the command](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/pypi%20--show-completion.gif)

### **Usage**

> pypi --show-completion

## --cache / --no-cache

Whether to use cache or not for the current command, for more information about the cache see [notes](https://wasi-master.github.io/pypi-command-line/notes#cache) [<span style="color: blue">default:</span> cache]

### **Demo**

TODO: Add demo for --no-cache

### **Usage**

> pypi --no-cache <command>

## --repository

Specify a base url for the repository from which the results are taken from. Such as [testpypi](https://test.pypi.org)

### **Demo**

TODO: Add demo for --repository

### **Usage**

> pypi --repository testpypi <command>
> pypi --repository "https://test.pypi.org" <command>

# Commands

## version

See the latest version of any package or pypi-command-line if no package was specified

How this works is if you specify a package name then it shows the top *limit* latest versions of that specified package, otherwise it shows the current version of pypi-command-line and the latest version of pypi-command-line

### **Demo**

Seeing the current and latest version of pypi-command-line
![Seeing the current and latest version of pypi-command-line](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/pypi%20version%20without%20package.png)

Seeing the latest versions of another package
![Seeing the latest versions of another package](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/pypi%20version%20with%20package.png)

### **Usage**

> pypi version [PACKAGE_NAME]

### **Options**

- `PACKAGE_NAME`
  The name of the package to show the latest version(s) for. [<span style="color: blue">default:</span> None]

- `-h`, `--help`

  Show the help message.

## browse

Browse for a package's URLs.

This gets the package information, and shows a list containing it's project urls. If the project has a maintainer email set then it also shows that as a mailto<sup>[<a title="mailto is a Uniform Resource Identifier (URI) scheme for email addresses. It is used to produce hyperlinks on websites that allow users to send an email to a specific address directly from an HTML document, without having to copy it and entering it into an email client." href="https://en.wikipedia.org/wiki/Mailto" target="_blank">?</a>]</sup> that you can press to send a email via your default email client. This gets all the project urls from PyPI and then shows them, there is a known bug where PyPI in some cases shows UNKNOWN for some url so that also gets shown.

### **Demo**

![Demo of the command](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/pypi%20browse.gif)

You can cancel using ++ctrl+c++ if you don't find your desired link

![Demo of cancelling](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/pypi%20browse%20but%20cancel.gif)

### **Usage**

> pypi browse PACKAGE_NAME

### **Options**

- `PACKAGE_NAME`
  The name of the package to show the urls for.

- `-h`, `--help`

  Show the help message.

## cache-clear

Clears the local packages and requests cache, see [notes](https://wasi-master.github.io/pypi-command-line/notes#cache) for more information about the cache.

### **Usage**

> pypi cache-clear

### **Errors and Warnings**

#### <span style="color: red">E:</span> Failed to delete \<file_path\>

Shown when it cannot delete a file due to some other process using it or not having enough permissions

## cache-information

Shows the size for the packages cache and the size and additionally the websites cached with their creation date and expiry date, see [notes](https://wasi-master.github.io/pypi-command-line/notes#cache) for more information about the cache.

### **Errors and Warnings**

#### <span style="color: yellow">W:</span> Packages cache not available

Shown when the packages cache doesn't exist due to it not being created yet or being deleted recently. You can rebuild that cache using [`cache-refresh`](#cache-refresh)


#### <span style="color: yellow">W:</span> Requests cache not available

Shown when the requests cache doesn't exist due to the `requests-cache` package not being installed

### **Usage**

> pypi cache-information

## cache-refresh

Reloads the packages cache and shows the number of new packages added after the last refresh, see [notes](https://wasi-master.github.io/pypi-command-line/notes#cache) for more information about the cache.

### **Usage**

> pypi cache-refresh

## description

Shows the description of a package as gotten from PyPI or GitHub.

This first gets the information about the package and then finds the descripton. If the package has a descripton it gets the description format, if it's reStructuredText or Markdown then it shows the description formatted according to the format.

If it doesn't get a description in PyPI then it looks for github repos mentioned in the json response gotten from the pypi api. this makes sure it gets the repo if it is supplied no matter where it is. If it finds multiple repos then it asks the user to pick one. Then it uses the github api to find the name of the readme file of the repo, this uses the api instead of manually finding it just in case. Then it reads the contents from the readme file and determines the format using the file extension then it shows the description formatted according to the format.

### **Demo**

![Demo of the command](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/pypi%20desc.gif)

Demo of getting description from github if pypi does not have one

![Demo of it finding github repo and getting the description from there](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/pypi%20desc%20github.gif)

### **Usage**

> pypi description [OPTIONS] PACKAGE_NAME

### **Options**

- `PACKAGE_NAME`

  Package to get the description for <span style="color: red">[required]</span>
- `--force-github` / `--no-force-github`

  Forcefully get the description from github [<span style="color: blue">default:</span> no-force-github]

  This will make sure that it doesn't get the description from pypi but get it from github by reading the readme file of that project's repository
- `-h`, `--help`

  Show the help message.

### Errors and Warnings

#### <span style="color: red">E:</span> Project not found

Shown when the pypi api returns a 404 response meaning a package with the specified name most likely doesn't exist

#### <span style="color: red">E:</span> ReadMe not found

Shown when `--force-github` is enabled or the PyPI page doesn't have a description and the github page also doesn't have a readme

#### <span style="color: yellow">W:</span> Multiple github repos

Shown when `--force-github` is enabled or the PyPI page doesn't have a description. If this is shown it will ask you to pick one

## information

The information command gets data from [PyPI](https://pypi.org) and [GitHub](https://github.com) and [PyPIStats](https://pypistats.org) and shows them to the console

### **Demo**

![Demo of the command](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/pypi%20info.gif)

You can also see classifiers if you want to

![Demo with classifiers](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/pypi%20info%20with%20classifiers.gif)

### **Usage**

> pypi information [OPTIONS] PACKAGE_NAME

### **Options**

- PACKAGE_NAME <span style="color: red">[required]</span>
- --version TEXT

  The version of the package to show information for
- `--show-classifiers` / `--no-show-classifiers`

   Show the classifiers  [<span style="color: blue">default:</span> no-show-classifiers]
   ![Example of this flag](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/pypi%20info%20with%20classifiers.gif)
- `--hide-project-urls` / `--no-hide-project-urls`

  Hide the project urls  [<span style="color: blue">default:</span> no-hide-project-urls]
- `--hide-requirements` / `--no-hide-requirements`

  Hide the requirements  [<span style="color: blue">default:</span> no-hide-requirements]
- `--hide-github` / `--no-hide-github`

  Hide the github  [<span style="color: blue">default:</span> no-hide-github]
- `--hide-stats` / `--no-hide-stats`

  Hide the stats  [<span style="color: blue">default:</span> no-hide-stats]
- `--hide-meta` / `--no-hide-meta`

  Hide the metadata  [<span style="color: blue">default:</span> no-hide-meta]
- `-h`, `--help`

  Show the help message.

### **Errors and Warnings**

#### <span style="color: red">E:</span> Project not found

Shown when the pypi api returns a 404 response meaning a package with the specified name most likely doesn't exist

## largest-files

This command shows the all time largest pypi packages. The layout is simillar to the [one found in PyPI](https://pypi.org/stats/)

### **Demo**

![Demo of the command](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/pypi%20largest-files.gif)

### **Usage**

> pypi information [OPTIONS]

### **Options**

- `-h`, `--help`

  Show the help message.

### **Errors and Warnings**

#### <span style="color: red">E:</span> Project not found

Shown when the pypi api returns a 404 response meaning a package with the specified name most likely doesn't exist

## new-packages

Shows the top 40 newly added packages. Meaning that the first ever version of those packages were uploaded from pypi a short while ago.

### **Usage**

> pypi new-packages [OPTIONS]

### **Options**

- `-h`, `--help`

  Show the help message.

- `---author` / `--no--author`

  Whether to show the project author or not  [<span style="color: blue">default:</span> no--author]

  This usually shows the author's email.

`---link` / `--no--link`

  Whether to show the project link or not  [<span style="color: blue">default:</span> -link]

### **Errors and Warnings**

#### <span style="color: yellow">W:</span> `lxml` not installed

There is a known bug that occurs when lxml is not installed. It doesn't show descriptions in some cases. Please install lxml using `pip install lxml`.

## new-releases

Shows the top 100 newly updated packages. Meaning that the latest version of those packages were uploaded from pypi short while ago.

### **Usage**

> pypi new-releases [OPTIONS]

### **Options**

- `-h`, `--help`

  Show the help message.

- `---author` / `--no--author`

  Whether to show the project author or not  [<span style="color: blue">default:</span> no--author]

  This usually shows the author's email.

`---link` / `--no--link`

  Whether to show the project link or not  [<span style="color: blue">default:</span> -link]

### **Errors and Warnings**

#### <span style="color: yellow">W:</span> `lxml` not installed

There is a known bug that occurs when lxml is not installed. It doesn't show descriptions in some cases. Please install lxml using `pip install lxml`.

## releases

Shows all the available releases for a package.

The --link argument can be used to also show the link of the releases. This
is turned off by default and the link is added as a hyperlink to the package
name on supported terminals

### **Usage**

> pypi releases [OPTIONS] PACKAGE_NAME

### **Options**

- `PACKAGE_NAME`

  The name of the package to show releases for

- `-h`, `--help`

  Show the help message.

- `---author` / `--no--author`

  Whether to show the project author or not  [<span style="color: blue"><span style="color: blue">default:</span></span> no--author]

  This usually shows the author's email.

- `---link` / `--no--link`

  Whether to show the project link or not  [<span style="color: blue">default:</span> -link]

### **Errors and Warnings**

#### <span style="color: red">E:</span> Project not found

Shown when the pypi api returns a 404 response meaning a package with the specified name most likely doesn't exist

## regex-search

Regex stands for Regular Expressions. It allows you to search for all packages in PyPI and only show ones that match a specific Regular Expression<sup>[<a title="A regular expression (shortened as regex or regexp) is a sequence of characters that specifies a search pattern. Usually such patterns are used by string-searching algorithms." href="https://en.wikipedia.org/wiki/Regular_expression" target="_blank">?</a>]

If the packages cache is empty it then loads the packages first, the cache is kept for 1 day meaning your data is at most 1 day old. if you want to refresh you may do so by using the [cache-refresh](#cache-refresh) command. For more information about this cache see [notes](https://wasi-master.github.io/pypi-command-line/notes#cache).

### **Demo**

![Demo of the command](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/pypi%20rsearch.gif)

### **Usage**

> pypi regex-search [OPTIONS] REGEX

### **Options**

- `REGEX`
  The regular expression to search with  <span style="color: red">[required]</span>

- `--compact` / `--no-compact`
  Compact formatting  [<span style="color: blue">default:</span> no-compact]

  This removes the table and just shows the package names seperated by commands, it also adds hyperlinks on supported terminals

- `-h`, `--help`
  Show the help message.

## releases

Shows all the available releases for a package.

This can help you determine what versions of a package are available on PyPI.

### **Demo**

![Demo of the command](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/pypi%20releases.gif)

### **Usage**

> pypi releases [OPTIONS] PACKAGE_NAME

### **Options**

- `PACKAGE_NAME`
  The name of package to show releases for <span style="color: red">[required]</span>

- `---link` / `--no--link`
  Display the links to the releases  [<span style="color: blue">default:</span> no--link]

  This is mostly not required unless you want to download that specific releases too but in that case `pip install PACKAGE_NAME==x.x.x` is better. And the link is already shown as a hyperlink on supported terminals.

- -h, --help
  Show the help message.

### **Errors and Warnings**

#### <span style="color: red">E:</span> Project not found

Shown when the pypi api returns a 404 response meaning a package with the specified name most likely doesn't exist

## search

Search for a package on PyPI.

### **Demo**

![Demo of the command](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/pypi%20search.gif)

### **Usage**

> pypi search [OPTIONS] PACKAGE_NAME

### **Options**

- `PACKAGE_NAME`
  The name of the package to search for  <span style="color: red">[required]</span>

- `--page INTEGER RANGE`
  The page of the search results to show. [<span style="color: blue">default:</span> 1; <span style="color: green">1<=x<=500</span>]

  ![Demo of the flag](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/pypi%20search%20with%20page.gif)

- -h, --help
  Shows the help message.

### **Errors and Warnings**

#### <span style="color: red">E:</span> Project not found

Shown when the pypi api returns a 404 response meaning the page number specified most likely doesn't exist

## wheels

See the available wheels of a release on PyPI. The wheel names are color coded and the information is colored too.

### **Demo**

![Demo of the command](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/pypi%20wheels.gif)

### **Usage**

> pypi search [OPTIONS] PACKAGE_NAME [VERSION]

### **Options**

- `PACKAGE_NAME`
  The name of the package to show wheel info for  <span style="color: red">[required]</span>

- `VERSION`
  The version of the package to show info for, defaults to latest

- -h, --help
  Shows the help message.

- --supported-only
  Only show wheels supported on the current platform

### Wheel Name Syntax

The wheel filename is `{distribution}-{version}(-{build tag})?-{python tag}-{abi tag}-{platform tag}.whl`.

![Image showing a wheel](https://i.imgur.com/6v2ubKU.png)

> <span style="color: #92EC5A;">distribution</span>

- Distribution name, e.g. 'pypi_command_line', 'django'.

> <span style="color: #F2C259;">version</span>

- Distribution version, e.g. 1.0.

> <span style="color: #FFF075;">build tag (<b>Optional</b>)</span>

- build number. Must start with a digit. Acts as a tie-breaker if two wheel file names are the same in all other respects (i.e. name, version, and other tags). Sort as an empty tuple if unspecified, else sort as a two-item tuple with the first item being the initial digits as an `int`, and the second item being the remainder of the tag as a `str`.

> <span style="color: #FF6EF8;">language implementation and version tag</span>

- E.g. 'py27', 'py2', 'py3'.

> <span style="color: #9263FB;">abi tag</span>

- E.g. 'p33m', 'abi3', 'none'.

> <span style="color: #33F1C8;">platform tag</span>

- E.g. 'linux_x86_64', 'any'.

> <span style="color: #33F1C8;">platform tag</span>

- E.g. 'linux_x86_64', 'any'.

For example, `distribution-1.0-1-py27-none-any.whl` is the first build of a package called 'distribution', and is compatible with Python 2.7 (any Python 2.7 implementation), with no ABI (pure Python), on any CPU architecture.

The last three components of the filename before the extension are called "compatibility tags." The compatibility tags express the package's basic interpreter requirements and are detailed in [PEP 425](https://www.python.org/dev/peps/pep-0425/).

\- Gotten from <https://www.python.org/dev/peps/pep-0427/#file-name-convention>

### **Errors and Warnings**

#### <span style="color: red">E:</span> Project not found

Shown when the pypi api returns a 404 response meaning the project name specified doesn't exist.

#### <span style="color: red">E:</span> Version not found

Shown when the specified version was not found.
