
from pathlib import Path

from cleaners.base import FileSystemCleaner


class Cleaner:
    def __init__(
        self,
        workspace_path: Path,
        target_folders: list[str],
        filesystem: FileSystemCleaner,
    ):
        self.workspace_path = workspace_path
        self.target_folders = target_folders
        self.filesystem = filesystem

    def get_projects(self) -> list[Path]:
        if not self.workspace_path.is_dir():
            raise NotADirectoryError(
                f"Workspace not found: {self.workspace_path}"
            )

        return [
            item
            for item in self.workspace_path.iterdir()
            if item.is_dir()
        ]

    def clean_project(self, project: Path) -> None:
        for target in self.target_folders:
            target_path = project / target

            # Ensure the target is a direct child of the project.
            if target_path.parent != project:
                raise ValueError(f"Invalid target directory: {target}")

            if target_path.is_dir():
                self.filesystem.remove(target_path)
                print(f"Deleted: {project.name}/{target}")

    def run(self) -> None:
        projects = self.get_projects()

        print(
            f"{len(projects)} projects found in "
            f"{self.workspace_path}"
        )

        for project in projects:
            self.clean_project(project)
