import os
import sys
import textwrap
import threading
import time
from typing import TextIO

from dev_cleaner import __version__
from dev_cleaner.core.catalog import DEFAULT_TARGETS, PRESETS
from dev_cleaner.core.cleaner import Cleaner, CleanupReport

GREEN = "32"
RED = "31"
YELLOW = "33"
CYAN = "36"
DIM = "2"

LABEL_WIDTH = 12
SPINNER_FRAMES = "|/-\\"
SPINNER_INTERVAL = 0.1
SPINNER_DELAY = 0.2
STATUS_PROJECT_WIDTH = 20


def _enable_windows_ansi(stream: TextIO) -> None:
    if os.name != "nt":
        return

    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle_id = -12 if stream is sys.stderr else -11
        handle = kernel32.GetStdHandle(handle_id)
        mode = ctypes.c_uint32()

        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


def supports_color(stream: TextIO) -> bool:
    if os.environ.get("NO_COLOR"):
        return False

    if os.environ.get("TERM") == "dumb":
        return False

    if not (hasattr(stream, "isatty") and stream.isatty()):
        return False

    _enable_windows_ansi(stream)

    return True


def backend_label(backend: str, distribution: str | None) -> str:
    if backend == "wsl":
        return f"wsl:{distribution}"

    return "native"


def plural(count: int, word: str) -> str:
    suffix = "" if count == 1 else "s"

    return f"{count} {word}{suffix}"


def supports_animation(stream: TextIO) -> bool:
    if os.environ.get("TERM") == "dumb":
        return False

    return hasattr(stream, "isatty") and stream.isatty()


def format_elapsed(seconds: float) -> str:
    total = int(seconds)
    minutes, secs = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)

    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"

    return f"{minutes}:{secs:02d}"


def shorten(text: str, width: int = STATUS_PROJECT_WIDTH) -> str:
    if len(text) <= width:
        return text

    return text[: width - 3] + "..."


def summarize_targets(targets: list[str], limit: int = 6) -> str:
    if len(targets) <= limit:
        return ", ".join(targets)

    remaining = len(targets) - limit

    return f"{', '.join(targets[:limit])} and {remaining} more"


class Spinner:
    """Single-line spinner with an elapsed timer, rendered only on a TTY."""

    def __init__(self, stream: TextIO, enabled: bool):
        self.stream = stream
        self.enabled = enabled
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._status = ""
        self._start = 0.0
        self._width = 0

    def __enter__(self) -> "Spinner":
        self._start = time.monotonic()

        if self.enabled:
            self._thread = threading.Thread(target=self._spin, daemon=True)
            self._thread.start()

        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self._stop.set()

        if self._thread is not None:
            self._thread.join()

        if self._width:
            self.stream.write("\r" + " " * self._width + "\r")
            self.stream.flush()

    def update(self, status: str) -> None:
        self._status = status

    def _spin(self) -> None:
        index = 0

        while not self._stop.wait(SPINNER_INTERVAL):
            if time.monotonic() - self._start < SPINNER_DELAY:
                continue

            elapsed = format_elapsed(time.monotonic() - self._start)
            frame = SPINNER_FRAMES[index % len(SPINNER_FRAMES)]
            line = f"{frame} {self._status} {elapsed}"

            self._width = max(self._width, len(line))
            self.stream.write("\r" + line.ljust(self._width))
            self.stream.flush()
            index += 1


class CLI:
    def __init__(self, out: TextIO | None = None, err: TextIO | None = None):
        self.out = out if out is not None else sys.stdout
        self.err = err if err is not None else sys.stderr
        self.out_color = supports_color(self.out)
        self.err_color = supports_color(self.err)

    def style(self, text: str, code: str, *, err: bool = False) -> str:
        enabled = self.err_color if err else self.out_color

        if not enabled:
            return text

        return f"\033[{code}m{text}\033[0m"

    def show_header(
        self,
        workspace: str,
        backend: str,
        distribution: str | None,
    ) -> None:
        version = self.style(f"dev-cleaner {__version__}", DIM)
        label = backend_label(backend, distribution)

        print(f"{version} | {label} | {workspace}", file=self.out)

    def show_presets(self) -> None:
        width = max(len(name) for name in PRESETS)
        indent = " " * (width + 4)

        print("presets:", file=self.out)

        for name in sorted(PRESETS):
            lines = textwrap.wrap(
                ", ".join(PRESETS[name]),
                width=88 - len(indent),
                break_on_hyphens=False,
            )
            print(f"  {name:<{width}}  {lines[0]}", file=self.out)

            for line in lines[1:]:
                print(f"{indent}{line}", file=self.out)

        print(file=self.out)
        print(f"defaults: {', '.join(DEFAULT_TARGETS)}", file=self.out)

    def confirm(self, targets: list[str]) -> bool:
        names = summarize_targets(targets)

        self.out.write(f"Remove {names} from every project? [y/N] ")
        self.out.flush()

        try:
            answer = sys.stdin.readline()
        except KeyboardInterrupt:
            self.out.write("\n")
            return False

        if not answer:
            self.out.write("\n")
            return False

        return answer.strip().lower() in {"y", "yes"}

    def show_results(self, report: CleanupReport, dry_run: bool = False) -> None:
        for result in report.results:
            path = f"{result.project}/{result.target}"

            if not result.success:
                label = self.style(f"{'failed':<{LABEL_WIDTH}}", RED, err=True)
                print(f"{label} {path}  {result.error}", file=self.err)
                continue

            if dry_run:
                label = self.style(f"{'would remove':<{LABEL_WIDTH}}", CYAN)
            else:
                label = self.style(f"{'removed':<{LABEL_WIDTH}}", GREEN)

            print(f"{label} {path}", file=self.out)

    def show_summary(
        self,
        report: CleanupReport,
        dry_run: bool = False,
        elapsed: float | None = None,
    ) -> None:
        projects = plural(report.projects_scanned, "project")
        removed = len(report.removed)
        failed = len(report.failed)

        if dry_run:
            summary = f"{removed} matched ({projects}) [dry run]"
        elif failed:
            summary = f"{removed} removed, {failed} failed ({projects})"
        else:
            summary = f"{removed} removed ({projects})"

        if elapsed is not None and not dry_run and elapsed >= 1.0:
            summary += f" in {format_elapsed(elapsed)}"

        code = YELLOW if failed else GREEN

        print(self.style(summary, code), file=self.out)

    def run(
        self,
        cleaner: Cleaner,
        workspace: str,
        backend: str,
        distribution: str | None = None,
        assume_yes: bool = False,
    ) -> int:
        self.show_header(workspace, backend, distribution)
        print(file=self.out)

        if not cleaner.dry_run and not assume_yes:
            if not self.confirm(cleaner.target_folders):
                print(self.style("cancelled", YELLOW), file=self.out)
                return 0

            print(file=self.out)

        action = "scanning" if cleaner.dry_run else "cleaning"
        start = time.monotonic()

        with Spinner(
            self.out,
            enabled=supports_animation(self.out),
        ) as spinner:
            spinner.update(f"{action}...")

            def on_target(current: int, total: int, project, target: str) -> None:
                name = f"{shorten(project.name)}/{target}"
                spinner.update(f"{action} {name} ({current}/{total})")

            report = cleaner.run(on_target=on_target)

        elapsed = time.monotonic() - start

        if not report.results:
            print("no matching directories", file=self.out)
            return 0

        self.show_results(report, dry_run=cleaner.dry_run)
        print(file=self.out)
        self.show_summary(report, dry_run=cleaner.dry_run, elapsed=elapsed)

        return 1 if report.failed else 0
