from pathlib import Path, PurePosixPath
from typing import Protocol


class FileSystemCleaner(Protocol):
    def remove(self, path: Path | PurePosixPath) -> None:
        """Remove a directory from the filesystem."""
        ...
