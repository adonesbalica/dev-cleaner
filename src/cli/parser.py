import argparse

from src import __version__

DEFAULT_TARGETS = [
    "node_modules",
    ".next",
    "dist",
]


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dev-cleaner",
        description="Remove generated directories from every project in a workspace.",
        epilog=(
            "examples:\n"
            "  python -m src.main -w C:/Users/me/workspace\n"
            "  python -m src.main -w /home/me/workspace -n\n"
            "  python -m src.main -w /home/me/workspace -t node_modules -t .venv -y\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-w",
        "--workspace",
        required=True,
        metavar="PATH",
        help="Workspace directory to scan.",
    )

    parser.add_argument(
        "-t",
        "--target",
        action="append",
        dest="targets",
        metavar="DIR",
        help=(
            "Directory to remove. Repeatable. "
            f"Defaults to: {', '.join(DEFAULT_TARGETS)}."
        ),
    )

    parser.add_argument(
        "-b",
        "--backend",
        type=str.lower,
        choices=["native", "wsl"],
        metavar="NAME",
        help="Force native or wsl. Defaults to auto-detection.",
    )

    parser.add_argument(
        "-d",
        "--distribution",
        metavar="DISTRO",
        help="WSL distribution. Defaults to the detected default, then Ubuntu.",
    )

    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Show what would be removed without deleting anything.",
    )

    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Do not ask for confirmation.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser
