# Final Split Diagnostics

> ⚠️  blind_holdout and all-split numbers are NOT safe for tuning. They are provided for honest reporting only.

Split provenance:
- **dev**: tuning fixtures — safe for hyperparameter and solver iteration.
- **regression**: known-failure regression fixtures — safe for targeted debugging.
- **blind_holdout** ⚠️: unseen at tuning time — for honest reporting only.
- **all** ⚠️: aggregate across all fixtures — for honest reporting only.

| Split | Tasks | Solve rate | Baseline rate | Lift | Avg uncertainty | Final failures | Unsupported exits | Shape rejections | Crash failures | Avg runtime | Worst runtime |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dev | 8 | 1.000 | 0.875 | +0.125 | 0.000 | 0 | 0 | 90 | 0 | 5.059 ms | 14.751 ms |
| regression | 7 | 0.571 | 0.286 | +0.286 | 0.286 | 3 | 3 | 176 | 0 | 4.682 ms | 13.388 ms |
| blind_holdout ⚠️ | 5 | 1.000 | 0.600 | +0.400 | 0.000 | 0 | 0 | 76 | 0 | 5.818 ms | 13.588 ms |
| all ⚠️ | 19 | 0.842 | 0.632 | +0.211 | 0.105 | 3 | 3 | 316 | 0 | 4.158 ms | 13.591 ms |

### Blind Holdout Verdict

> ⚠️  blind_holdout and all-split numbers are NOT safe for tuning. They are provided for honest reporting only.

- **Solver vs baseline:** Full solver beats primitive baseline on blind_holdout by +0.400 (1.000 vs 0.600).
- **Uncertainty:** Average winning uncertainty on blind_holdout is 0.0 (effectively zero). All holdout tasks are resolved with full confidence. Uncertainty is not decision-relevant here because the primitive transforms are unambiguous for these tasks.
- **Failures:** No task failures on blind_holdout. No dominant failure family present.
- **Generalisation:** Current evidence **supports** generalisation beyond tuning-facing splits.