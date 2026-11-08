import unittest

from dev_cleaner.core.catalog import (
    DEFAULT_TARGETS,
    PRESETS,
    PRUNE_DIRS,
    SAFE_PRESETS,
    resolve_targets,
)


class ResolveTargetsTests(unittest.TestCase):
    def test_defaults_when_nothing_is_given(self):
        self.assertEqual(resolve_targets(), DEFAULT_TARGETS)

    def test_explicit_replaces_defaults_and_presets(self):
        self.assertEqual(resolve_targets(["custom"], ["node"]), ["custom"])

    def test_preset_adds_to_the_defaults(self):
        result = resolve_targets(presets=["rust"])

        self.assertEqual(result[: len(DEFAULT_TARGETS)], DEFAULT_TARGETS)
        self.assertIn("target", result)

    def test_preset_expands_all_of_its_targets(self):
        result = resolve_targets(presets=["java"])

        for target in PRESETS["java"]:
            self.assertIn(target, result)

    def test_extra_is_appended(self):
        self.assertEqual(resolve_targets(extra=["coverage"])[-1], "coverage")

    def test_duplicates_are_removed_in_order(self):
        result = resolve_targets(["node_modules", "dist"], extra=["node_modules"])

        self.assertEqual(result, ["node_modules", "dist"])

    def test_multiple_presets_are_merged(self):
        result = resolve_targets(presets=["rust", "dotnet"])

        self.assertIn("target", result)
        self.assertIn("bin", result)
        self.assertIn("obj", result)

    def test_all_excludes_the_deps_preset(self):
        self.assertNotIn("vendor", PRESETS["all"])
        self.assertNotIn(".venv", PRESETS["all"])

        for preset in SAFE_PRESETS:
            for target in PRESETS[preset]:
                self.assertIn(target, PRESETS["all"])

    def test_prune_dirs_include_git_and_default_targets(self):
        self.assertIn(".git", PRUNE_DIRS)

        for target in DEFAULT_TARGETS:
            self.assertIn(target, PRUNE_DIRS)


if __name__ == "__main__":
    unittest.main()
