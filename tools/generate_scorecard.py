from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arc_epistemic.eval.analysis import build_scorecard, serialize_json
from arc_epistemic.eval.reporting import scorecard_markdown, write_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a top-line scorecard from benchmark outputs.")
    parser.add_argument("--benchmark", required=True, help="Benchmark JSON path.")
    parser.add_argument("--ablation", required=True, help="Ablation JSON path.")
    parser.add_argument("--determinism", required=True, help="Determinism JSON path.")
    parser.add_argument("--failures", required=True, help="Failure summary JSON path.")
    parser.add_argument("--output", required=True, help="Scorecard JSON output path.")
    parser.add_argument("--markdown", help="Optional markdown companion path.")
    args = parser.parse_args(argv)

    benchmark = json.loads(Path(args.benchmark).read_text(encoding="utf-8"))
    ablation = json.loads(Path(args.ablation).read_text(encoding="utf-8"))
    determinism = json.loads(Path(args.determinism).read_text(encoding="utf-8"))
    failures = json.loads(Path(args.failures).read_text(encoding="utf-8"))
    scorecard = build_scorecard(benchmark, ablation, determinism, failures)
    write_json(args.output, serialize_json(scorecard))
    if args.markdown:
        write_json(args.markdown, scorecard_markdown(scorecard))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
