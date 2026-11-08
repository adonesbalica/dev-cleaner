import os
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from src.cleaners.base import FileSystemCleaner


def is_link(path: Path) -> bool:
    """True for symlinks and, on Windows, directory junctions."""

    if path.is_symlink():
        return True

    is_junction = getattr(os.path, "isjunction", None)

    return bool(is_junction and is_junction(path))


@dataclass
class CleanupResult:
    project: str
    target: str
    path: Path | PurePosixPath
    success: bool
    error: str | None = None


@dataclass
class CleanupReport:
    projects_scanned: int = 0
    results: list[CleanupResult] = field(default_factory=list)

    @property
    def removed(self) -> list[CleanupResult]:
        return [result for result in self.results if result.success]

    @property
    def failed(self) -> list[CleanupResult]:
        return [result for result in self.results if not result.success]


class Cleaner:
    def __init__(
        self,
        workspace_path: Path,
        target_folders: list[str],
        filesystem: FileSystemCleaner,
        wsl_workspace_path: str | None = None,
        dry_run: bool = False,
    ):
        self.workspace_path = workspace_path
        self.target_folders = target_folders
        self.filesystem = filesystem
        self.wsl_workspace_path = wsl_workspace_path
        self.dry_run = dry_run

        self._validate_workspace()
        self._validate_targets()

    def _validate_workspace(self) -> None:
        anchor = self.workspace_path.anchor

        if anchor and self.workspace_path == Path(anchor):
            raise ValueError(
                f"Refusing to scan a filesystem root: {self.workspace_path}"
            )

        if not self.workspace_path.is_dir():
            raise NotADirectoryError(f"Workspace not found: {self.workspace_path}")

    def _validate_targets(self) -> None:
        for target in self.target_folders:
            target_path = Path(target)

            if (
                target_path.is_absolute()
                or len(target_path.parts) != 1
                or target in {".", ".."}
            ):
                raise ValueError(f"Invalid target directory: {target}")

    def _removal_path(self, target_path: Path) -> Path | PurePosixPath:
        if self.wsl_workspace_path is None:
            return target_path

        relative_path = target_path.relative_to(self.workspace_path)

        return PurePosixPath(self.wsl_workspace_path, *relative_path.parts)

    def get_projects(self) -> list[Path]:
        if not self.workspace_path.is_dir():
            raise NotADirectoryError(f"Workspace not found: {self.workspace_path}")

        return [
            item
            for item in self.workspace_path.iterdir()
            if item.is_dir() and not is_link(item)
        ]

    def clean_project(
        self,
        project: Path,
        on_target: Callable[[Path, str], None] | None = None,
    ) -> list[CleanupResult]:
        results = []

        for target in self.target_folders:
            target_path = project / target

            if is_link(target_path) or not target_path.is_dir():
                continue

            if on_target:
                on_target(project, target)

            try:
                removal_path = self._removal_path(target_path)

                if not self.dry_run:
                    self.filesystem.remove(removal_path)

                results.append(
                    CleanupResult(
                        project=project.name,
                        target=target,
                        path=removal_path,
                        success=True,
                    )
                )

            except Exception as error:
                results.append(
                    CleanupResult(
                        project=project.name,
                        target=target,
                        path=target_path,
                        success=False,
                        error=str(error),
                    )
                )

        return results

    def run(
        self,
        on_progress: Callable[[int, int, Path], None] | None = None,
        on_target: Callable[[int, int, Path, str], None] | None = None,
    ) -> CleanupReport:
        projects = self.get_projects()

        report = CleanupReport(
            projects_scanned=len(projects),
        )

        for index, project in enumerate(projects, start=1):

            def report_target(
                target_project: Path,
                target: str,
                index: int = index,
            ) -> None:
                if on_target is not None:
                    on_target(index, len(projects), target_project, target)

            report.results.extend(self.clean_project(project, on_target=report_target))

            if on_progress:
                on_progress(index, len(projects), project)

        return report
