---
name: Bug report
about: Create a report to help us improve
title: "[BUG] ..."
labels: bug
assignees: 'wasi-master'

---

## Describe the bug
A clear and concise description of what the bug is.

## To Reproduce
Steps to reproduce the behavior:

1. Use the command `...`
2. See `...`

## Expected behavior
A clear and concise description of what you expected to happen.

## Screenshots
_If applicable_, add screenshots to help explain your problem.

## Information (please try to complete the following information):

- **OS**             : [e.g. Windows 10, MacOS, Linux (Ubuntu)]
- **Terminal**       : [e.g.GNOME Terminal, Windows Terminal, Command Prompt]
- **Shell**          : [e.g. powershell, bash, zsh, fish]
- **OS Version**     : [e.g. 21H2 (OS Build 19044.1788)] 
- **Python Version** : [e.g. 3.10.0]  (Run `python --version`)
- **Package Versions**       :-

  Run the following command and put the output here
  - Linux/MacOS
  ```bash
  pip freeze | grep -E "bs4|click|humanize|packaging|questionary|requests|rich|rich-rst|thefuzz|typer|wheel-filename|lxml|rapidfuzz|requests-cache|shellingham"
  ```
  - Windows
  ```cmd
  pip freeze | findstr "bs4 click humanize packaging questionary requests rich rich-rst thefuzz typer wheel-filename lxml rapidfuzz requests-cache shellingham"
  ```


## Additional context
Add any other context about the problem here if applicable.
