from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arc_epistemic.eval.causal_v2 import build_freeze_manifest, freeze_manifest_markdown
from arc_epistemic.eval.reporting import write_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate blind_holdout_v3 freeze manifest artifacts.")
    parser.add_argument("--split-path", default="data/splits/blind_holdout_v3.json")
    parser.add_argument("--manifest-path", default="data/splits/blind_holdout_v3_manifest.json")
    parser.add_argument("--json", default="reports/blind_holdout_v3_freeze_manifest.json")
    parser.add_argument("--markdown", default="reports/blind_holdout_v3_freeze_manifest.md")
    args = parser.parse_args(argv)

    payload = build_freeze_manifest(args.split_path, args.manifest_path)
    write_json(args.json, json.dumps(payload, indent=2, sort_keys=True))
    write_json(args.markdown, freeze_manifest_markdown(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
