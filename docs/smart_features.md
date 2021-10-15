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

<!-- TODO: add command specific smart features -->
