import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dev_cleaner.main import main


class MainConfigTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.workspace = Path(self._tmp.name)

    def make(self, *parts: str) -> Path:
        path = self.workspace.joinpath(*parts)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_config(self, text: str) -> None:
        (self.workspace / ".dev-cleaner.toml").write_text(text, encoding="utf-8")

    def run_main(self, *args: str) -> tuple[int, str, str]:
        out = io.StringIO()
        err = io.StringIO()

        with patch.object(sys, "argv", ["dev-cleaner", *args]):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = main()

        return code, out.getvalue(), err.getvalue()

    def test_config_add_targets_is_used(self):
        self.make("app", "node_modules")
        self.make("app", "coverage")
        self.write_config('add_targets = ["coverage"]\n')

        code, out, _ = self.run_main("-w", str(self.workspace), "-n")

        self.assertEqual(code, 0)
        self.assertIn("app/coverage", out)
        self.assertIn("app/node_modules", out)

    def test_no_config_ignores_the_file(self):
        self.make("app", "node_modules")
        self.make("app", "coverage")
        self.write_config('add_targets = ["coverage"]\n')

        _, out, _ = self.run_main("-w", str(self.workspace), "-n", "--no-config")

        self.assertNotIn("app/coverage", out)

    def test_explicit_targets_override_config_presets(self):
        self.make("app", "node_modules")
        self.make("app", ".venv")
        self.write_config('presets = ["deps"]\n')

        _, out, _ = self.run_main(
            "-w",
            str(self.workspace),
            "-n",
            "-t",
            "node_modules",
        )

        self.assertIn("app/node_modules", out)
        self.assertNotIn(".venv", out)

    def test_config_depth_is_used(self):
        self.make("packages", "app", "node_modules")
        self.write_config("depth = 2\n")

        _, out, _ = self.run_main("-w", str(self.workspace), "-n")

        self.assertIn("packages/app/node_modules", out)

    def test_cli_depth_overrides_the_config(self):
        self.make("packages", "app", "node_modules")
        self.write_config("depth = 1\n")

        _, out, _ = self.run_main("-w", str(self.workspace), "-n", "--depth", "2")

        self.assertIn("packages/app/node_modules", out)

    def test_config_exclude_is_used(self):
        self.make("legacy", "node_modules")
        self.make("current", "node_modules")
        self.write_config('exclude = ["legacy"]\n')

        _, out, _ = self.run_main("-w", str(self.workspace), "-n")

        self.assertNotIn("legacy/node_modules", out)
        self.assertIn("current/node_modules", out)

    def test_invalid_config_exits_with_two(self):
        self.make("app", "node_modules")
        self.write_config("unknown = true\n")

        code, _, err = self.run_main("-w", str(self.workspace), "-n")

        self.assertEqual(code, 2)
        self.assertIn("unknown", err)

    def test_missing_explicit_config_exits_with_two(self):
        self.make("app", "node_modules")
        missing = self.workspace / "missing.toml"

        code, _, err = self.run_main(
            "-w",
            str(self.workspace),
            "-n",
            "--config",
            str(missing),
        )

        self.assertEqual(code, 2)
        self.assertIn("not found", err)

    def test_init_writes_the_config(self):
        self.make("app", "node_modules")

        code, out, _ = self.run_main("-w", str(self.workspace), "--init")

        self.assertEqual(code, 0)
        self.assertTrue((self.workspace / ".dev-cleaner.toml").is_file())
        self.assertIn("Wrote", out)

    def test_init_refuses_to_overwrite(self):
        self.write_config("depth = 2\n")

        code, _, err = self.run_main("-w", str(self.workspace), "--init")

        self.assertEqual(code, 2)
        self.assertIn("already exists", err)

    def test_init_with_an_explicit_path_does_not_need_a_workspace(self):
        path = self.workspace / "custom.toml"

        code, _, _ = self.run_main("--init", "--config", str(path))

        self.assertEqual(code, 0)
        self.assertTrue(path.is_file())


if __name__ == "__main__":
    unittest.main()
