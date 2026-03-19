from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arc_epistemic.eval.epistemic_redesign import (
    build_benchmark_quality_gates,
    build_efficiency_gating_analysis,
    build_epistemic_process_verdict,
    build_freeze_manifest,
    build_output_selection_causal_analysis,
    build_task_level_epistemic_attribution,
    freeze_manifest_markdown,
    load_manifest,
    run_frozen_experiment,
    run_native_experiment,
    summarize_experiment,
)
from arc_epistemic.eval.fixtures import discover_splits, load_fixture_split
from arc_epistemic.solver.output_competition import (
    aggregate_output_support,
    rank_output_classes,
    select_top_two_diversity_aware_output_classes,
)
from arc_epistemic.solver.solver import solve_task_with_diagnostics
from arc_epistemic.eval.epistemic_redesign import METHOD_CONFIGS_NATIVE


class BlindHoldoutV5ManifestTests(unittest.TestCase):
    def test_freeze_manifest_integrity(self) -> None:
        payload = build_freeze_manifest(
            "blind_holdout_v5",
            "data/splits/blind_holdout_v5.json",
            "data/splits/blind_holdout_v5_manifest.json",
            generated_at_utc="2026-03-19T00:00:00+00:00",
        )
        self.assertEqual(payload["task_count"], 36)
        self.assertEqual(payload["family_counts"], {
            "control": 8,
            "diversity_sensitive": 8,
            "refinement_composition": 8,
            "selector_divergence": 12,
        })
        self.assertIn("blind_holdout_v5", freeze_manifest_markdown(payload))

    def test_split_discovery_includes_v5(self) -> None:
        self.assertIn("blind_holdout_v5", discover_splits("data/splits"))


class OutputDiversitySelectionTests(unittest.TestCase):
    def test_diversity_selector_prefers_diverse_coalition_on_v5_fixture(self) -> None:
        fixture = load_fixture_split("data/fixtures", split="blind_holdout_v5")[12]  # first diversity-sensitive task
        result = solve_task_with_diagnostics(fixture.task, config=METHOD_CONFIGS_NATIVE["M3"])
        ranked = result.ranked_hypotheses
        test_input = fixture.task.test[0].input
        mass_supports = aggregate_output_support(ranked, test_input)
        diversity_winner, _, diversity_supports = select_top_two_diversity_aware_output_classes(ranked, test_input)
        self.assertGreaterEqual(len(mass_supports), 2)
        self.assertIsNotNone(diversity_winner)
        self.assertGreaterEqual(diversity_supports[0].family_diversity_count, 1)
        self.assertIn("diversity_adjusted_mass", rank_output_classes(ranked, test_input, strategy="diversity")[0].__dict__)


class EpistemicRedesignExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixtures = load_fixture_split("data/fixtures", split="blind_holdout_v5")
        cls.entries = load_manifest("data/splits/blind_holdout_v5_manifest.json")
        cls.freeze_manifest = build_freeze_manifest(
            "blind_holdout_v5",
            "data/splits/blind_holdout_v5.json",
            "data/splits/blind_holdout_v5_manifest.json",
            generated_at_utc="2026-03-19T00:00:00+00:00",
        )
        cls.frozen = summarize_experiment(run_frozen_experiment(cls.fixtures, cls.entries, split="blind_holdout_v5", freeze_manifest=cls.freeze_manifest))
        cls.native = summarize_experiment(run_native_experiment(cls.fixtures, cls.entries, split="blind_holdout_v5", freeze_manifest=cls.freeze_manifest))
        cls.quality = build_benchmark_quality_gates(cls.frozen, cls.native)
        cls.causal = build_output_selection_causal_analysis(cls.frozen, cls.native, n_bootstrap=100, seed=7)
        cls.efficiency = build_efficiency_gating_analysis(cls.frozen, cls.native, n_bootstrap=100, seed=7)
        cls.task_level = build_task_level_epistemic_attribution(cls.frozen, cls.native)
        cls.verdict = build_epistemic_process_verdict(cls.frozen, cls.native, cls.quality, cls.causal, cls.efficiency, cls.task_level)

    def test_quality_gates_pass(self) -> None:
        self.assertTrue(self.quality["methodology_valid"])
        self.assertTrue(self.quality["frozen"]["selector_divergence"]["valid"])
        self.assertTrue(self.quality["native"]["diversity_sensitive"]["valid"])

    def test_selector_divergence_and_diversity_are_exercised(self) -> None:
        self.assertGreater(self.quality["native"]["selector_divergence"]["metrics"]["selector_disagreement_m0_m2"], 0)
        self.assertGreater(self.quality["native"]["diversity_sensitive"]["metrics"]["selector_disagreement_m2_m3"], 0)

    def test_verdict_status_is_honest_and_explicit(self) -> None:
        self.assertIn(self.verdict["status"], {
            "proven_strongly",
            "supported_but_not_isolated",
            "inconclusive",
            "falsified_on_this_benchmark",
            "methodologically_inconclusive",
        })
        self.assertIn("uncertainty_causal_effect", self.verdict)
        self.assertIn("efficiency_gain", self.verdict)

    def test_task_level_attribution_contains_requested_categories(self) -> None:
        categories = {row["category"] for row in self.task_level}
        self.assertIn("output_mass_only_gain", categories)
        self.assertIn("diversity_aware_only_gain", categories)

    def test_native_selector_gain_is_positive(self) -> None:
        contrast = self.causal["native"]["selector_divergence"]["m2_vs_m0"]
        self.assertGreater(contrast["estimate"], 0.0)


class ToolSmokeTests(unittest.TestCase):
    def test_redesign_tools_smoke(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            commands = [
                [
                    "python",
                    "tools/run_epistemic_method_redesign_experiment.py",
                    "--tasks",
                    "data/fixtures",
                    "--split",
                    "blind_holdout_v5",
                    "--split-path",
                    "data/splits/blind_holdout_v5.json",
                    "--manifest",
                    "data/splits/blind_holdout_v5_manifest.json",
                    "--reports-dir",
                    str(tmp_path),
                    "--n-bootstrap",
                    "50",
                    "--seed",
                    "7",
                ],
                [
                    "python",
                    "tools/generate_benchmark_quality_gates.py",
                    "--input",
                    str(tmp_path / "benchmark_quality_gates.json"),
                    "--json",
                    str(tmp_path / "benchmark_quality_gates_copy.json"),
                    "--markdown",
                    str(tmp_path / "benchmark_quality_gates_copy.md"),
                ],
                [
                    "python",
                    "tools/generate_epistemic_process_verdict.py",
                    "--input",
                    str(tmp_path / "epistemic_process_verdict.json"),
                    "--json",
                    str(tmp_path / "epistemic_process_verdict_copy.json"),
                    "--markdown",
                    str(tmp_path / "epistemic_process_verdict_copy.md"),
                ],
            ]
            for command in commands:
                completed = subprocess.run(command, cwd=repo_root, capture_output=True, text=True)
                self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            for name in [
                "blind_holdout_v5_freeze_manifest.json",
                "epistemic_method_redesign_frozen.json",
                "epistemic_method_redesign_native.json",
                "benchmark_quality_gates.json",
                "output_selection_causal_analysis.json",
                "efficiency_gating_analysis.json",
                "task_level_epistemic_attribution.json",
                "epistemic_process_verdict.json",
                "method_setup_experiment_summary.json",
                "benchmark_quality_gates_copy.json",
                "epistemic_process_verdict_copy.json",
            ]:
                self.assertTrue((tmp_path / name).exists(), f"missing artifact {name}")


if __name__ == "__main__":
    unittest.main()
