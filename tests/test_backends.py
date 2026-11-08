import stat
import subprocess
import unittest
from pathlib import Path, PurePosixPath
from unittest.mock import Mock, patch

from dev_cleaner.cleaners.native import NativeCleaner, _handle_remove_error
from dev_cleaner.cleaners.wsl import WslCleaner


class NativeCleanerTests(unittest.TestCase):
    @patch("dev_cleaner.cleaners.native.shutil.rmtree")
    def test_existing_directory_is_removed(self, rmtree):
        path = Mock(spec=Path)
        path.is_dir.return_value = True

        NativeCleaner().remove(path)

        rmtree.assert_called_once_with(path, onexc=_handle_remove_error)

    @patch("dev_cleaner.cleaners.native.shutil.rmtree")
    def test_missing_directory_is_ignored(self, rmtree):
        path = Mock(spec=Path)
        path.is_dir.return_value = False

        NativeCleaner().remove(path)

        rmtree.assert_not_called()

    @patch("dev_cleaner.cleaners.native.os.chmod")
    def test_read_only_file_is_made_writable_before_retry(self, chmod):
        retry = Mock()
        retry.side_effect = lambda path: chmod.assert_called_once_with(
            path, stat.S_IWRITE
        )
        path = Path("node_modules/locked.txt")

        _handle_remove_error(retry, path, PermissionError("read only"))

        retry.assert_called_once_with(path)


class WslCleanerTests(unittest.TestCase):
    @patch("dev_cleaner.cleaners.wsl.shutil.which", return_value=None)
    def test_missing_wsl_is_rejected(self, which):
        with self.assertRaisesRegex(ValueError, "WSL installed"):
            WslCleaner()

    @patch("dev_cleaner.cleaners.wsl.subprocess.run")
    @patch("dev_cleaner.cleaners.wsl.shutil.which", return_value="wsl")
    def test_path_with_spaces_is_passed_as_one_argument(self, which, run):
        run.return_value = subprocess.CompletedProcess([], 0, "", "")
        path = PurePosixPath("/home/user/my projects/app/node_modules")

        WslCleaner(distribution="Debian").remove(path)

        run.assert_called_once_with(
            ["wsl", "-d", "Debian", "--", "rm", "-rf", "--", str(path)],
            capture_output=True,
            text=True,
        )

    @patch("dev_cleaner.cleaners.wsl.subprocess.run")
    @patch("dev_cleaner.cleaners.wsl.shutil.which", return_value="wsl")
    def test_failed_removal_reports_command_output(self, which, run):
        for stderr, stdout, message in [
            (" permission denied\n", "other output", "permission denied"),
            ("", " failure\n", "failure"),
            ("", "", "wsl rm failed with exit code 1"),
        ]:
            with self.subTest(stderr=stderr, stdout=stdout):
                run.return_value = subprocess.CompletedProcess([], 1, stdout, stderr)

                with self.assertRaisesRegex(RuntimeError, message):
                    WslCleaner().remove(PurePosixPath("/workspace/app/dist"))


if __name__ == "__main__":
    unittest.main()
