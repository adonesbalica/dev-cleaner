import io
import unittest

from dev_cleaner.cli.interface import CLI, summarize_targets
from dev_cleaner.core.catalog import PRESETS


class SummarizeTargetsTests(unittest.TestCase):
    def test_short_list_is_printed_whole(self):
        self.assertEqual(summarize_targets(["a", "b"]), "a, b")

    def test_long_list_is_truncated(self):
        targets = [f"t{index}" for index in range(8)]

        self.assertEqual(summarize_targets(targets, limit=3), "t0, t1, t2 and 5 more")


class ShowPresetsTests(unittest.TestCase):
    def test_lists_every_preset_and_the_defaults(self):
        out = io.StringIO()

        CLI(out=out, err=io.StringIO()).show_presets()

        text = out.getvalue()

        for name in PRESETS:
            self.assertIn(name, text)

        self.assertIn("defaults:", text)


if __name__ == "__main__":
    unittest.main()
