from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arc_epistemic.eval.causal import (
    causal_markdown,
    compute_causal_contrasts,
    run_factorial_experiment,
    serialize_causal_json,
)
from arc_epistemic.eval.fixtures import load_fixture_split
from arc_epistemic.eval.reporting import write_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run 2×2 factorial causal attribution experiment on ARC fixtures."
    )
    parser.add_argument("--tasks", required=True, help="Directory of ARC fixture tasks.")
    parser.add_argument(
        "--split",
        default="blind_holdout_v2",
        help="Task split to evaluate (default: blind_holdout_v2).",
    )
    parser.add_argument("--report", required=True, help="Markdown causal report output path.")
    parser.add_argument("--json", help="Optional JSON causal output path.")
    parser.add_argument(
        "--n-bootstrap",
        type=int,
        default=2000,
        help="Number of bootstrap resamples for confidence intervals (default: 2000).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for bootstrap resampling (default: 42).",
    )
    args = parser.parse_args(argv)

    fixtures = load_fixture_split(args.tasks, split=args.split)
    if not fixtures:
        print(f"No fixtures found for split '{args.split}' in '{args.tasks}'.", file=sys.stderr)
        return 1

    factorial_result = run_factorial_experiment(fixtures, split=args.split)
    causal = compute_causal_contrasts(factorial_result, n_bootstrap=args.n_bootstrap, seed=args.seed)

    json_path = args.json or str(Path(args.report).with_suffix(".json"))
    write_json(json_path, serialize_causal_json(causal))
    write_json(args.report, causal_markdown(causal))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
