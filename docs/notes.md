---
layout: page
title: Notes for pypi-command-line
description: pypi-command-line is a powerful, colorful, beautiful command line interface for pypi.org that is well maintained
---

# Notes

This page explains certain aspects of the code.

## Optimizations

### Imports outside top level

> import statements can be executed just about anywhere. It's often useful to place them inside functions to restrict their visibility and/or reduce initial startup time. Although Python's interpreter is optimized to not import the same module multiple times, repeatedly executing an import statement can seriously affect performance in some circumstances.

From <https://wiki.python.org/moin/PythonSpeed/PerformanceTips#Import_Statement_Overhead>

Because of this, I've added imports in each function that needs them instead of adding them at the top. since the user is only gonna run one single command the imports required for other commands don't need to be imported. Doing this saves around 500ms.

### Compiling regex in `regex-search`

I compile the regex because it's almost twice as fast.

```python
>>> timeit.timeit(not_compiled, number=5)
6.0103950999999824
>>> timeit.timeit(compiled, number=5)
3.9251674000000207
```

??? example "Code"

    Source code for non compiled regex:

    ```python linenums="1"
    def no_compile():
        for i in range(1000000):
            re.match(r".+", secrets.token_hex(32))
    ```

    Source code for compiled regex:

    ```python linenums="1"
    def no_compile():
        r = re.compile(r".+")
        for i in range(1000000):
            r.match(secrets.token_hex(32))
    ```


### Speedups

You may have seen that you can do `#!sh pip install "pypi-command-line[speedups]"` and you may have wondered what that actually does.
If you see the source code [you can see these lines](https://github.com/wasi-master/pypi-command-line/blob/main/setup.cfg#L79-L84)

```ini linenums="79"
[options.extras_require]
speedups =
    lxml
    rapidfuzz
    requests_cache
    shellingham
    ujson
```

Here's a detailed explanation of what each of those packages do

#### [**shellingham**](https://pypi.org/project/shellingham/)

This does not really speed up anything but adds auto shell detection for autocomplete installation using the `#!sh --install-completion ` command. This technically lowers the amount of time taken to install autocompletion because it makes it so that you don't have to manually provide what terminal/shell you're using

#### [**lxml**](https://pypi.org/project/lxml/)

This is an alternative for the built-in [html.parser](https://docs.python.org/3/library/html.parser.html) that comes with python. There is also [`html5lib`](https://pypi.org/project/html5lib/)

??? info "Table with parser comparisons supported by BeautifulSoup"

    | Parser               | Typical usage                                                                        | Advantages                                                                                                              | Disadvantages                                                   |
    | -------------------- | ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
    | Python's html.parser | `#!python BeautifulSoup(markup, "html.parser")`                                      | <ul> <li>Batteries included </li><li>Decent speed </li><li>Lenient (As of Python 2.7.3 &amp; 3.2.)</li></ul>                                       | <ul> <li>Not as fast as lxml, less lenient than html5lib.</li></ul>              |
    | lxml's HTML parser   | `#!python BeautifulSoup(markup, "lxml")`                                             | <ul> <li>Very fast</li><li>Lenient</li></ul>                                                                                                | <ul> <li>External C dependency</li></ul>                                         |
    | lxml's XML parser    | `#!python BeautifulSoup(markup, "lxml-xml")` `#!python BeautifulSoup(markup, "xml")` | <ul> <li>Very fast </li><li>The only currently supported XML parser</li></ul>                                                                | <ul> <li>External C dependency</li></ul>                                         |
    | html5lib             | `#!python BeautifulSoup(markup, "html5lib")`                                         | <ul> <li>Extremely lenient </li><li>Parses pages the same way a web browser does </li><li>Creates valid HTML5</li></ul> | <ul> <li>Very slow</li><li>External Python dependency</li></ul> |

    \- From <https://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-a-parser>


If this is not installed it uses [html.parser](https://docs.python.org/3/library/html.parser.html) for html and [xml.etree.ElementTree](https://docs.python.org/3/library/xml.etree.elementtree.html) for xml.

- For XML

    `lxml` is more than 10 times faster `than xml.etree.ElementTree`<sup>[<a title="Reference" href="https://lxml.de/performance.html#:~:text=lxml%20is%20still%20more%20than%2010%20times%20as%20fast%20as%20the%20much%20improved%20elementtree%201.3%20in%20recent%20python%20versions" target="_blank">‾</a>]</sup>

- For HTML

    `lxml` is more than 5 times faster than `html.parser` <sup>[<a title="Reference" href="https://www.ianbicking.org/blog/2008/03/python-html-parser-performance.html#:~:text=from%C2%A0python.org.-,parsing,-The%20first%20test" target="_blank">‾</a>]</sup>

#### [**requests-cache**](https://pypi.org/project/requests-cache/)

This allows http requests to be faster by caching<sup>[<a title="Caching is a process that stores multiple copies of data or files in a temporary storage location—or cache—so they can be accessed faster." href="https://aws.amazon.com/caching/" target="_blank">?</a>]</sup> them

#### [**rapidfuzz**](https://pypi.org/project/rapidfuzz/)

This allows rapid fuzzy string matching around 20 times faster than thefuzz

#### [**ujson**](https://pypi.org/project/ujson/)

This allows json parsing to be ultra fast

## Dependencies

### [Rich](https://github.com/willmcgugan/rich)

This allows the beautiful formatting that you can see when using the commands. [Colors](https://rich.readthedocs.io/en/latest/markup.html), [Tables](https://rich.readthedocs.io/en/latest/tables.html), [Panels](https://rich.readthedocs.io/en/latest/panel.html), [Progress Bars](https://rich.readthedocs.io/en/latest/progress.html) and much more.

### [Typer](https://typer.tiangolo.com)

This allows the command line interface to work properly. Although it's just a wrapper over [`click`](https://click.palletsprojects.com/en/8.0.x/) and the main stuff is done by click. typer adds some extra features over click such as autocompletion. That's why I've chosen typer over click.

### [Requests](https://requests.readthedocs.io/en/master/)

For HTTP web requests

### [Questionary](https://questionary.readthedocs.io/en/stable/)

For cool prompts.

### [Humanize](https://python-humanize.readthedocs.io/en/latest/)

For human readable data

### [bs4 (BeautifulSoup)](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

For parsing html and xml data

### [TheFuzz](https://github.com/seatgeek/thefuzz)

For fuzzy string matching

### [Rich RST](https://pypi.org/project/rich-rst/)

For pretty-printing reStructuredText descriptions

### [Packaging](https://packaging.pypa.io/en/latest/)

For version parsing

### [Wheel Filename](https://github.com/jwodder/wheel-filename)

For parsing wheel filenames

## Dependency Installation Notes

| Name                      | Applicable Commands                                        | Note                                                                                                                                                                                                                                                 |
| ------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| typer                     | meta                                                       |                                                                                                                                                                                                                                                      |
| rich                      | all                                                        |                                                                                                                                                                                                                                                      |
| requests                  | meta                                                       |                                                                                                                                                                                                                                                      |
| humanize                  | all                                                        |                                                                                                                                                                                                                                                      |
| bs4                       | search, new-packages (optional), new-releases (optional)   | If lxml and this both are installed then this is used for new-packages and new-releases and can provide up to a 5x improvement in speed and avoid a bug where the descriptions are not shown.                                                        |
| questionary               | rtfd, browse, description (optional)                       | For the description command, if the pypi page doesn't have a descripton, if it mentions a single github repository then this is not required but if it mentions multiple github repos then you'll need to select one therefore this will be required |
| thefuzz (optional)        | meta (command suggestions when an invalid command is used) | If this is not available then it uses difflib                                                                                                                                                                                                        |
| rich-rst                  | description (sometimes)                                    | This will only be required in the `description` command if the description is in reStructuredText                                                                                                                                                    |
| shellingham (optional)    | --install-completion                                       | This is only required to automatically detect the terminal when installing autocomplete for the current shell. without this you'd have to manually pass the shell as an argument to `install-completion`                                             |
| lxml (optional)           | search, new-packages (optional), new-releases (optional)   | For the search command this is a must have. for the new-packages and new-releases command this can provide up to 5x speed improvement and avoid a bug where the descriptions are not shown.                                                          |
| requests-cache (optional) | all                                                        |                                                                                                                                                                                                                                                      |
| rapidfuzz (optional)      | meta (command suggestions when an invalid command is used) | If this is not available then it tries to use thefuzz and if both are not installed it tries to use difflib                                                                                                                                          |
| packaging                 | wheels, information (optional)                             | In the information command If this is not available then it uses distutils which is buggy at times                                                                                                                                                   |
| wheel-filename            | wheels (optional)                                          | If the `--supported-only` flag is passed then this is required                                                                                                                                                                                       |

## Cache

The library caches packages and refreshes them per day. it also caches web requests and responses if `requests-cache` is installed

For the packages cache it makes it so that the data doesn't need to be re-downloaded in the `regex-search` command. The data is around 2.75 mb (gzipped) when it's gotten from the web, and when it's stored locally as cache it takes around 5 mb.

For the web requests cache it stores the recent few web requests so that if you are using the same command again it doesn't load the data again. This cache is automatically shortened by removing specific urls from the cache after they have expired depending on the url. Currently these are the cache expiry durations for commands

| Command       | Duration                                                    |
| ------------- | ----------------------------------------------------------- |
| browse        | 3 hours                                                     |
| description   | 3 hours if gotten from PyPI and 1 day if gotten from GitHub |
| information   | 3 hours                                                     |
| largest-files | 1 day                                                       |
| new-packages  | 1 minute                                                    |
| new-releases  | 1 minute                                                    |
| new-releases  | 3 hours                                                     |
| regex-search  | 1 day                                                       |
| releases      | 3 hours                                                     |
| rtfd          | No cache needed                                             |
| wheels        | 3 hours                                                     |
