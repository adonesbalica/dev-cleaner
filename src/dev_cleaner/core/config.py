"""Workspace configuration loaded from ``.dev-cleaner.toml``."""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from dev_cleaner.core.catalog import PRESETS

CONFIG_FILENAME = ".dev-cleaner.toml"

ALLOWED_KEYS = {"presets", "add_targets", "exclude", "depth", "min_size"}

TEMPLATE = """\
# dev-cleaner configuration for this workspace.
# Uncomment the options you want to change.

# Presets added on top of the default targets.
# presets = ["node", "python"]

# Extra directories added to the defaults.
# add_targets = ["coverage"]

# Projects to skip. Globs match the relative path or the directory name.
# exclude = ["legacy-*"]

# How many directory levels to scan.
# depth = 1

# Skip targets smaller than this size.
# min_size = "10MB"
"""


class ConfigError(ValueError):
    """Raised when a configuration file is invalid."""


@dataclass
class Config:
    presets: list[str] = field(default_factory=list)
    add_targets: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    depth: int | None = None
    min_size: str | None = None


def _string_list(data: dict, key: str) -> list[str]:
    value = data.get(key, [])

    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise ConfigError(f"'{key}' must be a list of non-empty strings.")

    return list(value)


def _positive_int(data: dict, key: str) -> int | None:
    value = data.get(key)

    if value is None:
        return None

    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ConfigError(f"'{key}' must be an integer greater than or equal to 1.")

    return value


def _string(data: dict, key: str) -> str | None:
    value = data.get(key)

    if value is None:
        return None

    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"'{key}' must be a non-empty string.")

    return value


def load_config(path: Path, *, required: bool = False) -> Config:
    """Read a configuration file, returning defaults when it does not exist."""

    if not path.exists():
        if required:
            raise ConfigError(f"Config file not found: {path}")

        return Config()

    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ConfigError(f"Cannot read {path}: {error}") from None
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"Invalid TOML in {path}: {error}") from None

    unknown = sorted(set(data) - ALLOWED_KEYS)

    if unknown:
        raise ConfigError(
            f"Unknown option in {path}: {', '.join(unknown)}. "
            f"Allowed options: {', '.join(sorted(ALLOWED_KEYS))}."
        )

    presets = _string_list(data, "presets")
    invalid_presets = sorted(set(presets) - set(PRESETS))

    if invalid_presets:
        raise ConfigError(
            f"Unknown preset in {path}: {', '.join(invalid_presets)}. "
            f"Available presets: {', '.join(sorted(PRESETS))}."
        )

    return Config(
        presets=presets,
        add_targets=_string_list(data, "add_targets"),
        exclude=_string_list(data, "exclude"),
        depth=_positive_int(data, "depth"),
        min_size=_string(data, "min_size"),
    )


def write_default_config(path: Path) -> None:
    """Write a commented template, refusing to overwrite an existing file."""

    if path.exists():
        raise ConfigError(f"Config file already exists: {path}")

    try:
        path.write_text(TEMPLATE, encoding="utf-8")
    except OSError as error:
        raise ConfigError(f"Cannot write {path}: {error}") from None
