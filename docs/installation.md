# Installation

- [Installation](#installation)
  - [Installation Options](#installation-options)
    - [I want it to be simple and easy](#i-want-it-to-be-simple-and-easy)
    - [I want it to be fast](#i-want-it-to-be-fast)
    - [I will not use some commands](#i-will-not-use-some-commands)
    - [I don't have pip](#i-dont-have-pip)
    - [I want to clone then install](#i-want-to-clone-then-install)
  - [Troubleshooting](#troubleshooting)
    - [Command `pip` not found](#command-pip-not-found)

## Installation Options

### I want it to be simple and easy

If you want to keep it as simple as possible you can just do

```cmd
pip install pypi-command-line
```

### I want it to be fast

If you want to make it fast then you can do

```cmd
pip install pypi-command-line[speedups]
```

For an explanation on how this speeds up things see [notes](https://wasi-master.github.io/pypi-command-line/notes#speedups)

### I will not use some commands

If you only want to install dependencies for the commands you use then you can see [notes](https://wasi-master.github.io/pypi-command-line/notes#dependency-installation-notes) and only install the dependencies you want:

First you need to install it without any dependencies.

```cmd
pip install --no-dependencies pypi-command-line
```

Then you need to install the required dependencies for any of the commands to work.

```cmd
pip install rich, typer, requests, humanize
```

Then install any of the extra dependencies you want according to the commands you need or the [speed dependencies](https://wasi-master.github.io/pypi-command-line/notes#speedups).

For example if you only want the information command then you can just install packaging since it only requires that

```cmd
pip install packaging
```

> Note: `packaging` comes pre-installed with setuptools which comes pre-installed with `pip` so if you have pip then you most likely have packaging too

### I don't have pip

If for some reason you don't have pip then you should get pip. See instructions at <https://pip.pypa.io/en/stable/installation/> then do it the ways showed above

### I want to clone then install

You can also clone the repo with git and then install it using the setup.py file

```cmd
git clone https://github.com/wasi-master/pypi-command-line.git
cd pypi-command-line
python setup.py install
```

> Note: You'll need [git](https://git-scm.com) in order to do this

## Troubleshooting

### Command `pip` not found

<details open>
<summary><b>Error Messages</b></summary>

Powershell

```powershell
pip : The term 'pip' is not recognized as the name of a cmdlet, function, script file, or operable program. Check the spelling of the name, or if a path was
included, verify that the path is correct and try again.
At line:1 char:1
+ pip install pypi-command-line
+ ~~~
    + CategoryInfo          : ObjectNotFound: (pip:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
```

Command Prompt

```cmd
'pip' is not recognized as an internal or external command,
operable program or batch file.
```

Bash

```bash
pip: command not found
```

Zsh

```zsh
zsh: command not found: pip
```

</details>

If you get this error you should change `pip` to `python -m pip` and if it still doesn't work you should install `pip` again See instructions at <https://pip.pypa.io/en/stable/installation/>
