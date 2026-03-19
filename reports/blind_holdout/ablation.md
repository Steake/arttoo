# Ablation Report: blind_holdout

Baseline variant: `primitive_baseline_only`

| Variant | Solve rate | Avg runtime ms | Mean winning score | Solve delta | Runtime delta | Score delta |
| --- | --- | --- | --- | --- | --- | --- |
| primitive_baseline_only | 0.600 | 3.311 | 0.644 | +0.000 | +0.000 | +0.000 |
| primitive_plus_bounded_compositions | 1.000 | 3.904 | 1.050 | +0.400 | +0.593 | +0.406 |
| epistemic_no_refinement | 0.600 | 1.245 | 0.532 | +0.000 | -2.066 | -0.112 |
| full_epistemic_coagency | 1.000 | 3.889 | 1.150 | +0.400 | +0.579 | +0.506 |