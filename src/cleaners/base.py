from pathlib import Path
from typing import Protocol

class FileSystemCleaner(Protocol):
    def remove(self, path: Path) -> None:
        ...