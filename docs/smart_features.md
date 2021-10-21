---
layout: page
title: Smart Features
---

# The smartness of `pypi-command-line`

## Autocompletion

It supports command line argument autocompletion that can be used via pressing tab.
![Example of autocomplete](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/autocomplete%20example.gif)

## Smart aliases

You can write the first character(s) of the command and it will automatically get the command that starts with that character(s). Whenever it does this you'll get a message notifying you about that in case that was unexpected.

It always tries not to show a command not found message unless the input doesn't match with any command (50% match is required). It asks the user which command they tried to use if it finds multiple matching commands

![Example of the smart aliases](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/smart_alias.png)

If there are multiple commands that start with the specified character(s) then it shows a selection and asks the user to select a command.

![Example of smart aliases selection](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/autocomplete%20example%20with%20ambiguity.gif)

## Caching packages and requests

The package implements caching logic for faster load times

## Colored output everywhere

It shows colored output wherever it can. help command, errors, command outputs

## Smart and Inituitive error handling

![Example of smart and inituitive error handling](https://raw.githubusercontent.com/wasi-master/pypi-command-line/main/images/error%20handling.gif)

## Emojis

It shows emojis for responses that makes it more *✨beautiful✨*

## Command specific

### `wheels`

In the wheels command it colorizes the seperate parts of the wheels for easy understanding

![Example of this feature](https://i.imgur.com/noxWljq.png)

#### **Format**

The wheel filename is `{distribution}-{version}(-{build tag})?-{python tag}-{abi tag}-{platform tag}.whl`.

> <span style="color: #92EC5A;">distribution</span>

- Distribution name, e.g. 'django', 'pyramid'.

> <span style="color: #F2C259;">version</span>

- Distribution version, e.g. 1.0.

> <span style="color: #FFF075;">build tag (<b>Optional</b>)</span>

- build number. Must start with a digit. Acts as a tie-breaker if two wheel file names are the same in all other respects (i.e. name, version, and other tags). Sort as an empty tuple if unspecified, else sort as a two-item tuple with the first item being the initial digits as an `int`, and the second item being the remainder of the tag as a `str`.

> <span style="color: #FF6EF8;">language implementation and version tag</span>

- E.g. 'py27', 'py2', 'py3'.

> <span style="color: #9263FB;">abi tag</span>

- E.g. 'p33m', 'abi3', 'none'.

> <span style="color: #4AA0FC;">file extension</span>

- E.g. '.whl'.

For example, `distribution-1.0-1-py27-none-any.whl` is the first build of a package called 'distribution', and is compatible with Python 2.7 (any Python 2.7 implementation), with no ABI (pure Python), on any CPU architecture.

The last three components of the filename before the extension are called "compatibility tags." The compatibility tags express the package's basic interpreter requirements and are detailed in [PEP 425](https://www.python.org/dev/peps/pep-0425/).

\- Gotten from <https://www.python.org/dev/peps/pep-0427/#file-name-convention>
