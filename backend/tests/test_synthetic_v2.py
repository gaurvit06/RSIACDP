import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from evaluation.generate_synthetic_v2 import generate
from evaluation.run_synthetic_pipeline import _read_fixture, _source_snapshot_sha256


class SyntheticV2FixtureTests(unittest.TestCase):
    def test_runner_source_fingerprint_is_a_sha256_digest(self):
        self.assertRegex(_source_snapshot_sha256(), r"^[0-9a-f]{64}$")

    def test_generator_writes_time_separated_campaign_scoped_reserved_entities(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "fixture"
            generate(output)
            input_path = output / "synthetic-input.jsonl"
            payload = input_path.read_bytes()
            manifest = json.loads((output / "MANIFEST.json").read_text(encoding="utf-8"))
            rows, digest = _read_fixture(input_path)

            self.assertEqual(manifest["generator_version"], "synthetic-fixtures-v2")
            self.assertEqual(manifest["sha256"], hashlib.sha256(payload).hexdigest())
            self.assertEqual(digest, manifest["sha256"])
            self.assertEqual(len(rows), 108)
            self.assertEqual({split: sum(row["split"] == split for row in rows) for split in ("train", "dev", "test")}, {"train": 36, "dev": 36, "test": 36})
            campaigns = {}
            for row in rows:
                email, domain = row["gold_entities"]
                self.assertEqual(email["type"], "email")
                self.assertEqual(domain["type"], "domain")
                self.assertTrue(email["value"].endswith("@" + domain["value"]))
                self.assertTrue(domain["value"].endswith(".invalid"))
                supported = {(item["type"], item["value"]) for item in row["gold_supported_entities"]}
                gold = {(item["type"], item["value"]) for item in row["gold_entities"]}
                self.assertLessEqual(supported, gold)
                campaigns.setdefault(row["campaign_id"], set()).add(domain["value"])
            self.assertTrue(all(len(domains) == 1 for domains in campaigns.values()))
            self.assertEqual(len({next(iter(domains)) for domains in campaigns.values()}), len(campaigns))

    def test_generator_refuses_to_overwrite_an_existing_fixture_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "fixture"
            output.mkdir()
            sentinel = output / "sentinel.txt"
            sentinel.write_text("preserve", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                generate(output)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve")


if __name__ == "__main__":
    unittest.main()
