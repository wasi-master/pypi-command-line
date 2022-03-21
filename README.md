# pypi-command-line

`pypi-command-line` is a **colorful**, **powerful**, and **beautiful** command line interface for [pypi.org](https://pypi.org "The Python Package Index (PyPI) is a repository of software for the Python programming language.") that is actively maintained

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
  - Many more... (
    command list includes
      [`browse`](https://wasi-master.github.io/pypi-command-line/usage/#browse),
      [`information`](https://wasi-master.github.io/pypi-command-line/usage/#information),
      [`description`](https://wasi-master.github.io/pypi-command-line/usage/#description),
      [`search`](https://wasi-master.github.io/pypi-command-line/usage/#search),
      [`wheels`](https://wasi-master.github.io/pypi-command-line/usage/#wheels),
      [`releases`](https://wasi-master.github.io/pypi-command-line/usage/#releases),
      [`largest-files`](https://wasi-master.github.io/pypi-command-line/usage/#largest-files),
      [`regex-search`](https://wasi-master.github.io/pypi-command-line/usage/#regex-search),
      [`version`](https://wasi-master.github.io/pypi-command-line/usage/#version),
      [`cache-info`](https://wasi-master.github.io/pypi-command-line/usage/#cache-info),
      [`cache-refresh`](https://wasi-master.github.io/pypi-command-line/usage/#cache-refresh),
      [`cache-clear`](https://wasi-master.github.io/pypi-command-line/usage/#cache-clear),
      [`new-packages`](https://wasi-master.github.io/pypi-command-line/usage/#new-packages),
      [`new-releases`](https://wasi-master.github.io/pypi-command-line/usage/#new-releases),
      [`read-the-docs`](https://wasi-master.github.io/pypi-command-line/usage/#read-the-docs)
    )
- 💻 Cross-platform.
- 🤯 Open source.
- 📚 Extensive documentation.

## Info

<details open>
<summary>Hide Info</summary>

### Download Count

I've included both [PePy](https://pepy.tech/) and [PyPIStats](https://pypistats.org/) since PyPIStats by default does not include mirrors in it's count<sup>[1](https://pypistats.org/faqs#why-are-the-cumulative-download-counts-different-from-the-sum-of)</sup>. Also see <https://github.com/psincraian/pepy/issues/351>

| Period | From [PePy](https://pepy.tech/project/pypi-command-line)                                                                                                                                             | From [PyPiStats](https://pypistats.org/packages/pypi-command-line)                                                                                                               |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Day    |                                                                                                                                                                                                     | [![Downloads yesterday](https://img.shields.io/pypi/dd/pypi-command-line?label=Day&labelColor=black&color=orange)](https://pypistats.org/packages/pypi-command-line)             |
| Week   | [![Downloads](https://static.pepy.tech/personalized-badge/pypi-command-line?period=week&units=none&left_color=black&right_color=blue&left_text=Week)](https://pepy.tech/project/pypi-command-line)   | [![Downloads in the last 7 days](https://img.shields.io/pypi/dw/pypi-command-line?label=Week&labelColor=black&color=orange)](https://pypistats.org/packages/pypi-command-line)   |
| Month  | [![Downloads](https://static.pepy.tech/personalized-badge/pypi-command-line?period=month&units=none&left_color=black&right_color=blue&left_text=Month)](https://pepy.tech/project/pypi-command-line) | [![Downloads in the last 30 days](https://img.shields.io/pypi/dm/pypi-command-line?label=Month&labelColor=black&color=orange)](https://pypistats.org/packages/pypi-command-line) |
| Total  | [![Downloads](https://static.pepy.tech/personalized-badge/pypi-command-line?period=total&units=none&left_color=black&right_color=blue&left_text=Total)](https://pepy.tech/project/pypi-command-line) |

### Meta

| Title                     | Badge                                                                                                                                                                                                                                                            |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Version                   | [![Version](https://img.shields.io/pypi/v/pypi-command-line?label=pypi%20version&style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/pypi-command-line/)                                                                                      |
| Wheel availability        | [![PyPI Wheel availability](https://img.shields.io/pypi/wheel/pypi-command-line?label=pypi%20wheel%20availabile%3F&style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/pypi-command-line/#files)                                              |
| Supported python versions | [![Supported python versions](https://img.shields.io/pypi/pyversions/pypi-command-line?label=supported%20python%20versions&style=flat-square&logo=python&logoColor=white)](https://pypi.org/project/pypi-command-line/#:~:text=requires%3A%20python%20%3E%3D3.6) |
| Python Implementation     | [![Python Implementation](https://img.shields.io/pypi/implementation/pypi-command-line?label=python%20implementation&style=flat-square&logo=python&logoColor=white)](https://pypi.org/project/pypi-command-line/#:~:text=programming%20language)                 |

### GitHub

| Title                   | Badge                                                                                                                                                                                                                                  |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Number of issues open   | [![Number of issues open](https://img.shields.io/github/issues/wasi-master/pypi-command-line?style=flat-square&logo=github&logoColor=white&label=issues%20open)](https://github.com/wasi-master/pypi-command-line/issues)              |
| Number of issues closed | [![Number of issues closed](https://img.shields.io/github/issues-closed/wasi-master/pypi-command-line?label=issues%20closed&style=flat-square&logo=github&logoColor=white)](https://github.com/wasi-master/pypi-command-line/issues?q=is%3Aissue++is%3Aclosed+)                                                             |
| Number of pull requests | [![Number of pull requests](https://img.shields.io/github/issues-pr-closed/wasi-master/pypi-command-line?style=flat-square&logo=github&logoColor=white&label=pull%20requests)](https://github.com/wasi-master/pypi-command-line/pulls) |
| Number of stars         | [![Number of stars on GitHub](https://img.shields.io/github/stars/wasi-master/pypi-command-line?style=flat-square&logo=github&logoColor=white)](https://github.com/wasi-master/pypi-command-line/stargazers)                           |

### Misc

| Title                | Badge                                                                                                                                                                                                                                                                                         |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Documentation status | [![Documentation status](https://img.shields.io/website?down_color=red&down_message=not%20working&label=docs&logo=github&style=flat-square&up_color=blue&up_message=working&url=https%3A%2F%2Fwasi-master.github.io%2Fpypi-command-line%2F)](https://wasi-master.github.io/pypi-command-line) |
| Lines of code        | [![Lines of code](https://img.shields.io/tokei/lines/github/wasi-master/pypi-command-line?style=flat-square&logo=python&logoColor=white)](https://github.com/wasi-master/pypi-command-line/)                                                                                                  |

</details>

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

## Alternatives

### [pypi-cli](https://pypi.org/project/pypi-cli/ "pypi-cli")

Now this probably was the best option before `pypi-command-line` came out and it does have some flaws. The `information` command of pypi-cli is pretty minimal, there's no way of seeing the github information, The download count doesn't work properly, the long descriptions aren't formatted at all with pypi-cli. pypi-cli uses the xml-rpc<sup>[<a title="XML-RPC is a remote procedure call (RPC) protocol which uses XML to encode its calls and HTTP as a transport mechanism." href="https://en.wikipedia.org/wiki/XML-RPC" target="_blank">?</a>]</sup> API that is discontinued So the search feature doesn't work anymore, . The stat command is broken and is badly formatted for screens that are not ultra wide. And the project is unmaintained and archived

**TL;DR** The `stat` and `search` commands don't work anymore, the information command kinda works but the download count doesn't work, can't see github information, descriptions are raw.

### [pypi-client](https://pypi.org/project/pypi-client/ "pypi-client")

So this can just search for packages on pypi and thats it. Now don't you think that this is inherently bad as per se. So I tried it out immediately and it just got stuck loading the packages, pypi-client gets names of all the packages that exist pypi<sup><a title=Reference href="https://github.com/abahdanovich/pypi-client#:~:text=fetches%20all%20package%20names%20from%20pypi" target="_blank">‾</a></sup> which took like 4 mins, then I assume it downloads the github stars data?<sup><a title=Reference href="https://github.com/abahdanovich/pypi-client#:~:text=downloads%20github%20stars" target="_blank">‾</a></sup> Which takes like another 3 mins and then It just asked me to authorize with github… like why does pypi-client even need authorization from me since github has a public api. And then it showed [this](https://i.imgur.com/D0VJhmZ.png "Demo of the program that has been badly formatted") which isn't really unreadable just badly formatted for screens that are not ultra wide. by changing the font size a bit I could make it look like [this](https://i.imgur.com/usU2AnJ.jpeg "Demo of the program after lowering the font size") which still isn't bad just a bit convoluted. And even at the end of the day the results are manually searched through therefore different from pypi<sup><a title=Example href="https://i.imgur.com/2AuCKuX.jpg" target="_blank">‾</a></sup>

**TL;DR:**
Takes too long (≈7 mins), Needs github authorization, badly formatted for non ultra wide monitors, searches manually so results are different compared to pypi

### [yolk](https://pypi.org/project/yolk/ "yolk")

Discontinued 9 years ago, only supports python 2. Uses flags instead of subcommands for everything.

**TL;DR:**
Is this really necessary?

### [qypi](https://pypi.org/project/qypi/ "qypi")

So, this library is most likely the best alternative for pypi-command-line. But the output is in json, uses the xml-rpc api for search which is discontinued, the readme command doesn't work for me, the list command doesn't have a progressbar

**TL;DR:**
Output is only in json, without color. The search command doesn't work anymore. Has no progressbar for long running tasks
