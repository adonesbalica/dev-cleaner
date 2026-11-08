import os
import shutil
import stat
from pathlib import Path


def _handle_remove_error(function, path, exc_info) -> None:
    # Read-only files (common inside node_modules on Windows) block rmtree.
    os.chmod(path, stat.S_IWRITE)
    function(path)


class NativeCleaner:
    def remove(self, path: Path) -> None:
        if not path.is_dir():
            return

        shutil.rmtree(path, onexc=_handle_remove_error)
