from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arc_epistemic.eval.analysis import compare_variants, serialize_json
from arc_epistemic.eval.fixtures import load_fixture_split
from arc_epistemic.eval.reporting import ablation_markdown, write_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run ARC solver ablations.")
    parser.add_argument("--tasks", required=True, help="Directory of ARC fixture tasks.")
    parser.add_argument("--split", default="all", help="Task split to evaluate: all, dev, regression, blind_holdout.")
    parser.add_argument("--report", required=True, help="Markdown ablation report output path.")
    parser.add_argument("--json", help="Optional JSON ablation output path.")
    args = parser.parse_args(argv)

    fixtures = load_fixture_split(args.tasks, split=args.split)
    result = compare_variants(fixtures, split=args.split)
    json_path = args.json or str(Path(args.report).with_suffix(".json"))
    write_json(json_path, serialize_json(result))
    write_json(args.report, ablation_markdown(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
