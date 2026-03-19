from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arc_epistemic.eval.causal_v2 import build_thesis_final_summary, thesis_final_summary_markdown
from arc_epistemic.eval.reporting import write_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the final blind_holdout_v3 attribution summary.")
    parser.add_argument("--causal-input", default="reports/causal_factorial_v2.json")
    parser.add_argument("--freeze-input", default="reports/blind_holdout_v3_freeze_manifest.json")
    parser.add_argument("--json", default="reports/thesis_final_attribution_summary.json")
    parser.add_argument("--markdown", default="reports/thesis_final_attribution_summary.md")
    args = parser.parse_args(argv)

    causal = json.loads(Path(args.causal_input).read_text(encoding="utf-8"))
    freeze_manifest = json.loads(Path(args.freeze_input).read_text(encoding="utf-8"))
    payload = build_thesis_final_summary(
        freeze_manifest,
        causal["causal_verdict_v2"],
        causal["uncertainty_causal_analysis"],
        causal["task_level_attribution_v2"],
    )
    write_json(args.json, json.dumps(payload, indent=2, sort_keys=True))
    write_json(args.markdown, thesis_final_summary_markdown(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
