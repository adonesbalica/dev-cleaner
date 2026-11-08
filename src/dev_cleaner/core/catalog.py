"""Target directories, presets, and directories to prune while scanning."""

from collections.abc import Sequence

DEFAULT_TARGETS = [
    "node_modules",
    ".next",
    "dist",
    "__pycache__",
    "target",
]

PRESETS: dict[str, tuple[str, ...]] = {
    "node": (
        "node_modules",
        ".next",
        ".nuxt",
        ".output",
        ".svelte-kit",
        ".astro",
        ".turbo",
        ".parcel-cache",
        ".vite",
        "coverage",
        ".nyc_output",
        "storybook-static",
        "out",
    ),
    "python": (
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".hypothesis",
        ".ipynb_checkpoints",
        "htmlcov",
        "build",
        "dist",
    ),
    "rust": ("target",),
    "java": ("build", "out", ".gradle"),
    "dotnet": ("bin", "obj"),
    "elixir": ("_build",),
    "terraform": (".terraform",),
    # Regenerable, but expensive to recreate, so this preset is never in "all".
    "deps": (
        "vendor",
        "Pods",
        ".venv",
        "venv",
        ".tox",
        ".nox",
        ".bundle",
        "deps",
        ".yarn",
    ),
}

SAFE_PRESETS = (
    "node",
    "python",
    "rust",
    "java",
    "dotnet",
    "elixir",
    "terraform",
)

PRESETS["all"] = tuple(
    dict.fromkeys(target for preset in SAFE_PRESETS for target in PRESETS[preset])
)

# Never descend into these while looking for projects.
PRUNE_DIRS = frozenset(
    {
        ".git",
        *DEFAULT_TARGETS,
        *(target for targets in PRESETS.values() for target in targets),
    }
)


def resolve_targets(
    explicit: Sequence[str] | None = None,
    presets: Sequence[str] | None = None,
    extra: Sequence[str] | None = None,
) -> list[str]:
    """Build the effective target list, preserving order and removing duplicates.

    ``explicit`` (``-t``) replaces the defaults and any preset. Otherwise the
    defaults are expanded with the selected presets. ``extra`` is always
    appended.
    """

    if explicit:
        targets = list(explicit)
    else:
        targets = list(DEFAULT_TARGETS)

        for preset in presets or []:
            targets.extend(PRESETS[preset])

    targets.extend(extra or [])

    return list(dict.fromkeys(targets))
