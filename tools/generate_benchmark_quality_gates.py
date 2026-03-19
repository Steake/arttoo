from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arc_epistemic.eval.epistemic_redesign import quality_gates_markdown
from arc_epistemic.eval.reporting import write_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rewrite benchmark quality gates markdown/json from an existing experiment output.")
    parser.add_argument("--input", default="reports/benchmark_quality_gates.json")
    parser.add_argument("--json", default="reports/benchmark_quality_gates.json")
    parser.add_argument("--markdown", default="reports/benchmark_quality_gates.md")
    args = parser.parse_args(argv)

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    write_json(args.json, json.dumps(payload, indent=2, sort_keys=True))
    write_json(args.markdown, quality_gates_markdown(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
