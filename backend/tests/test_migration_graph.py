"""Offline checks for the Alembic revision graph; no database is required."""
from pathlib import Path
import unittest

from alembic.config import Config
from alembic.script import ScriptDirectory


BACKEND_ROOT = Path(__file__).resolve().parents[1]


class MigrationGraphTests(unittest.TestCase):
    def setUp(self):
        config = Config(str(BACKEND_ROOT / "alembic.ini"))
        config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
        self.script = ScriptDirectory.from_config(config)

    def test_migrations_have_one_linear_head_and_reach_base(self):
        heads = self.script.get_revisions("heads")
        self.assertEqual(len(heads), 1, "migration history must have a single deployable head")

        revisions = list(self.script.walk_revisions())
        self.assertTrue(revisions, "migration history must not be empty")
        self.assertEqual(len({revision.revision for revision in revisions}), len(revisions))
        self.assertEqual(revisions[-1].down_revision, None, "migration history must reach a base revision")

    def test_each_revision_has_a_parent_except_base(self):
        revisions = {revision.revision: revision for revision in self.script.walk_revisions()}
        for revision in revisions.values():
            if revision.down_revision is None:
                continue
            parents = revision.down_revision
            if isinstance(parents, str):
                parents = (parents,)
            for parent in parents:
                with self.subTest(revision=revision.revision, parent=parent):
                    self.assertIn(parent, revisions, "revision references a missing parent")


if __name__ == "__main__":
    unittest.main()
