import shutil
import subprocess
from pathlib import PurePosixPath


class WslCleaner:
    def __init__(self, distribution: str = "Ubuntu"):
        if shutil.which("wsl") is None:
            raise ValueError(
                "The wsl backend requires Windows with WSL installed. "
                "Use the native backend on Linux."
            )

        self.distribution = distribution

    def remove(self, path: PurePosixPath) -> None:
        result = subprocess.run(
            [
                "wsl",
                "-d",
                self.distribution,
                "--",
                "rm",
                "-rf",
                "--",
                str(path),
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip()

            raise RuntimeError(
                message or f"wsl rm failed with exit code {result.returncode}"
            )
