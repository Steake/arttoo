# Multi-Split Scorecard Summary

> Split provenance: dev = tuning fixtures, regression = known-failure regressions, blind_holdout = unseen at tuning time, all = aggregate across all splits.

| Split | Solve rate | Baseline rate | Lift | Determinism | Final failures | Avg uncertainty |
| --- | --- | --- | --- | --- | --- | --- |
| dev | 1.000 | 0.875 | +0.125 | yes | 0 | 0.0 |
| regression | 0.571 | 0.286 | +0.286 | yes | 3 | 0.2857142857142857 |
| blind_holdout | 1.000 | 0.600 | +0.400 | yes | 0 | 0.0 |
| all | 0.842 | 0.632 | +0.211 | yes | 3 | 0.10526315789473684 |