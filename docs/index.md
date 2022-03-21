---
layout: page
title: Documentation for pypi-command-line
description: pypi-command-line is a powerful, colorful, beautiful command line interface for pypi.org that is well maintained
---

# Welcome to pypi-command-line documentation

`pypi-command-line` is a powerful command line interface for [pypi.org](https://pypi.org "The Python Package Index (PyPI) is a repository of software for the Python programming language.")

## What is this?

It's a command line interface<sup>[<a title="A command-line interface (CLI) processes commands to a computer program in the form of lines of text." href="https://en.wikipedia.org/wiki/Command-line_interface" target="_blank">?</a>]</sup> (CLI) that you can use to run commands<sup>[<a title="In computing, a command is a directive to a computer program to perform a specific task." href="https://en.wikipedia.org/wiki/Command_(computing)" target="_blank">?</a>]</sup> in a terminal<sup>[<a title="The terminal is an interface that allows you to access the command line." href="https://en.wikipedia.org/wiki/Computer_terminal" target="_blank">?</a>]</sup>

## Why is this?

There are [a few alternatives](#alternatives "List containing 2 alternatives") (namely [pypi-cli](https://pypi.org/project/pypi-cli/ "pypi-cli pypi page") and [pypi-client](https://pypi.org/project/pypi-client/ "pypi-client pypi page")) that I've come across but none of those offer the same amount of functionality and beautifulness<sup>[<a title="The qualities in something that give pleasure to the senses" href="https://www.merriam-webster.com/thesaurus/beautifulness" target="_blank">?</a>]</sup> or even the same [amount of speed](#benchmarks-for-speed "Benchmarks for Speed").

## Installation and Usage

- For installation instructions see [installation](https://wasi-master.github.io/pypi-command-line/install) for instructions.
- For usage details see [usage](https://wasi-master.github.io/pypi-command-line/usage "Page containing usage instructions")

## Alternatives

### [pypi-cli](https://pypi.org/project/pypi-cli/ "pypi-cli")

Now this probably was the best option before `pypi-command-line` came out and it does have some flaws. The `information` command of pypi-cli is pretty minimal, there's no way of seeing the github information, The download count doesn't work properly, the long descriptions aren't formatted at all with pypi-cli. pypi-cli uses the xml-rpc<sup>[<a title="XML-RPC is a remote procedure call (RPC) protocol which uses XML to encode its calls and HTTP as a transport mechanism." href="https://en.wikipedia.org/wiki/XML-RPC" target="_blank">?</a>]</sup> API that is discontinued So the search feature doesn't work anymore, . The stat command is broken and is badly formatted for screens that are not ultra wide. And the project is unmaintained and archived

**TL;DR** The `stat` and `search` commands don't work anymore, the information command kinda works but the download count doesn't work, can't see github information, descriptions are raw.

### [pypi-client](https://pypi.org/project/pypi-client/ "pypi-client")

So this can just search for packages on pypi and thats it. Now don't you think that this is inherently bad as per say. So I tried it out immediately and it just got stuck loading the packages, pypi-client gets names of all the packages that exist pypi<sup><a title=Reference href="https://github.com/abahdanovich/pypi-client#:~:text=fetches%20all%20package%20names%20from%20pypi" target="_blank">‾</a></sup> which took like 4 mins, then I assume it downloads the github stars data?<sup><a title=Reference href="https://github.com/abahdanovich/pypi-client#:~:text=downloads%20github%20stars" target="_blank">‾</a></sup> Which takes like another 3 mins and then It just asked me to authorize with github… like why does pypi-client even need authorization from me since github has a public api. And then it showed [this](https://i.imgur.com/D0VJhmZ.png "Demo of the program that has been badly formatted") which isn't really unreadable just badly formatted for screens that are not ultra wide. by changing the font size a bit I could make it look like [this](https://i.imgur.com/usU2AnJ.jpeg "Demo of the program after lowering the font size") which still isn't bad just a bit convoluted. And even at the end of the day the results are manually searched through therefore different from pypi<sup><a title=Example href="https://i.imgur.com/2AuCKuX.jpg" target="_blank">‾</a></sup>

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


## Benchmarks for speed

### `… search discord`

- pypi-command-line - **1.4221807**

    Takes around 1.5 secs to do a get request to the pypi search page then parse and return the results so that the results are the exact same as shown in [pypi.org](https://pypi.org "The Python Package Index (PyPI) is a repository of software for the Python programming language.")

- pypi-client - **7.4170682**

    Takes 7 secs to get all packages and show ones containing discord, `pypi-command-line` can achieve the same result in `1.22`<sup>[<a title="Real Speed is 1.2205886" href="javascript: void(0)">*</a>]</sup> seconds using `pypi regex-search discord` (the command allows you to search with regex)

- pypi-cli - **doesn't work** anymore

    The command doesn't work anymore since pypi has discontinued it's xml-rpc api<sup><a title=Reference href="https://status.python.org/incidents/grk0k7sz6zkp" target="_blank">‾</a></sup>

### `… information django`

- pypi-cli - **0.9757808**

    Now I do have to admit that this is faster, mainly because this does a single api call but mine does 3. You do have to realise that you are getting [this](https://i.imgur.com/X7OuPIb.png "Less information without color") instead of [this](https://i.imgur.com/s8aQx09.png "More detailed information with colored formatting")

- pypi-command-line - **2.0484411**

    This does take longer but it's using that time to get not only the pypi stats but the *proper* download stats and github stats along with the pypi stats, disabling those lowers this time to `1.35`<sup>[<a title="Real Speed is 1.3591562" href="javascript: void(0)">*</a>]</sup> seconds.

- pypi-client - **can't see information**

    You can't see project information with this package, you can only search for stuff.

Notes: <https://wasi-master.github.io/pypi-command-line/notes>
