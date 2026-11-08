import subprocess
from pathlib import Path


class Main:
    def __init__(self):
        self.list_folder = {}
        self.target_folders = ["node_modules", ".next"]
        self.dir_path = Path("//wsl.localhost/Ubuntu/home/adonebalica/workspace")
        self.base_path = "/home/adonebalica/workspace"

    def return_children_folder(self):
        self.list_folder = {
            item.name: item
            for item in self.dir_path.iterdir()
            if item.is_dir()
        }

        return self.list_folder

    def delete_folder(self):
        for folder in self.list_folder.values():
            for target in self.target_folders:
                linux_path = (
                    f"{self.base_path}/{folder.name}/{target}"
                )

                check = subprocess.run(
                    ["wsl", "-d", "Ubuntu", "--", "test", "-d", linux_path]
                )

                if check.returncode == 0:
                    subprocess.run(
                        [
                            "wsl", "-d", "Ubuntu", "--",
                            "rm", "-rf", "--", linux_path
                        ],
                        check=True
                    )

    def details(self):
        print(f"{len(self.list_folder)} folders found in {self.dir_path}")

        for key in self.list_folder:
            print(key)


cleaner = Main()
cleaner.return_children_folder()
cleaner.details()
cleaner.delete_folder()
