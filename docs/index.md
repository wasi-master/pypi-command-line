# Welcome to pypi-command-line documentation

`pypi-command-line` is a A powerful command line interface for [pypi.org](https://pypi.org)

## What is this?

It's a command line interface<sup>[<a title="A command-line interface (CLI) processes commands to a computer program in the form of lines of text." href="https://en.wikipedia.org/wiki/Command-line_interface">?</a>]</sup> that you can use to run commands<sup>[<a title="In computing, a command is a directive to a computer program to perform a specific task." href="https://en.wikipedia.org/wiki/Command_(computing)">?</a>]</sup> in a terminal<sup>[<a title="The terminal is an interface that allows you to access the command line." href="https://en.wikipedia.org/wiki/Computer_terminal">?</a>]</sup>

## Why is this?

There are [a few alternatives](#alternatives) that I've come across but none of those offer the same amount of functionality and beautifulness<sup>[<a title="The qualities in something that give pleasure to the senses" href="https://www.merriam-webster.com/thesaurus/beautifulness">?</a>]</sup> or even the same [amount of speed](#benchmarks-for-speed).

## Usage

For usage details see [usage](https://wasi-master.github.io/pypi-command-line/usage)

## Alternatives

### [pypi-cli](https://pypi.org/project/pypi-cli/)

Now this probably was the best option before `pypi-command-line` came out and even it has some flaws. The `info` command is pretty minimal, there's no way of seeing the github info, The download count doesn't work, the long descriptions aren't formatted at all. The search feature doesn't even work at all. It used to use the xml-rpc<sup>[<a title="XML-RPC is a remote procedure call (RPC) protocol which uses XML to encode its calls and HTTP as a transport mechanism." href="https://en.wikipedia.org/wiki/XML-RPC">?</a>]</sup> API that is discontinued therefore the feature doesn't work anymore. The stat command is broken and is badly formatted for screens that are not ultra high resolution.

**TL;DR** The `stat` and `search` commands don't work anymore, the info command kinda works but the download count doesn't work, can't see github info.

### [pypi-client](https://pypi.org/project/pypi-client/)

So this can just search for packages on pypi and thats it. Now don't you think that this is inherently bad as per say. So I tried it out immediately and it just got stuck loading the packages, it gets all package names from pypi<sup><a title=Reference href="https://github.com/abahdanovich/pypi-client#:~:text=fetches%20all%20package%20names%20from%20pypi">‾</a></sup> which took like 4 mins, then I assume it downloads the github stars?<sup><a title=Reference href="https://github.com/abahdanovich/pypi-client#:~:text=downloads%20github%20stars">‾</a></sup> Which takes like another 3 mins and then It just asked me to authorize… like why does it even need authorization from me since github has a public api. And then it showed [this](https://i.imgur.com/D0VJhmZ.png) which isn't really unreadable just badly formatted for screens that are not ultra high resolution. by changing the font size a bit I could make it look like [this](https://i.imgur.com/usU2AnJ.jpeg) which still isn't bad just a bit convoluted. And even at the end the results are manually searched through therefore different from pypi<sup><a title=Example href="https://i.imgur.com/2AuCKuX.jpg">‾</a></sup>

**TL;DR:**
Takes too long (≈7 mins), Needs github authorization, badly formatted for non ultra-high-end monitors, searches manually so results are different compared to pypi

## Benchmarks for speed

### `… search discord`

- pypi-command-line - **1.9511792**

    Takes around 2 secs to do a get request to the pypi search page then parse and return the results so that the results are the exact same as shown in [pypi.org](https://pypi.org)

- pypi-client - **7.4170682**

    Takes 7 secs to get all packages and show ones containing discord, `pypi-command-line` can achieve the same result in [`4.33`](# "04.3348642") seconds using `pypi rsearch discord` (r stands for regex, the command allows you to search with regex)

- pypi-cli - **doesn't work** anymore

    The command doesn't work anymore since pypi has discontinued it's xml-rpc api<sup><a title=Reference href="https://status.python.org/incidents/grk0k7sz6zkp">‾</a></sup>

### `… info django`

- pypi-cli - **0.9757808**

    Now I do have to admit that this is faster, mainly because this does a single api call but mine does 3. You do have to realise that you are getting [this](https://i.imgur.com/X7OuPIb.png) instead of [this](https://i.imgur.com/s8aQx09.png)

- pypi-command-line - **2.1925032**

    This does take longer but it's using that time to get not only the pypi stats but the *proper* download stats and github stats along with the pypi stats, disabling those lowers this time to [1.35](# "1.3591562") seconds.

- pypi-client - **can't see info**

    You can't see project info with this package, you can only search for stuff.
