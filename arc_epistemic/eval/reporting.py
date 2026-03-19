from __future__ import annotations

from pathlib import Path


def write_json(path: str | Path, payload: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(payload, encoding="utf-8")


def _table(headers: list[str], rows: list[list[str]]) -> str:
    parts = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        parts.append("| " + " | ".join(row) + " |")
    return "\n".join(parts)


def benchmark_markdown(result: dict[str, object]) -> str:
    aggregate = result["aggregate"]
    rows = [
        ["Split", str(result["split"])],
        ["Tasks", str(aggregate["task_count"])],
        ["Test cases", str(aggregate["test_case_count"])],
        ["Attempt 1 exact rate", f'{aggregate["attempt_1_exact_rate"]:.3f}'],
        ["Attempt 1 or 2 exact rate", f'{aggregate["attempt_1_or_2_exact_rate"]:.3f}'],
        ["Attempt 2 rescues", str(aggregate["attempt_2_rescue_count"])],
        ["Average runtime ms", f'{aggregate["average_runtime_ms"]:.3f}'],
        ["Max runtime ms", f'{aggregate["max_runtime_ms"]:.3f}'],
        ["Average generated hypotheses", f'{aggregate["average_generated_count"]:.2f}'],
        ["Average first-pass survivors", f'{aggregate["average_first_pass_survivor_count"]:.2f}'],
        ["Average refined hypotheses", f'{aggregate["average_refined_count"]:.2f}'],
        ["Average belief", f'{aggregate["average_belief"]:.3f}'],
        ["Average disbelief", f'{aggregate["average_disbelief"]:.3f}'],
        ["Average uncertainty", f'{aggregate["average_uncertainty"]:.3f}'],
        ["Average winning score", f'{aggregate["average_winning_score"]:.3f}'],
    ]
    failure_rows = [
        [name, str(count)]
        for name, count in sorted(aggregate["failure_primary_class_counts"].items())
    ] or [["none", "0"]]
    per_task_rows = [
        [
            item["task_id"],
            item["split"],
            "yes" if item["success_attempt_1"] else "no",
            "yes" if item["success_attempt_2"] else "no",
            f'{item["runtime_ms"]:.3f}',
            item["winning_hypothesis"] or "none",
            item["failure_primary_class"] or "",
        ]
        for item in result["per_task"]
    ]
    return "\n".join(
        [
            f"# Benchmark Report: {result['split']}",
            "",
            _table(["Metric", "Value"], rows),
            "",
            "## Failure Classes",
            "",
            _table(["Primary Class", "Count"], failure_rows),
            "",
            "## Per Task",
            "",
            _table(["Task", "Split", "Attempt 1", "Solved by Attempt 2", "Runtime ms", "Winner", "Failure"], per_task_rows),
        ]
    )


def ablation_markdown(result: dict[str, object]) -> str:
    rows = []
    baseline = result["baseline"]
    for name, payload in result["variants"].items():
        aggregate = payload["aggregate"]
        delta = result["deltas"].get(name, {})
        rows.append(
            [
                name,
                f'{aggregate["attempt_1_or_2_exact_rate"]:.3f}',
                f'{aggregate["average_runtime_ms"]:.3f}',
                f'{aggregate["average_winning_score"]:.3f}',
                f'{delta.get("solve_rate_delta_vs_baseline", 0.0):+.3f}',
                f'{delta.get("runtime_delta_ms_vs_baseline", 0.0):+.3f}',
                f'{delta.get("winning_score_delta_vs_baseline", 0.0):+.3f}',
            ]
        )
    return "\n".join(
        [
            f"# Ablation Report: {result['split']}",
            "",
            f"Baseline variant: `{baseline}`",
            "",
            _table(
                [
                    "Variant",
                    "Solve rate",
                    "Avg runtime ms",
                    "Mean winning score",
                    "Solve delta",
                    "Runtime delta",
                    "Score delta",
                ],
                rows,
            ),
        ]
    )


def determinism_markdown(result: dict[str, object]) -> str:
    rows = [
        ["Split", str(result["split"])],
        ["Runs", str(result["runs"])],
        ["Shuffled order checked", "yes" if result["checked_shuffled_order"] else "no"],
        ["Process-restart style invocations", "yes" if result["checked_process_restarts"] else "no"],
        ["Seed perturbations checked", "yes" if result["checked_seed_perturbations"] else "no"],
        ["Stable outputs", "yes" if result["stable_outputs"] else "no"],
        ["Stable rankings", "yes" if result["stable_rankings"] else "no"],
        ["Stable metrics", "yes" if result["stable_metrics"] else "no"],
    ]
    unstable = result["nondeterministic_tasks"] or ["none"]
    return "\n".join(
        [
            f"# Determinism Report: {result['split']}",
            "",
            _table(["Metric", "Value"], rows),
            "",
            "## Nondeterministic Tasks",
            "",
            "\n".join(f"- {task_id}" for task_id in unstable),
        ]
    )


def failures_markdown(result: dict[str, object]) -> str:
    rows = [
        [
            category,
            str(payload["count"]),
            ", ".join(payload["representatives"]),
            ", ".join(f"{key}:{value}" for key, value in sorted(payload["failure_tags"].items())),
            payload["suspected_root_cause"],
        ]
        for category, payload in sorted(result["failure_classes"].items())
    ] or [["none", "0", "", "", ""]]
    tag_rows = [[tag, str(count)] for tag, count in sorted(result["global_tag_counts"].items())] or [["none", "0"]]
    hygiene_rows = [
        ["Final task failures", str(result.get("final_task_failure_count", "n/a"))],
        ["Candidate transform failures", str(result.get("candidate_transform_failure_count", "n/a"))],
        ["Shape mismatch rejections (search)", str(result.get("shape_mismatch_rejection_count", "n/a"))],
        ["Unsupported pattern exits", str(result.get("unsupported_pattern_exit_count", "n/a"))],
    ]
    return "\n".join(
        [
            f"# Failure Summary: {result['split']}",
            "",
            _table(["Primary Class", "Count", "Representatives", "Tags", "Suspected Root Cause"], rows),
            "",
            "## Failure Category Breakdown",
            "",
            _table(["Category", "Count"], hygiene_rows),
            "",
            "## Global Tags",
            "",
            _table(["Tag", "Count"], tag_rows),
        ]
    )


def scorecard_markdown(result: dict[str, object]) -> str:
    rows = [[key, str(value)] for key, value in result.items()]
    return "\n".join([f"# Scorecard: {result['task_split']}", "", _table(["Field", "Value"], rows)])


def multi_split_summary_markdown(
    split_scorecards: dict[str, dict[str, object]],
) -> str:
    """Emit a concise multi-split comparison table. Never collapses into just 'all'."""
    ordered_splits = ["dev", "regression", "blind_holdout", "all"]
    rows = []
    for split in ordered_splits:
        if split not in split_scorecards:
            continue
        sc = split_scorecards[split]
        rows.append([
            split,
            f'{sc.get("exact_solve_rate", 0.0):.3f}',
            f'{sc.get("primitive_baseline_solve_rate", 0.0):.3f}',
            f'{sc.get("lift", 0.0):+.3f}',
            "yes" if sc.get("determinism_pass", False) else "no",
            str(sc.get("final_task_failure_count", sc.get("failure_counts_by_class", {}))),
            f'{sc.get("average_winning_uncertainty", sc.get("average_uncertainty", "n/a"))}',
        ])
    return "\n".join([
        "# Multi-Split Scorecard Summary",
        "",
        "> Split provenance: dev = tuning fixtures, regression = known-failure regressions, "
        "blind_holdout = unseen at tuning time, all = aggregate across all splits.",
        "",
        _table(
            ["Split", "Solve rate", "Baseline rate", "Lift", "Determinism", "Final failures", "Avg uncertainty"],
            rows,
        ),
    ])


def next_stage_summary_markdown(
    benchmark: dict[str, object],
    ablation: dict[str, object],
    failures: dict[str, object],
    determinism: dict[str, object],
) -> str:
    aggregate = benchmark["aggregate"]
    family_counts = aggregate["family_win_counts"]
    strongest = sorted(family_counts.items(), key=lambda item: (-item[1], item[0]))
    top_failures = sorted(
        failures["failure_classes"].items(),
        key=lambda item: (-item[1]["count"], item[0]),
    )
    full_variant = ablation["variants"]["full_epistemic_coagency"]["aggregate"]
    baseline_variant = ablation["variants"]["primitive_baseline_only"]["aggregate"]
    lift = full_variant["attempt_1_or_2_exact_rate"] - baseline_variant["attempt_1_or_2_exact_rate"]
    split_label = benchmark["split"]
    # Holdout discipline note: surface when this summary contains blind_holdout data.
    holdout_note = (
        "⚠️  This summary includes blind_holdout data. Do not use these numbers to guide tuning decisions."
        if split_label in ("all", "blind_holdout")
        else f"Split provenance: {split_label} (safe for tuning feedback)."
    )
    return "\n".join(
        [
            "# Next Stage Summary",
            "",
            f"> {holdout_note}",
            "",
            "## Current Strengths",
            f"- Split evaluated: {split_label}.",
            f"- Determinism status: outputs={determinism['stable_outputs']}, rankings={determinism['stable_rankings']}, metrics={determinism['stable_metrics']}.",
            f"- Current exact solve rate with full solver: {full_variant['attempt_1_or_2_exact_rate']:.3f}.",
            f"- Most frequent winning families: {', '.join(f'{name} ({count})' for name, count in strongest[:3]) or 'none'}.",
            "",
            "## Current Weaknesses",
            "- Dominant failure classes: {}.".format(
                ", ".join(f"{name} ({payload['count']})" for name, payload in top_failures[:3]) or "none"
            ),
            f"- Average uncertainty of winning hypotheses: {aggregate['average_uncertainty']:.3f}.",
            f"- Guardrail-sensitive search load: generated={aggregate['average_generated_count']:.2f}, refined={aggregate['average_refined_count']:.2f}.",
            "",
            "## Bottlenecks And Dead Weight",
            f"- Final task failures: {failures.get('final_task_failure_count', len(top_failures))}.",
            f"- Candidate transform crashes: {aggregate['transform_crash_count']}.",
            f"- Shape mismatch rejections (search phase): {aggregate['shape_mismatch_failure_count']}.",
            f"- Unsupported pattern exits: {failures.get('unsupported_pattern_exit_count', 'n/a')}.",
            f"- Failure tags seen: {', '.join(failures['global_tag_counts'].keys()) or 'none'}.",
            "",
            "## Recommended Priorities",
            "1. Improve failure-heavy shape and object-count transforms before expanding search breadth.",
            "2. Tighten ranking around contradiction-heavy or composition-sensitive losers.",
            "3. Use blind holdout scorecards to judge whether fixes generalise beyond dev/regression.",
            "",
            "## Thesis Assessment",
            f"- Measured solve-rate lift of full epistemic co-agency over primitive baseline: {lift:+.3f}.",
            "- Interpret lift jointly with split-specific scorecards and richer failure telemetry before expanding the approach further.",
        ]
    )
