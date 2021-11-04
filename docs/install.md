---
layout: page
title: Installation instructions for pypi-command-line
description: pypi-command-line is a powerful, colorful, beautiful command line interface for pypi.org that is well maintained
---

# Installation

## Installation Options

### I want it to be simple and easy

If you want to keep it as simple as possible you can just do

=== "From PyPI"

    ```shell
    pip install pypi-command-line
    ```

=== "From GitHub"

    ```shell
    pip install git+https://github.com/wasi-master/pypi-command-line.git
    ```

### I want it to be fast

If you want to make it fast then you can do

=== "From PyPI"

    ```shell
    pip install "pypi-command-line[speedups]"
    ```

=== "From GitHub"

    ```shell
    pip install "pypi-command-line[speedups] @ git+https://github.com/wasi-master/pypi-command-line.git"
    ```

For an explanation on how this speeds up things see [notes](https://wasi-master.github.io/pypi-command-line/notes#speedups)

### I will not use some commands

If you only want to install dependencies for the commands you use then you can see [notes](https://wasi-master.github.io/pypi-command-line/notes#dependency-installation-notes) and only install the dependencies you want:

First you need to install it without any dependencies.

=== "From PyPI"

    ```shell
    pip install --no-dependencies pypi-command-line
    ```

=== "From GitHub"

    ```shell
    pip install --no-dependencies git+https://github.com/wasi-master/pypi-command-line.git
    ```


Then you need to install the required dependencies for any of the commands to work.

```shell
pip install rich, typer, requests, humanize
```

Then install any of the extra dependencies you want according to the commands you need or the [speed dependencies](https://wasi-master.github.io/pypi-command-line/notes#speedups).

For example if you only want the information command then you can just install packaging since it only requires that

```shell
pip install packaging
```

### I don't have pip

If for some reason you don't have pip then you should get pip. See instructions at <https://pip.pypa.io/en/stable/installation/> then install it with the ways shown above

Or if you have [git](https://git-scm.com) installed then you can clone then install as shown below

### I want to clone then install

You can also clone the repo with git and then install it using the setup.py file

```shell
git clone https://github.com/wasi-master/pypi-command-line.git
cd pypi-command-line
python setup.py install
```

!!! note
    You'll need [git](https://git-scm.com) in order to do this

## Troubleshooting

### Command `pip` not found

!!! failure "Error Messages"

    **Powershell**

    ```powershell
    pip : The term 'pip' is not recognized as the name of a cmdlet, function, script file, or operable program. Check the spelling of the name, or if a path was
    included, verify that the path is correct and try again.
    At line:1 char:1
    + pip install pypi-command-line
    + ~~~
        + CategoryInfo          : ObjectNotFound: (pip:String) [], CommandNotFoundException
        + FullyQualifiedErrorId : CommandNotFoundException
    ```

    or

    ```powershell
    pip: The term 'pip' is not recognized as a name of a cmdlet, function, script file, or executable program.
    Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
    ```

    **Command Prompt**

    ```shell
    'pip' is not recognized as an internal or external command,
    operable program or batch file.
    ```

    **Bash**

    ```bash
    pip: command not found
    ```

    **Zsh**

    ```zsh
    zsh: command not found: pip
    ```

If you get this error you should change `#!sh pip` to `#!sh python -m pip` and if it still doesn't work you should install `#!sh pip` again. See instructions at <https://pip.pypa.io/en/stable/installation/>

!!! danger "Note"
    if `#!sh python` also doesn't work try `#!sh python3` or `#!sh py`. If nothing works make sure you have installed python correctly and it's in path
