from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arc_epistemic.eval.analysis import group_failures, serialize_json
from arc_epistemic.eval.reporting import failures_markdown, write_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize benchmark failure categories.")
    parser.add_argument("--input", required=True, help="Benchmark JSON input path.")
    parser.add_argument("--output", required=True, help="Failure summary markdown output path.")
    parser.add_argument("--json", help="Optional JSON failure summary output path.")
    args = parser.parse_args(argv)

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    failures = group_failures(payload.get("per_task", []), split=payload.get("split", "all"))
    json_path = args.json or str(Path(args.output).with_suffix(".json"))
    write_json(json_path, serialize_json(failures))
    write_json(args.output, failures_markdown(failures))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
