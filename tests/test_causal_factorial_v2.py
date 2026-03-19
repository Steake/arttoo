from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arc_epistemic.eval.causal_v2 import (
    build_freeze_manifest,
    build_subset_analyses,
    build_task_level_attribution_v2,
    categorize_task_attribution_v2,
    count_uncertainty_driven_reorders,
    detect_ranking_conflict,
    evaluate_conviction,
    load_manifest,
    run_frozen_factorial_v2,
    run_native_factorial_v2,
    subset_task_ids,
)
from arc_epistemic.eval.fixtures import discover_splits, load_fixture_split


class FreezeManifestTests(unittest.TestCase):
    def test_freeze_manifest_integrity(self) -> None:
        payload = build_freeze_manifest(
            "data/splits/blind_holdout_v3.json",
            "data/splits/blind_holdout_v3_manifest.json",
            generated_at_utc="2026-03-19T00:00:00+00:00",
        )
        manifest = json.loads(Path("data/splits/blind_holdout_v3_manifest.json").read_text())
        split = json.loads(Path("data/splits/blind_holdout_v3.json").read_text())
        self.assertEqual(payload["task_count"], 24)
        self.assertEqual(payload["task_count"], len(manifest["entries"]))
        self.assertEqual(payload["task_count"], len(split["task_ids"]))
        self.assertEqual(payload["family_counts"], {
            "control": 8,
            "ranking_conflict": 8,
            "refinement_composition": 8,
        })


class SubsetExtractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.entries = load_manifest("data/splits/blind_holdout_v3_manifest.json")

    def test_split_discovery_includes_v3(self) -> None:
        self.assertIn("blind_holdout_v3", discover_splits("data/splits"))

    def test_subset_counts_match_manifest(self) -> None:
        self.assertEqual(len(subset_task_ids(self.entries, None)), 24)
        self.assertEqual(len(subset_task_ids(self.entries, "ranking_conflict")), 8)
        self.assertEqual(len(subset_task_ids(self.entries, "refinement_composition")), 8)
        self.assertEqual(len(subset_task_ids(self.entries, "control")), 8)


class UtilityFunctionTests(unittest.TestCase):
    def test_ranking_conflict_detection(self) -> None:
        self.assertTrue(detect_ranking_conflict({"ranking_conflict_occurred": True}))
        self.assertFalse(detect_ranking_conflict({"ranking_conflict_occurred": False}))

    def test_uncertainty_reorder_counting(self) -> None:
        counts = count_uncertainty_driven_reorders(
            [
                {
                    "uncertainty_changed_winner": True,
                    "uncertainty_improved_correctness": True,
                    "uncertainty_hurt_correctness": False,
                    "condition_correctness": {"C11": True},
                    "uncertainty_aware_top_candidate": {"uncertainty": 0.5},
                },
                {
                    "uncertainty_changed_winner": True,
                    "uncertainty_improved_correctness": False,
                    "uncertainty_hurt_correctness": True,
                    "condition_correctness": {"C11": False},
                    "uncertainty_aware_top_candidate": {"uncertainty": 0.0},
                },
            ]
        )
        self.assertEqual(counts["winner_changes"], 2)
        self.assertEqual(counts["improved"], 1)
        self.assertEqual(counts["hurt"], 1)
        self.assertEqual(counts["solved_with_nonzero_winning_uncertainty"], 1)

    def test_task_attribution_v2_categories(self) -> None:
        self.assertEqual(categorize_task_attribution_v2(False, True, False, True), "refinement_only_gain")
        self.assertEqual(categorize_task_attribution_v2(False, False, True, True), "uncertainty_only_gain")
        self.assertEqual(categorize_task_attribution_v2(False, False, False, True), "synergy_gain")
        self.assertEqual(categorize_task_attribution_v2(True, True, True, True), "control_all_agree")
        self.assertEqual(categorize_task_attribution_v2(False, False, False, False), "persistent_failure")
        self.assertEqual(categorize_task_attribution_v2(True, False, True, False), "refinement_hurt")
        self.assertEqual(categorize_task_attribution_v2(False, True, False, False), "uncertainty_hurt")

    def test_conviction_threshold_logic(self) -> None:
        self.assertEqual(evaluate_conviction("proven", True, True), "high")
        self.assertEqual(evaluate_conviction("supported_but_not_isolated", False, True), "moderate")
        self.assertEqual(evaluate_conviction("still_inconclusive", False, False), "low")


class FrozenPoolConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        fixtures = load_fixture_split("data/fixtures", split="blind_holdout_v3")[:1]
        cls.fixture = fixtures[0]
        cls.native = run_native_factorial_v2(fixtures, split="blind_holdout_v3")
        cls.frozen = run_frozen_factorial_v2(fixtures, split="blind_holdout_v3")
        cls.entries = [
            entry
            for entry in load_manifest("data/splits/blind_holdout_v3_manifest.json")
            if entry.task_id == cls.fixture.task_id
        ]

    def test_frozen_pool_sizes_are_condition_consistent(self) -> None:
        task_id = self.fixture.task_id
        c00 = self.frozen["C00"][task_id]
        c01 = self.frozen["C01"][task_id]
        c10 = self.frozen["C10"][task_id]
        c11 = self.frozen["C11"][task_id]
        self.assertEqual(c00["primitive_pool_size"], c01["primitive_pool_size"])
        self.assertEqual(c10["full_pool_size"], c11["full_pool_size"])
        self.assertEqual(c00["full_pool_size"], c10["full_pool_size"])

    def test_subset_analysis_runs(self) -> None:
        subset = build_subset_analyses(self.entries, self.native, self.frozen, n_bootstrap=50, seed=7)
        self.assertIn("all_blind_holdout_v3", subset)
        self.assertEqual(subset["all_blind_holdout_v3"]["task_count"], 1)

    def test_task_level_attribution_contains_telemetry(self) -> None:
        rows = build_task_level_attribution_v2(self.entries, self.native, self.frozen)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertIn("point_estimate_first_pass_ordering", row)
        self.assertIn("uncertainty_aware_top_candidate", row)
        self.assertIn("runtime_ms_by_condition", row)


class ToolSmokeTests(unittest.TestCase):
    def test_v2_tools_smoke(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            commands = [
                ["python", "tools/generate_freeze_manifest.py", "--json", str(tmp_path / "freeze.json"), "--markdown", str(tmp_path / "freeze.md")],
                ["python", "tools/run_causal_factorial_v2.py", "--tasks", "data/fixtures", "--reports-dir", str(tmp_path), "--n-bootstrap", "50", "--seed", "7"],
                ["python", "tools/generate_uncertainty_causal_analysis.py", "--input", str(tmp_path / "causal_factorial_v2.json"), "--json", str(tmp_path / "uncertainty.json"), "--markdown", str(tmp_path / "uncertainty.md")],
                ["python", "tools/generate_thesis_final_attribution_summary.py", "--causal-input", str(tmp_path / "causal_factorial_v2.json"), "--freeze-input", str(tmp_path / "freeze.json"), "--json", str(tmp_path / "summary.json"), "--markdown", str(tmp_path / "summary.md")],
            ]
            for command in commands:
                result = subprocess.run(command, cwd=repo_root, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, msg=result.stderr)
            for name in [
                "freeze.json",
                "freeze.md",
                "causal_factorial_v2.json",
                "causal_factorial_v2.md",
                "task_level_attribution_v2.json",
                "task_level_attribution_v2.md",
                "causal_verdict_v2.json",
                "causal_verdict_v2.md",
                "uncertainty.json",
                "uncertainty.md",
                "summary.json",
                "summary.md",
            ]:
                self.assertTrue((tmp_path / name).exists(), f"missing artifact {name}")


if __name__ == "__main__":
    unittest.main()
