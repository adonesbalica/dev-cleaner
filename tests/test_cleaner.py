import os
import tempfile
import unittest
from pathlib import Path

from dev_cleaner.core.cleaner import Cleaner


class RecordingCleaner:
    def __init__(self):
        self.removed = []

    def remove(self, path):
        self.removed.append(path)


class CleanerTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.workspace = Path(self._tmp.name)
        self.filesystem = RecordingCleaner()

    def make(self, *parts: str) -> Path:
        path = self.workspace.joinpath(*parts)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def cleaner(self, targets=None, **kwargs) -> Cleaner:
        return Cleaner(
            workspace_path=self.workspace,
            target_folders=targets or ["node_modules"],
            filesystem=self.filesystem,
            **kwargs,
        )

    def labels(self, cleaner: Cleaner) -> list[str]:
        return [cleaner.project_label(project) for project in cleaner.get_projects()]


class ProjectDiscoveryTests(CleanerTestCase):
    def test_depth_one_only_reaches_direct_children(self):
        self.make("app", "node_modules")
        self.make("packages", "app", "node_modules")

        self.assertEqual(self.labels(self.cleaner()), ["app", "packages"])

    def test_depth_two_reaches_nested_projects(self):
        self.make("packages", "app", "node_modules")

        self.assertEqual(
            self.labels(self.cleaner(depth=2)),
            ["packages", "packages/app"],
        )

    def test_depth_three_reaches_deeper_projects(self):
        self.make("apps", "web", "frontend", "node_modules")

        self.assertIn("apps/web/frontend", self.labels(self.cleaner(depth=3)))

    def test_directories_are_sorted(self):
        self.make("b", "node_modules")
        self.make("a", "node_modules")

        self.assertEqual(self.labels(self.cleaner()), ["a", "b"])

    def test_git_and_target_directories_are_pruned(self):
        self.make(".git", "node_modules")
        self.make("node_modules", "package", "node_modules")

        self.assertEqual(self.labels(self.cleaner(depth=3)), [])

    @unittest.skipIf(os.name == "nt", "symlinks need privileges on Windows")
    def test_symlinked_projects_are_skipped(self):
        self.make("real", "node_modules")
        (self.workspace / "link").symlink_to(
            self.workspace / "real",
            target_is_directory=True,
        )

        self.assertEqual(self.labels(self.cleaner()), ["real"])


class ExcludeTests(CleanerTestCase):
    def test_exclude_matches_the_project_name(self):
        self.make("app-a", "node_modules")
        self.make("app-b", "node_modules")

        self.assertEqual(
            self.labels(self.cleaner(exclude=["app-a"])),
            ["app-b"],
        )

    def test_exclude_matches_the_relative_path(self):
        self.make("packages", "legacy", "node_modules")
        self.make("packages", "current", "node_modules")

        self.assertEqual(
            self.labels(self.cleaner(depth=2, exclude=["packages/legacy"])),
            ["packages", "packages/current"],
        )

    def test_exclude_glob_matches_nested_names(self):
        self.make("packages", "legacy-app", "node_modules")

        self.assertNotIn(
            "packages/legacy-app",
            self.labels(self.cleaner(depth=2, exclude=["legacy-*"])),
        )


class RunTests(CleanerTestCase):
    def test_nested_targets_are_reported_with_the_relative_label(self):
        self.make("packages", "app", "node_modules")

        report = self.cleaner(depth=2).run()

        self.assertEqual(
            [(result.project, result.target) for result in report.results],
            [("packages/app", "node_modules")],
        )

    def test_depth_one_ignores_nested_targets(self):
        self.make("packages", "app", "node_modules")

        self.assertEqual(self.cleaner(depth=1).run().results, [])

    def test_dry_run_does_not_remove_anything(self):
        self.make("app", "node_modules")

        report = self.cleaner(dry_run=True).run()

        self.assertEqual(len(report.removed), 1)
        self.assertEqual(self.filesystem.removed, [])

    def test_removal_uses_the_target_path(self):
        target = self.make("app", "node_modules")

        self.cleaner().run()

        self.assertEqual(self.filesystem.removed, [target])

    def test_depth_below_one_is_rejected(self):
        with self.assertRaises(ValueError):
            self.cleaner(depth=0)


if __name__ == "__main__":
    unittest.main()
