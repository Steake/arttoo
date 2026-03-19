# Multi-Split Scorecard Summary

> Split provenance: dev = tuning fixtures, regression = known-failure regressions, blind_holdout = unseen at tuning time, all = aggregate across all splits.

| Split | Solve rate | Baseline rate | Lift | Determinism | Final failures | Avg uncertainty |
| --- | --- | --- | --- | --- | --- | --- |
| dev | 1.000 | 0.875 | +0.125 | yes | 0 | 0.0 |
| regression | 0.500 | 0.333 | +0.167 | yes | 3 | 0.3333333333333333 |
| blind_holdout | 1.000 | 1.000 | +0.000 | yes | 0 | 0.0 |
| all | 0.812 | 0.750 | +0.062 | yes | 3 | 0.125 |