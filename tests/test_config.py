import tempfile
import unittest
from pathlib import Path

from dev_cleaner.core.config import (
    Config,
    ConfigError,
    load_config,
    write_default_config,
)


class ConfigFileTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / ".dev-cleaner.toml"

    def write(self, text: str) -> None:
        self.path.write_text(text, encoding="utf-8")


class LoadConfigTests(ConfigFileTestCase):
    def test_missing_file_returns_defaults(self):
        self.assertEqual(load_config(self.path), Config())

    def test_required_missing_file_raises(self):
        with self.assertRaises(ConfigError):
            load_config(self.path, required=True)

    def test_full_file_is_parsed(self):
        self.write(
            'presets = ["node", "python"]\n'
            'add_targets = ["coverage"]\n'
            'exclude = ["legacy-*"]\n'
            "depth = 2\n"
            'min_size = "10MB"\n'
        )

        config = load_config(self.path)

        self.assertEqual(config.presets, ["node", "python"])
        self.assertEqual(config.add_targets, ["coverage"])
        self.assertEqual(config.exclude, ["legacy-*"])
        self.assertEqual(config.depth, 2)
        self.assertEqual(config.min_size, "10MB")

    def test_unknown_option_is_rejected(self):
        self.write('targetz = ["dist"]\n')

        with self.assertRaises(ConfigError) as context:
            load_config(self.path)

        self.assertIn("targetz", str(context.exception))

    def test_unknown_preset_is_rejected(self):
        self.write('presets = ["unknown"]\n')

        with self.assertRaises(ConfigError) as context:
            load_config(self.path)

        self.assertIn("unknown", str(context.exception))

    def test_depth_must_be_positive(self):
        self.write("depth = 0\n")

        with self.assertRaises(ConfigError):
            load_config(self.path)

    def test_lists_must_contain_strings(self):
        self.write("add_targets = [1]\n")

        with self.assertRaises(ConfigError):
            load_config(self.path)

    def test_invalid_toml_is_rejected(self):
        self.write("depth = \n")

        with self.assertRaises(ConfigError):
            load_config(self.path)


class WriteDefaultConfigTests(ConfigFileTestCase):
    def test_writes_a_commented_template(self):
        write_default_config(self.path)

        lines = self.path.read_text(encoding="utf-8").splitlines()

        self.assertTrue(
            all(not line.strip() or line.lstrip().startswith("#") for line in lines)
        )
        self.assertEqual(load_config(self.path), Config())

    def test_refuses_to_overwrite_an_existing_file(self):
        self.write("depth = 2\n")

        with self.assertRaises(ConfigError):
            write_default_config(self.path)

        self.assertEqual(self.path.read_text(encoding="utf-8"), "depth = 2\n")


if __name__ == "__main__":
    unittest.main()
