import contextlib
import io
import sys
import unittest
from unittest.mock import patch

from dev_cleaner.cli.parser import create_parser
from dev_cleaner.main import main


def parse(*args: str):
    return create_parser().parse_args(list(args))


class ParserTests(unittest.TestCase):
    def test_workspace_is_optional_for_commands_without_it(self):
        args = parse("--list-presets")

        self.assertTrue(args.list_presets)
        self.assertIsNone(args.workspace)

    def test_target_and_preset_are_mutually_exclusive(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as context:
                parse("-w", ".", "-t", "dist", "--preset", "node")

        self.assertEqual(context.exception.code, 2)

    def test_presets_can_be_repeated(self):
        args = parse("-w", ".", "--preset", "node", "--preset", "python")

        self.assertEqual(args.presets, ["node", "python"])

    def test_unknown_preset_is_rejected(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as context:
                parse("-w", ".", "--preset", "unknown")

        self.assertEqual(context.exception.code, 2)

    def test_add_target_combines_with_a_preset(self):
        args = parse("-w", ".", "--preset", "node", "--add-target", "coverage")

        self.assertEqual(args.add_targets, ["coverage"])


class MainTests(unittest.TestCase):
    def test_list_presets_exits_zero_without_a_workspace(self):
        argv = ["dev-cleaner", "--list-presets"]

        with patch.object(sys, "argv", argv):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(), 0)


if __name__ == "__main__":
    unittest.main()
