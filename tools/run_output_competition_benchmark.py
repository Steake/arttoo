from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arc_epistemic.eval.fixtures import load_fixture_split
from arc_epistemic.eval.output_competition import (
    output_competition_json,
    output_competition_markdown,
    run_frozen_output_competition_experiment,
    run_native_output_competition_experiment,
)
from arc_epistemic.eval.reporting import write_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run output-level competition benchmark.")
    parser.add_argument("--tasks", default="data/fixtures")
    parser.add_argument("--split", default="blind_holdout_v3")
    parser.add_argument("--reports-dir", default="reports")
    args = parser.parse_args(argv)

    fixtures = load_fixture_split(args.tasks, split=args.split)
    bundle = {
        "split": args.split,
        "frozen": run_frozen_output_competition_experiment(fixtures, split=args.split),
        "native": run_native_output_competition_experiment(fixtures, split=args.split),
    }
    reports_dir = Path(args.reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    write_json(reports_dir / "output_competition_benchmark.json", output_competition_json(bundle))
    write_json(reports_dir / "output_competition_benchmark.md", output_competition_markdown(bundle))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
