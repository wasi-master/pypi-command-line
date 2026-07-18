#!/usr/bin/env python3
"""Record asciicast v2 demos for every pypi-command-line command and flag.

Runs each command in a pseudo-terminal, captures the timed output, and writes
an asciinema-compatible ``.cast`` file to ``docs/assets/demos/``. A fake shell
prompt and per-character "typing" of the command is prepended so the casts look
like a real terminal session. No asciinema binary is required.

Usage::

    python3 scripts/record_demos.py            # record everything
    python3 scripts/record_demos.py wheels     # only demos whose name contains "wheels"
"""

from __future__ import annotations

import codecs
import fcntl
import json
import os
import pty
import re
import select
import shutil
import struct
import subprocess
import sys
import tempfile
import termios
import time
from typing import Any

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO_ROOT, "docs", "assets", "demos")

COLS = 100
ROWS = 30

# Seconds; gaps longer than this are compressed so viewers never stare at a
# frozen screen, and casts longer than MAX_BODY are time-scaled down.
IDLE_LIMIT = 2.0
MAX_BODY = 22.0

# The player has no scrollback, so the terminal must be tall enough to fit the
# whole demo. Output longer than MAX_LINES is cut (keeping the beginning) and
# replaced with a truncation notice; the player height is then sized to the
# content so nothing scrolls out of view.
MAX_LINES = 40
MIN_ROWS = 10

PROMPT = "\x1b[1;35m~\x1b[0m \x1b[1;32m❯\x1b[0m "
TRUNCATION_NOTICE = "\r\n\x1b[2m… output truncated, run the command yourself to see the rest …\x1b[0m\r\n"

# Sequences that move the cursor up (spinners, interactive menus) reclaim lines.
_CURSOR_UP_RE = re.compile(r"\x1b\[(\d*)[AF]")


def _net_lines(text: str) -> int:
    """Net number of terminal lines this chunk advances the cursor by."""
    ups = sum(int(match.group(1) or 1) for match in _CURSOR_UP_RE.finditer(text))
    return text.count("\n") - ups


def fit_events(events: list[tuple[float, str]]) -> tuple[list[tuple[float, str]], int]:
    """Truncate *events* to MAX_LINES of output and return (events, rows).

    Keeps the beginning of the output and appends a truncation notice plus a
    fresh prompt when content is cut, so the player always shows the start of
    the output with nothing scrolled away.
    """
    # The recorder runs the CLI as `python -m pypi_cli`, but the demos should
    # read as the installed `pypi` command (shows up in --help usage lines).
    events = [(ts, data.replace("python -m pypi_cli", "pypi")) for ts, data in events]

    # Already-truncated casts (e.g. when re-processing) must not be cut again.
    if any(TRUNCATION_NOTICE in data for _, data in events):
        total = 1 + sum(_net_lines(data) for _, data in events)
        return events, max(MIN_ROWS, min(total + 1, MAX_LINES + 5))

    fitted: list[tuple[float, str]] = []
    lines = 1  # the prompt line itself
    for ts, data in events:
        advance = _net_lines(data)
        if lines + advance <= MAX_LINES:
            lines += advance
            fitted.append((ts, data))
            continue
        # Cut inside this chunk, on a newline boundary.
        kept: list[str] = []
        for piece in data.splitlines(keepends=True):
            piece_advance = _net_lines(piece)
            if lines + piece_advance > MAX_LINES:
                break
            lines += piece_advance
            kept.append(piece)
        if kept:
            fitted.append((ts, "".join(kept)))
        fitted.append((ts + 0.2, TRUNCATION_NOTICE))
        fitted.append((ts + 0.7, f"\r\n{PROMPT}"))
        lines += 4
        break
    rows = max(MIN_ROWS, min(lines + 1, MAX_LINES + 5))
    return fitted, rows


def typing_delays(text: str) -> list[float]:
    """Deterministic, human-ish typing delays (no randomness for reproducibility)."""
    delays = []
    for i, char in enumerate(text):
        base = 0.035 + (hash((char, i)) % 40) / 1000.0
        if char == " ":
            base += 0.04
        delays.append(base)
    return delays


def record(
    display: str,
    argv: list[str],
    out_name: str,
    *,
    cwd: str | None = None,
    env_extra: dict[str, str] | None = None,
    inputs: list[tuple[float, bytes]] | None = None,
    timeout: float = 180.0,
    max_body: float = MAX_BODY,
    redact: list[tuple[str, str]] | None = None,
) -> None:
    """Run *argv* in a pty and write an asciicast file named *out_name*."""
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", ROWS, COLS, 0, 0))

    env = os.environ.copy()
    env.update(
        {
            "TERM": "xterm-256color",
            "COLUMNS": str(COLS),
            "LINES": str(ROWS),
            "FORCE_COLOR": "1",
            "PYTHONUNBUFFERED": "1",
            # The recording pty never answers cursor-position queries, which
            # would make prompt_toolkit (questionary) print a CPR warning.
            "PROMPT_TOOLKIT_NO_CPR": "1",
        }
    )
    if env_extra:
        env.update(env_extra)

    proc = subprocess.Popen(argv, stdin=slave, stdout=slave, stderr=slave, env=env, cwd=cwd, close_fds=True)
    os.close(slave)

    events: list[tuple[float, str]] = []
    decoder = codecs.getincrementaldecoder("utf-8")("replace")
    pending = sorted(inputs or [])
    start = time.monotonic()
    eof = False
    while not eof:
        now = time.monotonic() - start
        if now > timeout:
            proc.kill()
            break
        while pending and pending[0][0] <= now:
            _, keys = pending.pop(0)
            try:
                os.write(master, keys)
            except OSError:
                pending.clear()
        readable, _, _ = select.select([master], [], [], 0.05)
        if readable:
            try:
                data = os.read(master, 65536)
            except OSError:
                break
            if not data:
                break
            text = decoder.decode(data)
            if text:
                events.append((time.monotonic() - start, text))
        elif proc.poll() is not None and not pending:
            # Drain whatever is left in the pty buffer, then stop.
            while True:
                readable, _, _ = select.select([master], [], [], 0.1)
                if not readable:
                    eof = True
                    break
                try:
                    data = os.read(master, 65536)
                except OSError:
                    eof = True
                    break
                if not data:
                    eof = True
                    break
                text = decoder.decode(data)
                if text:
                    events.append((time.monotonic() - start, text))
    os.close(master)
    proc.wait()

    # Hide recording internals (e.g. the throwaway $HOME) from the output.
    for old, new in redact or []:
        events = [(ts, data.replace(old, new)) for ts, data in events]

    # Compress long idle gaps.
    compressed: list[tuple[float, str]] = []
    clock = 0.0
    prev = 0.0
    for ts, data in events:
        gap = min(ts - prev, IDLE_LIMIT)
        clock += gap
        prev = ts
        compressed.append((clock, data))

    # Scale down casts that are still too long (e.g. cache refresh downloads).
    if compressed and compressed[-1][0] > max_body:
        factor = max_body / compressed[-1][0]
        compressed = [(ts * factor, data) for ts, data in compressed]

    # Prologue: prompt + typed command.
    out_events: list[tuple[float, str]] = []
    clock = 0.4
    out_events.append((clock, PROMPT))
    clock += 0.3
    for char, delay in zip(display, typing_delays(display)):
        clock += delay
        out_events.append((clock, char))
    clock += 0.35
    out_events.append((clock, "\r\n"))
    body_start = clock + 0.05
    for ts, data in compressed:
        out_events.append((body_start + ts, data))
    end = out_events[-1][0] if out_events else body_start
    out_events.append((end + 0.5, f"\r\n{PROMPT}"))
    out_events, cast_rows = fit_events(out_events)

    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, out_name + ".cast")
    header: dict[str, Any] = {
        "version": 2,
        "width": COLS,
        "height": cast_rows,
        "title": display,
        "env": {"TERM": "xterm-256color", "SHELL": "/bin/zsh"},
    }
    with open(path, "w", encoding="utf-8") as file:
        file.write(json.dumps(header) + "\n")
        for ts, data in out_events:
            file.write(json.dumps([round(ts, 4), "o", data]) + "\n")
    duration = out_events[-1][0]
    print(f"  wrote {os.path.relpath(path, REPO_ROOT)} ({duration:.1f}s, exit {proc.returncode})")


_LAUNCHER = os.path.join(tempfile.mkdtemp(prefix="pypi-demo-bin-"), "pypi")
with open(_LAUNCHER, "w", encoding="utf-8") as _file:
    # argv[0] is what click uses as the program name in help/usage output, so
    # run through a script named `pypi` instead of `python -m pypi_cli`.
    _file.write("from pypi_cli.__main__ import run\n\nrun()\n")


def pypi_argv(*args: str) -> list[str]:
    """Run the CLI from the repo checkout so demos always reflect current code."""
    return [sys.executable, _LAUNCHER, *args]


def build_demos() -> list[dict[str, Any]]:
    """Return the full list of demos to record."""
    fake_home = tempfile.mkdtemp(prefix="pypi-demo-home-")
    check_dir = tempfile.mkdtemp(prefix="pypi-demo-check-")

    # Shell detection (shellingham) walks the process tree, which is unreliable
    # in sandboxed/CI environments, so the completion demos get a stub module
    # that always reports zsh. The demo output is identical to a real zsh setup.
    shim_dir = tempfile.mkdtemp(prefix="pypi-demo-shim-")
    os.makedirs(os.path.join(shim_dir, "shellingham"), exist_ok=True)
    with open(os.path.join(shim_dir, "shellingham", "__init__.py"), "w", encoding="utf-8") as file:
        file.write(
            "class ShellDetectionFailure(Exception):\n"
            "    pass\n\n\n"
            "def detect_shell(pid=None):\n"
            '    return ("zsh", "/bin/zsh")\n'
        )
    shim_path = os.pathsep.join([shim_dir, REPO_ROOT])
    with open(os.path.join(check_dir, "requirements.txt"), "w", encoding="utf-8") as file:
        file.write("rich>=10.0\nrequests==2.25.0\ntyper\nWasi-Master-does-not-exist\n")

    demos: list[dict[str, Any]] = [
        # ── Global options ──────────────────────────────────────────────
        {"name": "pypi-help", "display": "pypi --help", "args": ["--help"]},
        {"name": "pypi-command-help", "display": "pypi info --help", "args": ["info", "--help"]},
        {
            "name": "pypi-install-completion",
            "display": "pypi --install-completion",
            "args": ["--install-completion"],
            "env": {"HOME": fake_home, "SHELL": "/bin/zsh", "ZDOTDIR": fake_home, "PYTHONPATH": shim_path},
            "redact": [(fake_home, "~")],
        },
        {
            "name": "pypi-show-completion",
            "display": "pypi --show-completion",
            "args": ["--show-completion"],
            "env": {"SHELL": "/bin/zsh", "PYTHONPATH": shim_path},
        },
        {"name": "pypi-no-cache", "display": "pypi --no-cache information rich", "args": ["--no-cache", "information", "rich"]},
        {
            "name": "pypi-repository",
            "display": "pypi --repository testpypi releases pip",
            "args": ["--repository", "testpypi", "releases", "pip"],
        },
        {"name": "pypi-timeout", "display": "pypi --timeout 5 information requests", "args": ["--timeout", "5", "information", "requests"]},
        {"name": "pypi-verbose", "display": "pypi --verbose version pypi-command-line", "args": ["--verbose", "version", "pypi-command-line"]},
        # ── version ─────────────────────────────────────────────────────
        {"name": "pypi-version", "display": "pypi version", "args": ["version"]},
        {
            "name": "pypi-version-package",
            "display": "pypi version django --limit 5 --show-installed-version",
            "args": ["version", "django", "--limit", "5", "--show-installed-version"],
        },
        {
            "name": "pypi-version-no-pre-releases",
            "display": "pypi version numpy --no-pre-releases",
            "args": ["version", "numpy", "--no-pre-releases"],
        },
        # ── browse ──────────────────────────────────────────────────────
        {
            "name": "pypi-browse",
            "display": "pypi browse rich",
            "args": ["browse", "rich"],
            "inputs": [(10.0, b"\x1b[B"), (11.0, b"\x1b[B"), (12.0, b"\x1b[A"), (14.0, b"\x03")],
            "env": {"BROWSER": "/usr/bin/true"},
        },
        {"name": "pypi-browse-url-only", "display": "pypi browse rich --url-only", "args": ["browse", "rich", "--url-only"]},
        # ── description ─────────────────────────────────────────────────
        {"name": "pypi-description", "display": "pypi description rich", "args": ["description", "rich"]},
        {
            "name": "pypi-description-force-github",
            "display": "pypi description flask --force-github",
            "args": ["description", "flask", "--force-github"],
        },
        {
            "name": "pypi-description-syntax-theme",
            "display": "pypi description rich --syntax-theme dracula",
            "args": ["description", "rich", "--syntax-theme", "dracula"],
        },
        # ── dependencies ────────────────────────────────────────────────
        {"name": "pypi-dependencies", "display": "pypi dependencies requests", "args": ["dependencies", "requests"]},
        {
            "name": "pypi-dependencies-level",
            "display": 'pypi dependencies "requests[socks]" --level 2',
            "args": ["dependencies", "requests[socks]", "--level", "2"],
        },
        # ── information ─────────────────────────────────────────────────
        {"name": "pypi-information", "display": "pypi information rich", "args": ["information", "rich"]},
        {
            "name": "pypi-information-classifiers",
            "display": "pypi information rich --show-classifiers",
            "args": ["information", "rich", "--show-classifiers"],
        },
        {
            "name": "pypi-information-hide",
            "display": "pypi information rich --hide-github --hide-stats --hide-meta --hide-project-urls --hide-requirements",
            "args": [
                "information",
                "rich",
                "--hide-github",
                "--hide-stats",
                "--hide-meta",
                "--hide-project-urls",
                "--hide-requirements",
            ],
        },
        {"name": "pypi-information-json", "display": "pypi information rich --json", "args": ["information", "rich", "--json"]},
        # ── check ───────────────────────────────────────────────────────
        {
            "name": "pypi-check",
            "display": "pypi check requirements.txt",
            "args": ["check", "requirements.txt"],
            "cwd": check_dir,
        },
        {
            "name": "pypi-check-json",
            "display": "pypi check requirements.txt --json",
            "args": ["check", "requirements.txt", "--json"],
            "cwd": check_dir,
        },
        # ── compare ─────────────────────────────────────────────────────
        {"name": "pypi-compare", "display": "pypi compare requests httpx aiohttp", "args": ["compare", "requests", "httpx", "aiohttp"]},
        {
            "name": "pypi-compare-json",
            "display": "pypi compare requests httpx --json",
            "args": ["compare", "requests", "httpx", "--json"],
        },
        # ── largest-files ───────────────────────────────────────────────
        {"name": "pypi-largest-files", "display": "pypi largest-files", "args": ["largest-files"]},
        # ── new-packages / new-releases ─────────────────────────────────
        {"name": "pypi-new-packages", "display": "pypi new-packages", "args": ["new-packages"]},
        {
            "name": "pypi-new-packages-flags",
            "display": "pypi new-packages --show-author --hide-link",
            "args": ["new-packages", "--show-author", "--hide-link"],
        },
        {"name": "pypi-new-releases", "display": "pypi new-releases", "args": ["new-releases"]},
        {
            "name": "pypi-new-releases-flags",
            "display": "pypi new-releases --show-author --hide-link",
            "args": ["new-releases", "--show-author", "--hide-link"],
        },
        # ── releases ────────────────────────────────────────────────────
        {"name": "pypi-releases", "display": "pypi releases pypi-command-line", "args": ["releases", "pypi-command-line"]},
        {
            "name": "pypi-releases-version",
            "display": "pypi releases rich --version 13.7.1",
            "args": ["releases", "rich", "--version", "13.7.1"],
        },
        {
            "name": "pypi-releases-links",
            "display": "pypi releases pypi-command-line --show-links",
            "args": ["releases", "pypi-command-line", "--show-links"],
        },
        {
            "name": "pypi-releases-json",
            "display": "pypi releases pypi-command-line --json",
            "args": ["releases", "pypi-command-line", "--json"],
        },
        # ── read-the-docs ───────────────────────────────────────────────
        {"name": "pypi-read-the-docs", "display": "pypi read-the-docs numpy", "args": ["read-the-docs", "numpy"]},
        {
            "name": "pypi-read-the-docs-query",
            "display": "pypi read-the-docs numpy ndarray",
            "args": ["read-the-docs", "numpy", "ndarray"],
        },
        # ── search (disabled upstream) ──────────────────────────────────
        {"name": "pypi-search", "display": "pypi search rich", "args": ["search", "rich"]},
        # ── vulnerabilities ─────────────────────────────────────────────
        {"name": "pypi-vulnerabilities", "display": "pypi vulnerabilities django==3.2", "args": ["vulnerabilities", "django==3.2"]},
        # ── wheels ──────────────────────────────────────────────────────
        {"name": "pypi-wheels", "display": "pypi wheels numpy", "args": ["wheels", "numpy"]},
        {
            "name": "pypi-wheels-supported-only",
            "display": "pypi wheels numpy --supported-only",
            "args": ["wheels", "numpy", "--supported-only"],
        },
        # ── regex-search (needs the packages cache) ─────────────────────
        {
            "name": "pypi-regex-search",
            "display": 'pypi regex-search "^flask-admin.*"',
            "args": ["regex-search", "^flask-admin.*"],
        },
        {
            "name": "pypi-regex-search-compact",
            "display": 'pypi regex-search "^django-rest.*" --compact --limit 20',
            "args": ["regex-search", "^django-rest.*", "--compact", "--limit", "20"],
        },
        # ── smart features ──────────────────────────────────────────────
        {"name": "pypi-smart-alias", "display": "pypi lar", "args": ["lar"]},
        {
            "name": "pypi-smart-alias-ambiguous",
            "display": "pypi ca",
            "args": ["ca"],
            "inputs": [(3.0, b"\x1b[B"), (4.0, b"\r")],
        },
        {
            "name": "pypi-smart-error-handling",
            "display": "pypi informatoin rich",
            "args": ["informatoin", "rich"],
            "inputs": [(3.0, b"\r")],
        },
        # ── cache commands (refresh before info, clear last) ────────────
        {"name": "pypi-cache-refresh", "display": "pypi cache-refresh", "args": ["cache-refresh"], "timeout": 600},
        {"name": "pypi-cache-information", "display": "pypi cache-info", "args": ["cache-info"]},
        {"name": "pypi-cache-clear", "display": "pypi cache-clear", "args": ["cache-clear"]},
    ]
    return demos


def reprocess() -> None:
    """Re-apply truncation and height sizing to the already-recorded casts."""
    for name in sorted(os.listdir(OUT_DIR)):
        if not name.endswith(".cast"):
            continue
        path = os.path.join(OUT_DIR, name)
        with open(path, encoding="utf-8") as file:
            header = json.loads(file.readline())
            events = [(e[0], e[2]) for line in file if (e := json.loads(line))[1] == "o"]
        events, rows = fit_events(events)
        header["height"] = rows
        with open(path, "w", encoding="utf-8") as file:
            file.write(json.dumps(header) + "\n")
            for ts, data in events:
                file.write(json.dumps([round(ts, 4), "o", data]) + "\n")
        print(f"  {name}: height {rows}")


def main() -> None:
    if "--reprocess" in sys.argv[1:]:
        reprocess()
        return
    filters = [arg.lower() for arg in sys.argv[1:]]
    demos = build_demos()
    if filters:
        demos = [demo for demo in demos if any(f in demo["name"] for f in filters)]
    if not demos:
        print("No demos matched the given filter(s).")
        raise SystemExit(1)

    print(f"Recording {len(demos)} demos to {os.path.relpath(OUT_DIR, os.getcwd())}")
    failures: list[str] = []
    for demo in demos:
        print(f"* {demo['display']}")
        env = {"PYTHONPATH": REPO_ROOT}
        env.update(demo.get("env", {}))
        try:
            record(
                demo["display"],
                demo.get("argv_override") or pypi_argv(*demo["args"]),
                demo["name"],
                cwd=demo.get("cwd", REPO_ROOT),
                env_extra=env,
                inputs=demo.get("inputs"),
                timeout=demo.get("timeout", 180.0),
                redact=demo.get("redact"),
            )
        except Exception as exc:  # noqa: BLE001 - keep recording the rest
            failures.append(demo["name"])
            print(f"  FAILED: {exc}")
    if failures:
        print(f"\n{len(failures)} demo(s) failed: {', '.join(failures)}")
        raise SystemExit(1)
    print("\nAll demos recorded.")


if __name__ == "__main__":
    main()
