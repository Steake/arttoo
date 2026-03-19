from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arc_epistemic.eval.causal_v2 import uncertainty_causal_markdown
from arc_epistemic.eval.reporting import write_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render the attribution v2 uncertainty causal analysis report.")
    parser.add_argument("--input", default="reports/causal_factorial_v2.json")
    parser.add_argument("--json", default="reports/uncertainty_causal_analysis.json")
    parser.add_argument("--markdown", default="reports/uncertainty_causal_analysis.md")
    args = parser.parse_args(argv)

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))["uncertainty_causal_analysis"]
    write_json(args.json, json.dumps(payload, indent=2, sort_keys=True))
    write_json(args.markdown, uncertainty_causal_markdown(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
