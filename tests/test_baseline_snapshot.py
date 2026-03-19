import json
import tempfile
import unittest
from pathlib import Path

from tools.snapshot_baseline import main as snapshot_main


class BaselineSnapshotTests(unittest.TestCase):
    def test_snapshot_baseline_copies_reports_and_writes_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            reports = root / "reports"
            reports.mkdir()
            (reports / "benchmark.json").write_text(json.dumps({"split": "dev", "aggregate": {"attempt_1_or_2_exact_rate": 0.9}}), encoding="utf-8")
            (reports / "ablation.json").write_text(
                json.dumps(
                    {
                        "baseline": "primitive_baseline_only",
                        "variants": {
                            "primitive_baseline_only": {"aggregate": {"attempt_1_or_2_exact_rate": 0.8}}
                        },
                    }
                ),
                encoding="utf-8",
            )
            (reports / "determinism.json").write_text(
                json.dumps({"stable_outputs": True, "stable_rankings": True, "stable_metrics": True}),
                encoding="utf-8",
            )
            snapshot_main(["--reports", str(reports), "--output", str(root / "baselines"), "--name", "frozen"])
            manifest = json.loads((root / "baselines" / "frozen" / "baseline_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["task_set_used"], "dev")
            self.assertAlmostEqual(manifest["lift"], 0.1)


if __name__ == "__main__":
    unittest.main()
