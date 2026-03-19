# Final Split Diagnostics

> ⚠️  blind_holdout and all-split numbers are NOT safe for tuning. They are provided for honest reporting only.

Split provenance:
- **dev**: tuning fixtures — safe for hyperparameter and solver iteration.
- **regression**: known-failure regression fixtures — safe for targeted debugging.
- **blind_holdout** ⚠️: unseen at tuning time — for honest reporting only.
- **all** ⚠️: aggregate across all fixtures — for honest reporting only.

| Split | Tasks | Solve rate | Baseline rate | Lift | Avg uncertainty | Final failures | Unsupported exits | Shape rejections | Crash failures | Avg runtime | Worst runtime |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dev | 8 | 1.000 | 0.875 | +0.125 | 0.000 | 0 | 0 | 90 | 0 | 5.998 ms | 15.812 ms |
| regression | 6 | 0.500 | 0.333 | +0.167 | 0.333 | 3 | 3 | 150 | 0 | 5.945 ms | 14.307 ms |
| blind_holdout ⚠️ | 3 | 1.000 | 1.000 | +0.000 | 0.000 | 0 | 0 | 24 | 0 | 8.966 ms | 14.415 ms |
| all ⚠️ | 16 | 0.812 | 0.750 | +0.062 | 0.125 | 3 | 3 | 238 | 0 | 4.984 ms | 16.278 ms |

### Blind Holdout Verdict

> ⚠️  blind_holdout and all-split numbers are NOT safe for tuning. They are provided for honest reporting only.

- **Solver vs baseline:** Full solver matches primitive baseline on blind_holdout (both 1.000). No additional lift from the epistemic layer.
- **Uncertainty:** Average winning uncertainty on blind_holdout is 0.0 (effectively zero). All holdout tasks are resolved with full confidence. Uncertainty is not decision-relevant here because the primitive transforms are unambiguous for these tasks.
- **Failures:** No task failures on blind_holdout. No dominant failure family present.
- **Generalisation:** Current evidence shows the epistemic layer does **not** add measurable lift on blind_holdout. The primitive baseline already solves all holdout tasks. This means there is no room for epistemic machinery to demonstrate value on the current holdout set. Expand the holdout set with tasks the primitive baseline fails on to get a meaningful signal.