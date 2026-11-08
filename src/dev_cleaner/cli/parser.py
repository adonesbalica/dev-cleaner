import argparse

from dev_cleaner import __version__
from dev_cleaner.core.catalog import PRESETS

PRESET_NAMES = ", ".join(sorted(PRESETS))


def positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid integer: {value}") from None

    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")

    return number


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dev-cleaner",
        description="Remove generated directories from every project in a workspace.",
        epilog=(
            "examples:\n"
            "  dev-cleaner -w C:/Users/me/workspace\n"
            "  dev-cleaner -w /home/me/workspace -n\n"
            "  dev-cleaner -w /home/me/workspace --preset node --preset python -y\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-w",
        "--workspace",
        metavar="PATH",
        help="Workspace directory to scan.",
    )

    targets = parser.add_mutually_exclusive_group()

    targets.add_argument(
        "-t",
        "--target",
        action="append",
        dest="targets",
        metavar="DIR",
        help=("Directory to remove. Repeatable. Replaces the defaults and any preset."),
    )

    targets.add_argument(
        "--preset",
        action="append",
        dest="presets",
        choices=sorted(PRESETS),
        metavar="NAME",
        help=(
            "Preset group of directories to remove. Repeatable. "
            f"Choices: {PRESET_NAMES}. Adds to the defaults."
        ),
    )

    parser.add_argument(
        "--add-target",
        action="append",
        dest="add_targets",
        metavar="DIR",
        help="Directory to add to the defaults, -t, or --preset. Repeatable.",
    )

    parser.add_argument(
        "--list-presets",
        action="store_true",
        help="List the available presets and exit.",
    )

    parser.add_argument(
        "--depth",
        type=positive_int,
        metavar="N",
        help="How many directory levels to scan for projects. Defaults to 1.",
    )

    parser.add_argument(
        "--exclude",
        action="append",
        dest="excludes",
        metavar="PATTERN",
        help=(
            "Skip projects whose relative path or name matches the glob. Repeatable."
        ),
    )

    config = parser.add_mutually_exclusive_group()

    config.add_argument(
        "--config",
        metavar="PATH",
        help="Configuration file. Defaults to <workspace>/.dev-cleaner.toml.",
    )

    config.add_argument(
        "--no-config",
        action="store_true",
        help="Ignore the workspace configuration file.",
    )

    parser.add_argument(
        "--init",
        action="store_true",
        help="Write a commented .dev-cleaner.toml and exit.",
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
