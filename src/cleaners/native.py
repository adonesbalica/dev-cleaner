import shutil
from pathlib import Path


class NativeCleaner:
    def remove(self, path: Path) -> None:
        if path.is_dir():
            shutil.rmtree(path)