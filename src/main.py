from pathlib import Path

import yaml

from cleaners.native import NativeCleaner
from cleaners.wsl import WslCleaner
from core.cleaner import Cleaner


def load_config():
    config_path = Path(__file__).parent.parent / "config.yaml"

    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def create_cleaner(config):
    backend = config["cleanup_backend"]

    if backend == "native":
        return NativeCleaner()

    if backend == "wsl":
        distribution = config["wsl"]["distribution"]
        return WslCleaner(distribution)

    raise ValueError(f"Unsupported cleanup backend: {backend}")


def main():
    config = load_config()["config"]

    cleaner_backend = create_cleaner(config)

    cleaner = Cleaner(
        workspace_path=Path(config["workspace_path"]),
        target_folders=config["target_folders"],
        filesystem=cleaner_backend,
    )

    cleaner.run()


if __name__ == "__main__":
    main()