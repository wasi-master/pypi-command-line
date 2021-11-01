# pypi-command-line

[![Version](https://img.shields.io/pypi/v/pypi-command-line?label=pypi%20version&style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/pypi-command-line/)
[![Lines of code](https://img.shields.io/tokei/lines/github/wasi-master/pypi-command-line?style=flat-square&logo=python&logoColor=white)](https://github.com/wasi-master/pypi-command-line/)
[![Downloads yesterday](https://img.shields.io/pypi/dd/pypi-command-line?label=pypi%20downloads%20yesterday&style=flat-square&logo=pypi&logoColor=white)](https://pypistats.org/packages/pypi-command-line)
[![Downloads in the last 7 days](https://img.shields.io/pypi/dw/pypi-command-line?label=pypi%20downloads%20in%20the%20last%207%20days&style=flat-square&logo=pypi&logoColor=white)](https://pypistats.org/packages/pypi-command-line)
[![Downloads in the last 30 days](https://img.shields.io/pypi/dm/pypi-command-line?label=pypi%20downloads%20in%20the%20last%2030%20days&style=flat-square&logo=pypi&logoColor=white)](https://pypistats.org/packages/pypi-command-line)
[![Number of issues](https://img.shields.io/github/issues/wasi-master/pypi-command-line?style=flat-square&logo=github&logoColor=white)](https://github.com/wasi-master/pypi-command-line/issues)
[![Number of pull requests](https://img.shields.io/github/issues-pr-closed/wasi-master/pypi-command-line?style=flat-square&logo=github&logoColor=white)](https://github.com/wasi-master/pypi-command-line/pulls)
[![Number of stars on GitHub](https://img.shields.io/github/stars/wasi-master/pypi-command-line?style=flat-square&logo=github&logoColor=white)](https://github.com/wasi-master/pypi-command-line/stargazers)
[![Supported python versions](https://img.shields.io/pypi/pyversions/pypi-command-line?label=supported%20python%20versions&style=flat-square&logo=python&logoColor=white)](https://pypi.org/project/pypi-command-line/#:~:text=requires%3A%20python%20%3E%3D3.6)
[![Python Implementation](https://img.shields.io/pypi/implementation/pypi-command-line?label=python%20implementation&style=flat-square&logo=python&logoColor=white)](https://pypi.org/project/pypi-command-line/#:~:text=programming%20language)
[![PyPI Wheel availability](https://img.shields.io/pypi/wheel/pypi-command-line?label=pypi%20wheel%20availabile%3F&style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/pypi-command-line/#files)
[![Documentation status](https://img.shields.io/website?down_color=red&down_message=not%20working&label=docs&logo=github&style=flat-square&up_color=blue&up_message=working&url=https%3A%2F%2Fwasi-master.github.io%2Fpypi-command-line%2F)](https://wasi-master.github.io/pypi-command-line)

A powerful command line interface for <https://pypi.org>

Detailed Documentation available at <https://wasi-master.github.io/pypi-command-line/>

## Features

- 🚀 Extremely intuitive and easy to use.
- 🌟 Beautiful UI with pleasant colors *everywhere*.
- 😁 Emojis in responses and errors.
- 📰 Great Markdown and reStructuredText support for viewing project descriptions.
- 😎 Many features (There are optional parameters for extra information too!).
  - See in-depth information about a package including it's download count and github repo stats.
  - See beautifully rendered markdown/rst/plain text description of a package
  - Search for packages with the same information as pypi and even filter them.
  - Search for packages with regex, for example using `flask-.+` will show all flask extensions.
  - Browse for a package's URLs and open any of those URLs inside a browser with a beautiful colored link selection menu
  - See all the releases of a package, along with when they were made and their size.
  - See New projects and new releases [just like PyPI](https://pypi.org#pypi-trending-packages).
  - See top 100 of the largest packages [just like PyPI](https://pypi.org/stats/).
- 💻 Cross-platform.
- 🤯 Open source.
- 📚 Extensive documentation.

## Screenshots

<details open>
<summary>Click to hide screenshots</summary>

Command name and parameter autocompletion
![Autocomplete](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/autocomplete%20example.gif "Autocomplete")
Smart error handling
![Error Handling](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/error%20handling.gif "Error Handling")
Auto command aliases
![Smart Command Aliasing](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/smart_alias.png "Smart Command Aliasing")
Search feature that gives the same results as on PyPI
![Search for a package using PyPI](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/pypi%20search.gif "Search for a package using PyPI")
See detailed information about a project
![See project information](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/pypi%20info.gif "See project information")
View the project description right in your terminal with rich Markdown and reStructuredText formatting
![Get description from PyPI](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/pypi%20desc.gif "Get description from PyPI")
View the project readme from github
![Get readme content from GitHub](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/pypi%20desc%20github.gif "Get readme content from GitHub")
Search for packages using regular expresssions
![Search for packages using regex](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/pypi%20rsearch.gif "Search for packages using regex")
Open the package's URLs gotten from PyPI
![Browse for URLs](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/pypi%20browse%20alligned.gif "Browse for URLs")
See the project information with classifiers
![See project information with classifiers](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/pypi%20info%20with%20classifiers.gif "See !project information with classifiers")
See the all time largest projects in PyPI
![See all time largest projects in PyPI](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/pypi%20largest-files.gif "See all time largest !projects in PyPI")
Install autocompletion for the current shell
![Install Completion](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/pypi%20--install-completion.gif "Install Completion")
See the source code for the autocompletion
![Show Completion](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/pypi%20--show-completion.gif "Show Completion")
See a specific page of the search results
![Specify a page to search to](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/pypi%20search%20with%20page.gif "Specify a page to search to")

</details>

## Installation

- Installing from PyPI (recommended).

  ```sh
  pip install pypi-command-line
  ```

  If you want to also install [speed dependencies](https://wasi-master.github.io/pypi-command-line/notes#speedups)

  ```sh
  pip install "pypi-command-line[speedups]"
  ```

- Installing from source.

  ```sh
  pip install git+https://github.com/wasi-master/pypi-command-line.git
  ```

  If you want to also install [speed dependencies](https://wasi-master.github.io/pypi-command-line/notes#speedups)

  ```sh
  pip install "pypi-command-line[speedups] @ git+https://github.com/wasi-master/pypi-command-line.git"
  ```

## Usage

To see all the available commands use:

```sh
pypi --help
```

For more information on a certain command use `pypi <command_name> --help`. For example,

```sh
pypi search --help
```

For a full guide see <https://wasi-master.github.io/pypi-command-line/usage>.
