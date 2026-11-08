import subprocess
from pathlib import PurePosixPath


class WslCleaner:
    def __init__(self, distribution: str = "Ubuntu"):
        self.distribution = distribution

    def remove(self, path: PurePosixPath) -> None:
        subprocess.run(
            [
                "wsl",
                "-d", self.distribution,
                "--",
                "rm", "-rf", "--",
                str(path),
            ],
            check=True,
        )