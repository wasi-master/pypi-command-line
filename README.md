# pypi-command-line

 A powerful command line interface for <https://pypi.org>

## Features

- 🚀 Extremely fast and easy to use.
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

## Installation

- Installing from PyPI (recommended).

  ```sh
  pip install pypi-command-line
  ```

- Installing from source.

  ```sh
  pip install git+https://github.com/wasi-master/pypi-command-line.git
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

For a full guide see the wiki.
