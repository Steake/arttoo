from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arc_epistemic.eval.causal_v2 import (
    causal_factorial_markdown_v2,
    build_causal_verdict_v2,
    build_subset_analyses,
    build_task_level_attribution_v2,
    build_uncertainty_causal_analysis,
    load_manifest,
    manifest_by_task,
    run_frozen_factorial_v2,
    run_native_factorial_v2,
    task_level_attribution_markdown_v2,
    causal_verdict_markdown_v2,
)
from arc_epistemic.eval.fixtures import load_fixture_split
from arc_epistemic.eval.reporting import write_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run attribution v2 on blind_holdout_v3.")
    parser.add_argument("--tasks", default="data/fixtures")
    parser.add_argument("--split", default="blind_holdout_v3")
    parser.add_argument("--manifest", default="data/splits/blind_holdout_v3_manifest.json")
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--n-bootstrap", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    reports_dir = Path(args.reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    fixtures = load_fixture_split(args.tasks, split=args.split)
    entries = load_manifest(args.manifest)
    manifest_lookup = manifest_by_task(entries)
    missing = sorted(set(manifest_lookup) - {fixture.task_id for fixture in fixtures})
    if missing:
        raise ValueError(f"Manifest tasks missing from fixtures: {missing}")

    native = run_native_factorial_v2(fixtures, split=args.split)
    frozen = run_frozen_factorial_v2(fixtures, split=args.split)
    subset_analyses = build_subset_analyses(entries, native, frozen, n_bootstrap=args.n_bootstrap, seed=args.seed)
    task_entries = build_task_level_attribution_v2(entries, native, frozen)
    uncertainty_analysis = build_uncertainty_causal_analysis(subset_analyses, task_entries)
    verdict = build_causal_verdict_v2(subset_analyses, task_entries)

    bundle = {
        "split": args.split,
        "manifest": json.loads(Path(args.manifest).read_text(encoding="utf-8")),
        "subset_analyses": subset_analyses,
        "task_level_attribution_v2": task_entries,
        "uncertainty_causal_analysis": uncertainty_analysis,
        "causal_verdict_v2": verdict,
    }
    write_json(reports_dir / "causal_factorial_v2.json", json.dumps(bundle, indent=2, sort_keys=True))
    write_json(reports_dir / "causal_factorial_v2.md", causal_factorial_markdown_v2(bundle))
    write_json(reports_dir / "task_level_attribution_v2.json", json.dumps(task_entries, indent=2, sort_keys=True))
    write_json(reports_dir / "task_level_attribution_v2.md", task_level_attribution_markdown_v2(task_entries))
    write_json(reports_dir / "causal_verdict_v2.json", json.dumps(verdict, indent=2, sort_keys=True))
    write_json(reports_dir / "causal_verdict_v2.md", causal_verdict_markdown_v2(verdict))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
