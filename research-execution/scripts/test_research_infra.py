"""Software fixtures only: these temporary records are not research evidence."""
import json
from pathlib import Path
import tempfile
import unittest

import research_infra as infra


class InfrastructureTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="research-infra-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "project"
        infra.initialize(self.root, "SOFTWARE_TEST_ONLY")

    def load(self, name):
        return infra.read_json(self.root / name)

    def save(self, name, data):
        (self.root / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def accept(self, number=0):
        board = self.load("tasks.json")
        task = board["tasks"][number]
        tid = task["id"]
        relative = f"artifacts/{tid}.txt"
        (self.root / relative).write_text("SOFTWARE TEST FIXTURE, NOT SCIENTIFIC EVIDENCE", encoding="utf-8")
        record = {"path": relative, "sha256": infra.digest(self.root / relative)}
        review_path = f"reviews/{tid}.json"
        review = {"task_id": tid, "verdict": "ACCEPT", "reviewer": "fixture-reviewer", "independent_context": True, "context_record": "fixture only", "artifact_sha256": {relative: record["sha256"]}, "checks": ["fixture hash binding"], "limitations": ["not a real review"]}
        self.save(review_path, review)
        task.update(status="ACCEPTED", owner="fixture-author", acceptance_criteria=["software fixture"], outputs=[record], review={"path": review_path, "sha256": infra.digest(self.root / review_path)})
        self.save("tasks.json", board)

    def ready_snapshot(self):
        for i in range(5):
            self.accept(i)
        (self.root / "protocol" / "design.md").write_text("test protocol", encoding="utf-8")

    def change_review(self, **changes):
        review = self.load("reviews/G0.json")
        review.update(changes)
        self.save("reviews/G0.json", review)
        board = self.load("tasks.json")
        board["tasks"][0]["review"]["sha256"] = infra.digest(self.root / "reviews/G0.json")
        self.save("tasks.json", board)

    def test_new_project_is_unaccepted_and_ready(self):
        report = infra.check(self.root)
        self.assertTrue(report["ok"])
        self.assertEqual(report["counts"], {"TODO": 10})
        self.assertEqual(report["ready_tasks"], ["G0"])

    def test_initialization_never_overwrites(self):
        original = infra.digest(self.root / "tasks.json")
        with self.assertRaises(ValueError):
            infra.initialize(self.root, "another")
        self.assertEqual(infra.digest(self.root / "tasks.json"), original)

    def test_duplicate_id_rejected(self):
        board = self.load("tasks.json")
        board["tasks"].append(board["tasks"][0])
        self.save("tasks.json", board)
        self.assertFalse(infra.check(self.root)["ok"])

    def test_missing_dependency_rejected(self):
        board = self.load("tasks.json")
        board["tasks"][0]["depends_on"] = ["absent"]
        self.save("tasks.json", board)
        self.assertFalse(infra.check(self.root)["ok"])

    def test_dependency_cycle_rejected(self):
        board = self.load("tasks.json")
        board["tasks"][0]["depends_on"] = ["G1"]
        self.save("tasks.json", board)
        self.assertFalse(infra.check(self.root)["ok"])

    def test_unaccepted_upstream_blocks_acceptance(self):
        self.accept(1)
        self.assertFalse(infra.check(self.root)["ok"])

    def test_accepted_task_unlocks_next(self):
        self.accept()
        report = infra.check(self.root)
        self.assertTrue(report["ok"])
        self.assertEqual(report["ready_tasks"], ["G1"])

    def test_modified_artifact_invalidates_acceptance(self):
        self.accept()
        (self.root / "artifacts/G0.txt").write_text("changed", encoding="utf-8")
        self.assertFalse(infra.check(self.root)["ok"])

    def test_modified_review_invalidates_acceptance(self):
        self.accept()
        (self.root / "reviews/G0.json").write_text("{}", encoding="utf-8")
        self.assertFalse(infra.check(self.root)["ok"])

    def test_self_review_cannot_be_independent(self):
        self.accept()
        self.change_review(reviewer="fixture-author")
        self.assertFalse(infra.check(self.root)["ok"])

    def test_independent_context_required(self):
        self.accept()
        self.change_review(independent_context=False)
        self.assertFalse(infra.check(self.root)["ok"])

    def test_review_must_bind_current_outputs(self):
        self.accept()
        self.change_review(artifact_sha256={"artifacts/G0.txt": "0" * 64})
        self.assertFalse(infra.check(self.root)["ok"])

    def test_no_evidence_no_acceptance(self):
        self.accept()
        board = self.load("tasks.json")
        board["tasks"][0]["outputs"] = []
        self.save("tasks.json", board)
        self.assertFalse(infra.check(self.root)["ok"])

    def test_traversal_and_absolute_paths_rejected(self):
        for relative in ("../outside.txt", "C:\\outside.txt", "/outside.txt", "data/../tasks.json", "tasks.json:stream"):
            with self.subTest(relative=relative), self.assertRaises(ValueError):
                infra.local_file(self.root, relative)

    def test_low_risk_task_requires_self_check(self):
        self.accept()
        board = self.load("tasks.json")
        board["tasks"][0].update(review_required=False, review=None)
        self.save("tasks.json", board)
        self.assertFalse(infra.check(self.root)["ok"])
        board["tasks"][0]["self_check"] = "actual low risk check in a software fixture"
        self.save("tasks.json", board)
        self.assertTrue(infra.check(self.root)["ok"])

    def test_snapshot_cannot_bypass_gates(self):
        with self.assertRaises(ValueError):
            infra.snapshot(self.root, "p1", "protocol", ["README.md"])
        self.assertFalse((self.root / "snapshots/p1.json").exists())

    def test_snapshot_no_overwrite_or_state_mutation(self):
        self.ready_snapshot()
        original = infra.digest(self.root / "tasks.json")
        infra.snapshot(self.root, "p1", "protocol", ["protocol/design.md"])
        self.assertTrue(infra.verify(self.root, "snapshots/p1.json")["ok"])
        with self.assertRaises(FileExistsError):
            infra.snapshot(self.root, "p1", "protocol", ["protocol/design.md"])
        self.assertEqual(infra.digest(self.root / "tasks.json"), original)

    def test_snapshot_detects_changed_selected_file(self):
        self.ready_snapshot()
        infra.snapshot(self.root, "p1", "protocol", ["protocol/design.md"])
        (self.root / "protocol/design.md").write_text("changed", encoding="utf-8")
        self.assertFalse(infra.verify(self.root, "snapshots/p1.json")["ok"])

    def test_snapshot_explicit_scope_allows_unrelated_new_file(self):
        self.ready_snapshot()
        infra.snapshot(self.root, "p1", "protocol", ["protocol/design.md"])
        (self.root / "runs/new.log").write_text("new run", encoding="utf-8")
        self.assertTrue(infra.verify(self.root, "snapshots/p1.json")["ok"])

    def test_snapshot_rejects_named_secret(self):
        self.ready_snapshot()
        (self.root / ".env").write_text("DUMMY_FIXTURE_ONLY", encoding="utf-8")
        with self.assertRaises(ValueError):
            infra.snapshot(self.root, "p1", "protocol", [".env"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
