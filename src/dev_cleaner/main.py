import os
import subprocess
import sys
from pathlib import Path, PurePosixPath

from dev_cleaner.cleaners.base import FileSystemCleaner
from dev_cleaner.cleaners.native import NativeCleaner
from dev_cleaner.cleaners.wsl import WslCleaner
from dev_cleaner.cli.interface import CLI
from dev_cleaner.cli.parser import create_parser
from dev_cleaner.core.catalog import resolve_targets
from dev_cleaner.core.cleaner import Cleaner

DEFAULT_DISTRIBUTION = "Ubuntu"
WSL_UNC_HOST = "wsl.localhost"
WSL_UNC_HOSTS = {WSL_UNC_HOST, "wsl$"}


def is_wsl_unc_path(workspace: str) -> bool:
    parts = PurePosixPath(workspace.replace("\\", "/")).parts

    return len(parts) >= 3 and parts[0] == "//" and parts[1].lower() in WSL_UNC_HOSTS


def split_wsl_unc_path(workspace: str) -> tuple[str, PurePosixPath] | None:
    if not is_wsl_unc_path(workspace):
        return None

    parts = PurePosixPath(workspace.replace("\\", "/")).parts

    if len(parts) < 4:
        raise ValueError(
            "Workspace must point to a directory inside the WSL distribution, "
            "not to the distribution root."
        )

    distribution = parts[2]
    linux_path = PurePosixPath("/", *parts[3:])

    return distribution, linux_path


def detect_backend(workspace: str) -> str:
    """Pick a backend from the shape of the workspace path.

    WSL is only considered when running on Windows, because Linux already
    sees WSL paths natively and has no ``wsl`` command to delegate to.
    """

    if os.name != "nt":
        return "native"

    if is_wsl_unc_path(workspace):
        return "wsl"

    # A POSIX path such as /home/user/workspace is not a valid Windows path,
    # so it must refer to a filesystem inside WSL.
    if PurePosixPath(workspace).is_absolute() and not Path(workspace).is_absolute():
        return "wsl"

    return "native"


def decode_wsl_output(data: bytes) -> str:
    # wsl.exe writes UTF-16LE to pipes, which looks like ASCII with NUL bytes.
    if b"\x00" in data:
        text = data.decode("utf-16-le", errors="replace")
    else:
        text = data.decode("utf-8", errors="replace")

    return text.replace("\ufeff", "").replace("\x00", "")


def detect_default_distribution() -> str | None:
    """Return the default WSL distribution, or None when WSL is unavailable."""

    try:
        result = subprocess.run(
            ["wsl", "-l", "-q"],
            capture_output=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    if result.returncode != 0:
        return None

    for line in decode_wsl_output(result.stdout).splitlines():
        name = line.strip()

        if name:
            return name

    return None


def create_cleaner(backend: str, distribution: str) -> FileSystemCleaner:
    if backend == "native":
        return NativeCleaner()

    return WslCleaner(distribution)


def resolve_workspace(
    workspace: str,
    backend: str,
    distribution: str | None,
) -> tuple[Path, str | None, str]:
    """Return the path to scan, the Linux path for WSL, and the distribution."""

    if backend == "native":
        return (
            Path(workspace).expanduser(),
            None,
            distribution or DEFAULT_DISTRIBUTION,
        )

    unc = split_wsl_unc_path(workspace)

    if unc is not None:
        unc_distribution, linux_path = unc
        distribution = distribution or unc_distribution
    else:
        linux_path = PurePosixPath(workspace)

    if not linux_path.is_absolute():
        raise ValueError(
            "WSL workspace must be an absolute Linux path, "
            "for example /home/user/workspace."
        )

    if ".." in linux_path.parts:
        raise ValueError("WSL workspace cannot contain '..'.")

    distribution = distribution or detect_default_distribution() or DEFAULT_DISTRIBUTION

    scan_path = Path(f"//{WSL_UNC_HOST}/{distribution}{linux_path.as_posix()}")

    return scan_path, linux_path.as_posix(), distribution


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()

    if args.list_presets:
        CLI().show_presets()
        return 0

    if not args.workspace:
        parser.error("the following arguments are required: -w/--workspace")

    try:
        backend = args.backend or detect_backend(args.workspace)

        workspace_path, wsl_workspace_path, distribution = resolve_workspace(
            workspace=args.workspace,
            backend=backend,
            distribution=args.distribution,
        )

        cleaner = Cleaner(
            workspace_path=workspace_path,
            target_folders=resolve_targets(
                args.targets,
                args.presets,
                args.add_targets,
            ),
            filesystem=create_cleaner(backend, distribution),
            wsl_workspace_path=wsl_workspace_path,
            dry_run=args.dry_run,
        )

        return CLI().run(
            cleaner=cleaner,
            workspace=args.workspace,
            backend=backend,
            distribution=distribution if backend == "wsl" else None,
            assume_yes=args.yes,
        )

    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 130

    except (NotADirectoryError, ValueError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
