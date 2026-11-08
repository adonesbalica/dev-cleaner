import os
import sys
from typing import TextIO

from src import __version__
from src.core.cleaner import Cleaner, CleanupReport

GREEN = "32"
RED = "31"
YELLOW = "33"
CYAN = "36"
DIM = "2"

LABEL_WIDTH = 12


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

    def confirm(self, targets: list[str]) -> bool:
        names = ", ".join(targets)

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

    def show_summary(self, report: CleanupReport, dry_run: bool = False) -> None:
        projects = plural(report.projects_scanned, "project")
        removed = len(report.removed)
        failed = len(report.failed)

        if dry_run:
            summary = f"{removed} matched ({projects}) [dry run]"
        elif failed:
            summary = f"{removed} removed, {failed} failed ({projects})"
        else:
            summary = f"{removed} removed ({projects})"

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

        report = cleaner.run()

        if not report.results:
            print("no matching directories", file=self.out)
            return 0

        self.show_results(report, dry_run=cleaner.dry_run)
        print(file=self.out)
        self.show_summary(report, dry_run=cleaner.dry_run)

        return 1 if report.failed else 0
