"""2×2 factorial causal attribution experiment.

Factors
-------
  R: use_refinement         (0 = off, 1 = on)
  E: use_epistemic_scoring  (0 = off, 1 = on)

Conditions (C{R}{E})
--------------------
  C00: R=0, E=0  →  PRIMITIVE_BASELINE_CONFIG
  C10: R=1, E=0  →  COMPOSITION_BASELINE_CONFIG
  C01: R=0, E=1  →  EPISTEMIC_NO_REFINEMENT_CONFIG
  C11: R=1, E=1  →  FULL_COAGENCY_CONFIG

Five pairwise contrasts + one interaction term are computed and returned
with paired bootstrap 95 % CIs and McNemar exact tests.
"""
from __future__ import annotations

import json
import math
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from arc_epistemic.eval.analysis import _case_diagnostic
from arc_epistemic.eval.fixtures import FixtureTask
from arc_epistemic.solver.agents import (
    COMPOSITION_BASELINE_CONFIG,
    EPISTEMIC_NO_REFINEMENT_CONFIG,
    FULL_COAGENCY_CONFIG,
    PRIMITIVE_BASELINE_CONFIG,
    SolverConfig,
)

# Ordered conditions: C{refinement_bit}{epistemic_bit}
CONDITION_LABELS: tuple[str, ...] = ("C00", "C10", "C01", "C11")
CONDITION_CONFIGS: dict[str, SolverConfig] = {
    "C00": PRIMITIVE_BASELINE_CONFIG,
    "C10": COMPOSITION_BASELINE_CONFIG,
    "C01": EPISTEMIC_NO_REFINEMENT_CONFIG,
    "C11": FULL_COAGENCY_CONFIG,
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FrozenCandidatePool:
    """Snapshot of the hypothesis pool generated for one task under one condition."""

    task_id: str
    condition: str
    generated_candidates: tuple[str, ...]
    refined_candidates: tuple[str, ...]
    top_hypothesis: str
    top_score: float


@dataclass(frozen=True)
class TaskOutcome:
    task_id: str
    condition: str
    solved: bool
    winning_hypothesis: str
    winning_score: float
    failure_class: str | None
    candidate_pool: FrozenCandidatePool


@dataclass(frozen=True)
class ConditionSummary:
    condition: str
    config_name: str
    task_count: int
    solve_count: int
    solve_rate: float
    outcomes: tuple[TaskOutcome, ...]


@dataclass(frozen=True)
class FactorialResult:
    split: str
    task_ids: tuple[str, ...]
    conditions: dict[str, ConditionSummary]
    generated_at_utc: str


@dataclass(frozen=True)
class Contrast:
    """One pairwise causal contrast between two conditions."""

    name: str
    description: str
    condition_a: str
    condition_b: str
    solve_rate_a: float
    solve_rate_b: float
    estimate: float       # solve_rate_b − solve_rate_a
    ci_lower: float
    ci_upper: float
    n_concordant: int     # both solve or both fail
    n_ab: int             # A solves, B fails
    n_ba: int             # B solves, A fails
    mcnemar_statistic: float | None
    mcnemar_p: float | None


@dataclass(frozen=True)
class TaskAttribution:
    """Per-task causal category derived from the 4-condition solve pattern."""

    task_id: str
    c00: bool
    c10: bool
    c01: bool
    c11: bool
    category: str


@dataclass(frozen=True)
class CausalVerdict:
    dominant_factor: str   # "refinement" | "epistemic" | "interaction" | "both_additive" | "neither"
    refinement_main_effect: float
    epistemic_main_effect: float
    interaction_effect: float
    conclusion: str


@dataclass(frozen=True)
class CausalContrasts:
    split: str
    factorial_result: FactorialResult
    contrasts: tuple[Contrast, ...]
    interaction: Contrast
    task_attributions: tuple[TaskAttribution, ...]
    verdict: CausalVerdict
    generated_at_utc: str


# ---------------------------------------------------------------------------
# Statistical helpers (no third-party dependencies)
# ---------------------------------------------------------------------------


def _mcnemar_test(
    outcomes_a: tuple[bool, ...],
    outcomes_b: tuple[bool, ...],
) -> tuple[float | None, float | None]:
    """McNemar chi-squared test with continuity correction (df=1).

    Returns (statistic, p_value) or (None, None) when no discordant pairs exist.
    """
    b = sum(1 for a, bv in zip(outcomes_a, outcomes_b) if a and not bv)
    c = sum(1 for a, bv in zip(outcomes_a, outcomes_b) if not a and bv)
    if b + c == 0:
        return (None, None)
    statistic = (abs(b - c) - 1.0) ** 2 / (b + c)
    # chi2(df=1) survival function = erfc(sqrt(x/2))
    p_value = math.erfc(math.sqrt(statistic / 2.0))
    return (round(statistic, 6), round(p_value, 6))


def _paired_bootstrap_ci(
    outcomes_a: tuple[bool, ...],
    outcomes_b: tuple[bool, ...],
    n_bootstrap: int = 2000,
    seed: int = 42,
    alpha: float = 0.05,
) -> tuple[float, float]:
    """Paired percentile bootstrap 95 % CI for the contrast (mean_b - mean_a)."""
    n = len(outcomes_a)
    if n == 0:
        return (0.0, 0.0)
    diffs = [int(b) - int(a) for a, b in zip(outcomes_a, outcomes_b)]
    rng = random.Random(seed)
    boot_means: list[float] = []
    for _ in range(n_bootstrap):
        sample = [diffs[rng.randrange(n)] for _ in range(n)]
        boot_means.append(sum(sample) / n)
    boot_means.sort()
    lo_idx = max(0, int(math.floor(alpha / 2.0 * n_bootstrap)))
    hi_idx = min(n_bootstrap - 1, int(math.ceil((1.0 - alpha / 2.0) * n_bootstrap)) - 1)
    return (round(boot_means[lo_idx], 4), round(boot_means[hi_idx], 4))


def _bootstrap_ci_interaction(
    c00: tuple[bool, ...],
    c10: tuple[bool, ...],
    c01: tuple[bool, ...],
    c11: tuple[bool, ...],
    n_bootstrap: int = 2000,
    seed: int = 42,
    alpha: float = 0.05,
) -> tuple[float, float]:
    """Bootstrap CI for the R×E interaction: (C11 - C01) - (C10 - C00)."""
    n = len(c00)
    if n == 0:
        return (0.0, 0.0)
    interactions = [int(d11) - int(d01) - int(d10) + int(d00) for d00, d10, d01, d11 in zip(c00, c10, c01, c11)]
    rng = random.Random(seed)
    boot_means: list[float] = []
    for _ in range(n_bootstrap):
        sample = [interactions[rng.randrange(n)] for _ in range(n)]
        boot_means.append(sum(sample) / n)
    boot_means.sort()
    lo_idx = max(0, int(math.floor(alpha / 2.0 * n_bootstrap)))
    hi_idx = min(n_bootstrap - 1, int(math.ceil((1.0 - alpha / 2.0) * n_bootstrap)) - 1)
    return (round(boot_means[lo_idx], 4), round(boot_means[hi_idx], 4))


# ---------------------------------------------------------------------------
# Task attribution
# ---------------------------------------------------------------------------


def _categorize_task(c00: bool, c10: bool, c01: bool, c11: bool) -> str:
    """Map the 4-bit solve pattern to a causal category label."""
    if c00 and c10 and c01 and c11:
        return "all_solve"
    if not c00 and not c10 and not c01 and not c11:
        return "none_solve"
    if c00:
        if not c10 and not c01 and not c11:
            return "baseline_only"
        return "trivially_solved"
    # Baseline (C00) fails from here on.
    if c10 and c01 and c11:
        return "either_factor_sufficient"
    if c10 and not c01 and c11:
        return "refinement_resolves"
    if c01 and not c10 and c11:
        return "epistemic_resolves"
    if c11 and not c10 and not c01:
        return "synergy_required"
    if c10 and not c01 and not c11:
        return "refinement_only_partial"
    if c01 and not c10 and not c11:
        return "epistemic_only_partial"
    if c10 and c01 and not c11:
        return "factors_conflict_in_combination"
    return "mixed_pattern"


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------


def _build_conclusion(
    dominant: str,
    me_r: float,
    me_e: float,
    interaction: float,
    c00_rate: float,
    c11_rate: float,
) -> str:
    lift = round(c11_rate - c00_rate, 4)
    if dominant == "neither":
        return (
            f"Neither factor dominates (ME_R={me_r:+.3f}, ME_E={me_e:+.3f}). "
            f"Full-vs-primitive lift is {lift:+.3f}."
        )
    if dominant == "refinement":
        return (
            f"Refinement (R) is the dominant causal factor (ME_R={me_r:+.3f} vs ME_E={me_e:+.3f}). "
            f"Adding bounded composition explains most of the {lift:+.3f} full-vs-primitive lift."
        )
    if dominant == "epistemic":
        return (
            f"Epistemic scoring (E) is the dominant causal factor (ME_E={me_e:+.3f} vs ME_R={me_r:+.3f}). "
            f"Uncertainty-aware ranking explains most of the {lift:+.3f} full-vs-primitive lift."
        )
    if dominant == "interaction":
        return (
            f"The R×E interaction dominates (interaction={interaction:+.3f}). "
            f"Neither factor alone accounts for the {lift:+.3f} lift; they are synergistic."
        )
    return (
        f"Both factors contribute additively (ME_R={me_r:+.3f}, ME_E={me_e:+.3f}, "
        f"interaction={interaction:+.3f}). Full-vs-primitive lift is {lift:+.3f}."
    )


def _compute_verdict(
    c00_rate: float,
    c10_rate: float,
    c01_rate: float,
    c11_rate: float,
    interaction_estimate: float,
) -> CausalVerdict:
    me_r = ((c10_rate + c11_rate) - (c00_rate + c01_rate)) / 2.0
    me_e = ((c01_rate + c11_rate) - (c00_rate + c10_rate)) / 2.0
    abs_r = abs(me_r)
    abs_e = abs(me_e)
    abs_i = abs(interaction_estimate)
    threshold = 0.05
    if abs_r < threshold and abs_e < threshold and abs_i < threshold:
        dominant = "neither"
    elif abs_i > abs_r and abs_i > abs_e:
        dominant = "interaction"
    elif abs_r >= abs_e and abs_r >= threshold:
        dominant = "refinement"
    elif abs_e > abs_r and abs_e >= threshold:
        dominant = "epistemic"
    else:
        dominant = "both_additive"
    conclusion = _build_conclusion(dominant, me_r, me_e, interaction_estimate, c00_rate, c11_rate)
    return CausalVerdict(
        dominant_factor=dominant,
        refinement_main_effect=round(me_r, 4),
        epistemic_main_effect=round(me_e, 4),
        interaction_effect=round(interaction_estimate, 4),
        conclusion=conclusion,
    )


# ---------------------------------------------------------------------------
# Core experiment runner
# ---------------------------------------------------------------------------


def run_factorial_experiment(
    fixtures: list[FixtureTask],
    split: str = "all",
) -> FactorialResult:
    """Run all 4 factorial conditions on every fixture and return a FactorialResult."""
    outcomes_by_condition: dict[str, list[TaskOutcome]] = {label: [] for label in CONDITION_LABELS}
    task_ids = tuple(f.task_id for f in fixtures)

    for fixture in fixtures:
        for label in CONDITION_LABELS:
            config = CONDITION_CONFIGS[label]
            case_diag, result = _case_diagnostic(fixture, config, split=split)
            pool = FrozenCandidatePool(
                task_id=fixture.task_id,
                condition=label,
                generated_candidates=result.loop_diagnostics.generated_candidates,
                refined_candidates=result.loop_diagnostics.refined_candidates,
                top_hypothesis=case_diag.winning_hypothesis,
                top_score=case_diag.winning_score,
            )
            outcomes_by_condition[label].append(
                TaskOutcome(
                    task_id=fixture.task_id,
                    condition=label,
                    solved=case_diag.success_attempt_1,
                    winning_hypothesis=case_diag.winning_hypothesis,
                    winning_score=case_diag.winning_score,
                    failure_class=case_diag.failure_primary_class,
                    candidate_pool=pool,
                )
            )

    n = len(fixtures)
    conditions: dict[str, ConditionSummary] = {}
    for label in CONDITION_LABELS:
        outcomes = outcomes_by_condition[label]
        solves = sum(1 for o in outcomes if o.solved)
        conditions[label] = ConditionSummary(
            condition=label,
            config_name=CONDITION_CONFIGS[label].name,
            task_count=n,
            solve_count=solves,
            solve_rate=solves / n if n else 0.0,
            outcomes=tuple(outcomes),
        )

    return FactorialResult(
        split=split,
        task_ids=task_ids,
        conditions=conditions,
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
    )


# ---------------------------------------------------------------------------
# Contrast computation
# ---------------------------------------------------------------------------


def _build_contrast(
    name: str,
    description: str,
    label_a: str,
    label_b: str,
    result: FactorialResult,
    n_bootstrap: int,
    seed: int,
) -> Contrast:
    cond_a = result.conditions[label_a]
    cond_b = result.conditions[label_b]
    outcomes_a = tuple(o.solved for o in cond_a.outcomes)
    outcomes_b = tuple(o.solved for o in cond_b.outcomes)
    estimate = cond_b.solve_rate - cond_a.solve_rate
    ci_lo, ci_hi = _paired_bootstrap_ci(outcomes_a, outcomes_b, n_bootstrap=n_bootstrap, seed=seed)
    stat, pval = _mcnemar_test(outcomes_a, outcomes_b)
    n_ab = sum(1 for a, b in zip(outcomes_a, outcomes_b) if a and not b)
    n_ba = sum(1 for a, b in zip(outcomes_a, outcomes_b) if not a and b)
    n_conc = len(outcomes_a) - n_ab - n_ba
    return Contrast(
        name=name,
        description=description,
        condition_a=label_a,
        condition_b=label_b,
        solve_rate_a=round(cond_a.solve_rate, 4),
        solve_rate_b=round(cond_b.solve_rate, 4),
        estimate=round(estimate, 4),
        ci_lower=ci_lo,
        ci_upper=ci_hi,
        n_concordant=n_conc,
        n_ab=n_ab,
        n_ba=n_ba,
        mcnemar_statistic=stat,
        mcnemar_p=pval,
    )


def compute_causal_contrasts(
    result: FactorialResult,
    n_bootstrap: int = 2000,
    seed: int = 42,
) -> CausalContrasts:
    """Compute all causal contrasts, task attributions, and the causal verdict."""
    c00 = result.conditions["C00"]
    c10 = result.conditions["C10"]
    c01 = result.conditions["C01"]
    c11 = result.conditions["C11"]

    contrasts = (
        _build_contrast("c10_vs_c00", "Refinement without epistemic scoring (C10 − C00)", "C00", "C10", result, n_bootstrap, seed),
        _build_contrast("c01_vs_c00", "Epistemic scoring without refinement (C01 − C00)", "C00", "C01", result, n_bootstrap, seed),
        _build_contrast("c11_vs_c10", "Epistemic scoring given refinement (C11 − C10)", "C10", "C11", result, n_bootstrap, seed),
        _build_contrast("c11_vs_c01", "Refinement given epistemic scoring (C11 − C01)", "C01", "C11", result, n_bootstrap, seed),
        _build_contrast("c11_vs_c00", "Full co-agency vs primitive baseline (C11 − C00)", "C00", "C11", result, n_bootstrap, seed),
    )

    oc00 = tuple(o.solved for o in c00.outcomes)
    oc10 = tuple(o.solved for o in c10.outcomes)
    oc01 = tuple(o.solved for o in c01.outcomes)
    oc11 = tuple(o.solved for o in c11.outcomes)
    interaction_estimate = (c11.solve_rate - c01.solve_rate) - (c10.solve_rate - c00.solve_rate)
    ci_lo, ci_hi = _bootstrap_ci_interaction(oc00, oc10, oc01, oc11, n_bootstrap=n_bootstrap, seed=seed)
    interaction = Contrast(
        name="interaction_RxE",
        description="R×E interaction: (C11 − C01) − (C10 − C00)",
        condition_a="C01",
        condition_b="C10",
        solve_rate_a=round(c01.solve_rate, 4),
        solve_rate_b=round(c10.solve_rate, 4),
        estimate=round(interaction_estimate, 4),
        ci_lower=ci_lo,
        ci_upper=ci_hi,
        n_concordant=sum(1 for d00, d10, d01, d11 in zip(oc00, oc10, oc01, oc11) if d11 - d01 == d10 - d00),
        n_ab=sum(1 for d00, d10, d01, d11 in zip(oc00, oc10, oc01, oc11) if (d11 - d01) < (d10 - d00)),
        n_ba=sum(1 for d00, d10, d01, d11 in zip(oc00, oc10, oc01, oc11) if (d11 - d01) > (d10 - d00)),
        mcnemar_statistic=None,
        mcnemar_p=None,
    )

    task_attributions = tuple(
        TaskAttribution(
            task_id=task_id,
            c00=oc00[i],
            c10=oc10[i],
            c01=oc01[i],
            c11=oc11[i],
            category=_categorize_task(oc00[i], oc10[i], oc01[i], oc11[i]),
        )
        for i, task_id in enumerate(result.task_ids)
    )

    verdict = _compute_verdict(
        c00.solve_rate, c10.solve_rate, c01.solve_rate, c11.solve_rate,
        interaction_estimate,
    )

    return CausalContrasts(
        split=result.split,
        factorial_result=result,
        contrasts=contrasts,
        interaction=interaction,
        task_attributions=task_attributions,
        verdict=verdict,
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
    )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def causal_markdown(contrasts: CausalContrasts) -> str:
    fr = contrasts.factorial_result
    lines: list[str] = []

    lines.append("# 2×2 Factorial Causal Attribution")
    lines.append("")
    lines.append(f"**Split**: `{fr.split}` | **Tasks**: {len(fr.task_ids)} | **Generated**: {contrasts.generated_at_utc}")
    lines.append("")
    lines.append("## Factorial Design")
    lines.append("")
    lines.append("| Condition | use_refinement | use_epistemic_scoring | Config |")
    lines.append("| --- | --- | --- | --- |")
    for label in CONDITION_LABELS:
        cfg = CONDITION_CONFIGS[label]
        lines.append(f"| {label} | {cfg.use_refinement} | {cfg.use_epistemic_scoring} | `{cfg.name}` |")
    lines.append("")

    lines.append("## Condition Solve Rates")
    lines.append("")
    lines.append("| Condition | Solved | Total | Solve Rate |")
    lines.append("| --- | --- | --- | --- |")
    for label in CONDITION_LABELS:
        cs = fr.conditions[label]
        lines.append(f"| {label} | {cs.solve_count} | {cs.task_count} | {cs.solve_rate:.3f} |")
    lines.append("")

    v = contrasts.verdict
    lines.append("## Causal Verdict")
    lines.append("")
    lines.append(f"**Dominant factor**: `{v.dominant_factor}`")
    lines.append("")
    lines.append(f"- Main effect of Refinement (ME_R): `{v.refinement_main_effect:+.4f}`")
    lines.append(f"- Main effect of Epistemic scoring (ME_E): `{v.epistemic_main_effect:+.4f}`")
    lines.append(f"- R×E Interaction: `{v.interaction_effect:+.4f}`")
    lines.append("")
    lines.append(f"> {v.conclusion}")
    lines.append("")

    lines.append("## Five Pairwise Contrasts")
    lines.append("")
    lines.append("| Contrast | Rate_A | Rate_B | Estimate | 95% CI | McNemar p |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for c in contrasts.contrasts:
        pval_str = f"{c.mcnemar_p:.4f}" if c.mcnemar_p is not None else "—"
        lines.append(
            f"| {c.name} | {c.solve_rate_a:.3f} | {c.solve_rate_b:.3f} "
            f"| {c.estimate:+.3f} | [{c.ci_lower:+.3f}, {c.ci_upper:+.3f}] "
            f"| {pval_str} |"
        )
    lines.append("")

    ic = contrasts.interaction
    lines.append("## R×E Interaction")
    lines.append("")
    lines.append(f"- Estimate: `{ic.estimate:+.4f}`")
    lines.append(f"- 95% Bootstrap CI: `[{ic.ci_lower:+.4f}, {ic.ci_upper:+.4f}]`")
    lines.append(f"- Concordant task pairs (no synergy/anti-synergy): `{ic.n_concordant}`")
    lines.append(f"- Synergistic pairs (R×E > 0): `{ic.n_ba}`")
    lines.append(f"- Anti-synergistic pairs (R×E < 0): `{ic.n_ab}`")
    lines.append("")

    lines.append("## Task Attribution")
    lines.append("")
    lines.append("| Task | C00 | C10 | C01 | C11 | Category |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for ta in contrasts.task_attributions:
        def fmt(b: bool) -> str:
            return "✓" if b else "✗"
        lines.append(
            f"| `{ta.task_id}` | {fmt(ta.c00)} | {fmt(ta.c10)} | {fmt(ta.c01)} | {fmt(ta.c11)} | `{ta.category}` |"
        )
    lines.append("")

    # Category summary
    from collections import Counter
    category_counts = Counter(ta.category for ta in contrasts.task_attributions)
    lines.append("### Attribution Category Counts")
    lines.append("")
    lines.append("| Category | Count |")
    lines.append("| --- | --- |")
    for cat, cnt in sorted(category_counts.items()):
        lines.append(f"| `{cat}` | {cnt} |")
    lines.append("")

    return "\n".join(lines)


def serialize_causal_json(contrasts: CausalContrasts) -> str:
    """Serialize CausalContrasts to a JSON string, omitting the nested FactorialResult outcomes."""

    def _safe(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: _safe(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [_safe(i) for i in obj]
        return obj

    data: dict[str, Any] = {
        "split": contrasts.split,
        "generated_at_utc": contrasts.generated_at_utc,
        "verdict": asdict(contrasts.verdict),
        "contrasts": [asdict(c) for c in contrasts.contrasts],
        "interaction": asdict(contrasts.interaction),
        "task_attributions": [asdict(ta) for ta in contrasts.task_attributions],
        "condition_solve_rates": {
            label: {
                "config_name": contrasts.factorial_result.conditions[label].config_name,
                "solve_count": contrasts.factorial_result.conditions[label].solve_count,
                "task_count": contrasts.factorial_result.conditions[label].task_count,
                "solve_rate": contrasts.factorial_result.conditions[label].solve_rate,
            }
            for label in CONDITION_LABELS
        },
        "task_ids": list(contrasts.factorial_result.task_ids),
    }
    return json.dumps(_safe(data), indent=2, sort_keys=True)
