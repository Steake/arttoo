from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arc_epistemic.eval.epistemic_redesign import (
    build_benchmark_quality_gates,
    build_efficiency_gating_analysis,
    build_epistemic_process_verdict,
    build_freeze_manifest,
    build_output_selection_causal_analysis,
    build_task_level_epistemic_attribution,
    experiment_markdown,
    freeze_manifest_markdown,
    load_manifest,
    method_setup_experiment_summary,
    method_setup_summary_markdown,
    quality_gates_markdown,
    run_frozen_experiment,
    run_native_experiment,
    summarize_experiment,
    task_level_attribution_markdown,
    verdict_markdown,
    output_selection_causal_markdown,
    efficiency_gating_markdown,
)
from arc_epistemic.eval.fixtures import load_fixture_split
from arc_epistemic.eval.reporting import write_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the blind_holdout_v5 epistemic method redesign experiment.")
    parser.add_argument("--tasks", default="data/fixtures")
    parser.add_argument("--split", default="blind_holdout_v5")
    parser.add_argument("--split-path", default="data/splits/blind_holdout_v5.json")
    parser.add_argument("--manifest", default="data/splits/blind_holdout_v5_manifest.json")
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--n-bootstrap", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    reports_dir = Path(args.reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    fixtures = load_fixture_split(args.tasks, split=args.split)
    entries = load_manifest(args.manifest)
    freeze_manifest = build_freeze_manifest(args.split, args.split_path, args.manifest)
    frozen = summarize_experiment(run_frozen_experiment(fixtures, entries, split=args.split, freeze_manifest=freeze_manifest))
    native = summarize_experiment(run_native_experiment(fixtures, entries, split=args.split, freeze_manifest=freeze_manifest))
    quality = build_benchmark_quality_gates(frozen, native)
    causal = build_output_selection_causal_analysis(frozen, native, n_bootstrap=args.n_bootstrap, seed=args.seed)
    efficiency = build_efficiency_gating_analysis(frozen, native, n_bootstrap=args.n_bootstrap, seed=args.seed)
    task_level = build_task_level_epistemic_attribution(frozen, native)
    verdict = build_epistemic_process_verdict(frozen, native, quality, causal, efficiency, task_level)
    summary = method_setup_experiment_summary(frozen, native, quality, causal, efficiency, verdict)

    write_json(reports_dir / "blind_holdout_v5_freeze_manifest.json", json.dumps(freeze_manifest, indent=2, sort_keys=True))
    write_json(reports_dir / "blind_holdout_v5_freeze_manifest.md", freeze_manifest_markdown(freeze_manifest))
    write_json(reports_dir / "epistemic_method_redesign_frozen.json", json.dumps(frozen, indent=2, sort_keys=True))
    write_json(reports_dir / "epistemic_method_redesign_frozen.md", experiment_markdown(frozen, title="Epistemic Method Redesign — Frozen"))
    write_json(reports_dir / "epistemic_method_redesign_native.json", json.dumps(native, indent=2, sort_keys=True))
    write_json(reports_dir / "epistemic_method_redesign_native.md", experiment_markdown(native, title="Epistemic Method Redesign — Native"))
    write_json(reports_dir / "benchmark_quality_gates.json", json.dumps(quality, indent=2, sort_keys=True))
    write_json(reports_dir / "benchmark_quality_gates.md", quality_gates_markdown(quality))
    write_json(reports_dir / "output_selection_causal_analysis.json", json.dumps(causal, indent=2, sort_keys=True))
    write_json(reports_dir / "output_selection_causal_analysis.md", output_selection_causal_markdown(causal))
    write_json(reports_dir / "efficiency_gating_analysis.json", json.dumps(efficiency, indent=2, sort_keys=True))
    write_json(reports_dir / "efficiency_gating_analysis.md", efficiency_gating_markdown(efficiency))
    write_json(reports_dir / "task_level_epistemic_attribution.json", json.dumps(task_level, indent=2, sort_keys=True))
    write_json(reports_dir / "task_level_epistemic_attribution.md", task_level_attribution_markdown(task_level))
    write_json(reports_dir / "epistemic_process_verdict.json", json.dumps(verdict, indent=2, sort_keys=True))
    write_json(reports_dir / "epistemic_process_verdict.md", verdict_markdown(verdict))
    write_json(reports_dir / "method_setup_experiment_summary.json", json.dumps(summary, indent=2, sort_keys=True))
    write_json(reports_dir / "method_setup_experiment_summary.md", method_setup_summary_markdown(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
