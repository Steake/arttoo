"""Tests for the 2×2 factorial causal attribution module."""
from __future__ import annotations

import unittest

from arc_epistemic.eval.causal import (
    CausalContrasts,
    ConditionSummary,
    FactorialResult,
    TaskAttribution,
    TaskOutcome,
    _bootstrap_ci_interaction,
    _categorize_task,
    _compute_verdict,
    _mcnemar_test,
    _paired_bootstrap_ci,
    compute_causal_contrasts,
    run_factorial_experiment,
    causal_markdown,
    serialize_causal_json,
    CONDITION_LABELS,
)
from arc_epistemic.eval.fixtures import load_fixture_split


# ---------------------------------------------------------------------------
# Unit tests for statistical helpers
# ---------------------------------------------------------------------------


class McNemarTests(unittest.TestCase):
    def test_all_concordant_returns_none(self) -> None:
        a = (True, False, True, False)
        b = (True, False, True, False)
        stat, p = _mcnemar_test(a, b)
        self.assertIsNone(stat)
        self.assertIsNone(p)

    def test_all_discordant_one_direction_returns_significant(self) -> None:
        # With 10 all-discordant pairs (c=10, b=0), McNemar with continuity correction is significant
        outcomes_a = (False,) * 10
        outcomes_b = (True,) * 10
        stat, p = _mcnemar_test(outcomes_a, outcomes_b)
        self.assertIsNotNone(stat)
        self.assertIsNotNone(p)
        assert p is not None
        self.assertLess(p, 0.05)

    def test_single_discordant_pair_not_significant(self) -> None:
        outcomes_a = (True, True, True, False)
        outcomes_b = (True, True, True, True)
        stat, p = _mcnemar_test(outcomes_a, outcomes_b)
        self.assertIsNotNone(stat)
        self.assertIsNotNone(p)
        assert p is not None
        # With b+c=1, continuity correction gives 0, p=1
        self.assertGreater(p, 0.05)

    def test_symmetric_discordant_not_significant(self) -> None:
        # Equal discordant in both directions
        outcomes_a = (True, False, True, False)
        outcomes_b = (False, True, False, True)
        stat, p = _mcnemar_test(outcomes_a, outcomes_b)
        self.assertIsNotNone(stat)
        assert p is not None
        self.assertGreater(p, 0.05)


class BootstrapCITests(unittest.TestCase):
    def test_identical_outcomes_ci_includes_zero(self) -> None:
        outcomes = (True, False, True, False, True, False, True, False)
        lo, hi = _paired_bootstrap_ci(outcomes, outcomes, n_bootstrap=500)
        self.assertLessEqual(lo, 0.0)
        self.assertGreaterEqual(hi, 0.0)

    def test_b_always_better_ci_positive(self) -> None:
        outcomes_a = (False, False, False, False, False, False, False, False)
        outcomes_b = (True, True, True, True, True, True, True, True)
        lo, hi = _paired_bootstrap_ci(outcomes_a, outcomes_b, n_bootstrap=500)
        self.assertGreater(lo, 0.0)
        self.assertGreater(hi, 0.0)

    def test_empty_inputs_returns_zeros(self) -> None:
        lo, hi = _paired_bootstrap_ci((), (), n_bootstrap=100)
        self.assertEqual(lo, 0.0)
        self.assertEqual(hi, 0.0)

    def test_interaction_bootstrap_no_interaction(self) -> None:
        # When all tasks behave identically under interaction, CI should include 0
        c00 = (True, False, True, False)
        c10 = (True, True, True, True)
        c01 = (True, False, True, False)
        c11 = (True, True, True, True)
        lo, hi = _bootstrap_ci_interaction(c00, c10, c01, c11, n_bootstrap=500)
        self.assertLessEqual(lo, 0.001)
        self.assertGreaterEqual(hi, -0.001)


# ---------------------------------------------------------------------------
# Unit tests for task attribution categorization
# ---------------------------------------------------------------------------


class TaskAttributionTests(unittest.TestCase):
    def test_all_solve(self) -> None:
        self.assertEqual(_categorize_task(True, True, True, True), "all_solve")

    def test_none_solve(self) -> None:
        self.assertEqual(_categorize_task(False, False, False, False), "none_solve")

    def test_trivially_solved(self) -> None:
        # Baseline solves, plus others
        self.assertEqual(_categorize_task(True, True, False, True), "trivially_solved")

    def test_baseline_only(self) -> None:
        self.assertEqual(_categorize_task(True, False, False, False), "baseline_only")

    def test_refinement_resolves(self) -> None:
        self.assertEqual(_categorize_task(False, True, False, True), "refinement_resolves")

    def test_epistemic_resolves(self) -> None:
        self.assertEqual(_categorize_task(False, False, True, True), "epistemic_resolves")

    def test_synergy_required(self) -> None:
        self.assertEqual(_categorize_task(False, False, False, True), "synergy_required")

    def test_either_factor_sufficient(self) -> None:
        self.assertEqual(_categorize_task(False, True, True, True), "either_factor_sufficient")


# ---------------------------------------------------------------------------
# Unit tests for verdict computation
# ---------------------------------------------------------------------------


class VerdictTests(unittest.TestCase):
    def test_refinement_dominates(self) -> None:
        v = _compute_verdict(0.2, 0.8, 0.2, 0.8, 0.0)
        self.assertEqual(v.dominant_factor, "refinement")
        self.assertAlmostEqual(v.refinement_main_effect, 0.6)
        self.assertAlmostEqual(v.epistemic_main_effect, 0.0)

    def test_epistemic_dominates(self) -> None:
        v = _compute_verdict(0.2, 0.2, 0.8, 0.8, 0.0)
        self.assertEqual(v.dominant_factor, "epistemic")
        self.assertAlmostEqual(v.epistemic_main_effect, 0.6)
        self.assertAlmostEqual(v.refinement_main_effect, 0.0)

    def test_neither_when_small_effects(self) -> None:
        v = _compute_verdict(0.5, 0.5, 0.5, 0.5, 0.0)
        self.assertEqual(v.dominant_factor, "neither")

    def test_interaction_dominates(self) -> None:
        # Large interaction, small main effects
        # C00=0.0, C10=0.0, C01=0.0, C11=1.0 → interaction=1.0, ME_R=0.5, ME_E=0.5
        v = _compute_verdict(0.0, 0.0, 0.0, 1.0, 1.0)
        self.assertEqual(v.dominant_factor, "interaction")

    def test_conclusion_contains_factor_name(self) -> None:
        v = _compute_verdict(0.2, 0.8, 0.2, 0.8, 0.0)
        self.assertIn("Refinement", v.conclusion)


# ---------------------------------------------------------------------------
# Integration test: run factorial on blind_holdout_v2
# ---------------------------------------------------------------------------


class FactorialIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        fixtures = load_fixture_split("data/fixtures", split="blind_holdout_v2")
        cls.fixtures = fixtures
        cls.factorial_result = run_factorial_experiment(fixtures, split="blind_holdout_v2")
        cls.causal = compute_causal_contrasts(cls.factorial_result, n_bootstrap=200, seed=42)

    def test_factorial_result_has_all_conditions(self) -> None:
        for label in CONDITION_LABELS:
            self.assertIn(label, self.factorial_result.conditions)

    def test_task_count_matches_fixtures(self) -> None:
        n = len(self.fixtures)
        for label in CONDITION_LABELS:
            self.assertEqual(self.factorial_result.conditions[label].task_count, n)

    def test_five_contrasts_returned(self) -> None:
        self.assertEqual(len(self.causal.contrasts), 5)

    def test_interaction_contrast_present(self) -> None:
        self.assertEqual(self.causal.interaction.name, "interaction_RxE")

    def test_task_attributions_count_matches(self) -> None:
        n = len(self.fixtures)
        self.assertEqual(len(self.causal.task_attributions), n)

    def test_all_attribution_categories_valid(self) -> None:
        valid = {
            "all_solve", "none_solve", "trivially_solved", "baseline_only",
            "refinement_resolves", "epistemic_resolves", "synergy_required",
            "either_factor_sufficient", "refinement_only_partial",
            "epistemic_only_partial", "factors_conflict_in_combination",
            "mixed_pattern",
        }
        for ta in self.causal.task_attributions:
            self.assertIn(ta.category, valid, f"Unknown category: {ta.category} for {ta.task_id}")

    def test_solve_rates_in_unit_interval(self) -> None:
        for label in CONDITION_LABELS:
            rate = self.factorial_result.conditions[label].solve_rate
            self.assertGreaterEqual(rate, 0.0)
            self.assertLessEqual(rate, 1.0)

    def test_c00_solve_rate_less_than_c10(self) -> None:
        # Composition tasks require refinement; C10 should outperform C00
        c00_rate = self.factorial_result.conditions["C00"].solve_rate
        c10_rate = self.factorial_result.conditions["C10"].solve_rate
        self.assertLess(c00_rate, c10_rate)

    def test_contrast_estimates_match_solve_rate_diff(self) -> None:
        for c in self.causal.contrasts:
            expected = round(c.solve_rate_b - c.solve_rate_a, 4)
            self.assertAlmostEqual(c.estimate, expected, places=3)

    def test_verdict_has_dominant_factor(self) -> None:
        valid_factors = {"refinement", "epistemic", "interaction", "both_additive", "neither"}
        self.assertIn(self.causal.verdict.dominant_factor, valid_factors)

    def test_refinement_dominant_on_holdout_v2(self) -> None:
        # blind_holdout_v2 contains composition tasks that need refinement, not epistemic
        self.assertEqual(self.causal.verdict.dominant_factor, "refinement")

    def test_markdown_renders_without_error(self) -> None:
        md = causal_markdown(self.causal)
        self.assertIn("2×2 Factorial", md)
        self.assertIn("Causal Verdict", md)
        self.assertIn("Task Attribution", md)

    def test_json_serialization_roundtrip(self) -> None:
        import json
        json_str = serialize_causal_json(self.causal)
        data = json.loads(json_str)
        self.assertEqual(data["split"], "blind_holdout_v2")
        self.assertIn("verdict", data)
        self.assertIn("contrasts", data)
        self.assertEqual(len(data["contrasts"]), 5)

    def test_split_discovery_includes_v2(self) -> None:
        from arc_epistemic.eval.fixtures import discover_splits
        splits = discover_splits("data/splits")
        self.assertIn("blind_holdout_v2", splits)

    def test_v2_disjoint_from_existing_holdout(self) -> None:
        v2_ids = {f.task_id for f in load_fixture_split("data/fixtures", split="blind_holdout_v2")}
        bh_ids = {f.task_id for f in load_fixture_split("data/fixtures", split="blind_holdout")}
        dev_ids = {f.task_id for f in load_fixture_split("data/fixtures", split="dev")}
        self.assertTrue(v2_ids.isdisjoint(bh_ids))
        self.assertTrue(v2_ids.isdisjoint(dev_ids))


if __name__ == "__main__":
    unittest.main()
