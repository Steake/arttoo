# Ablation Report: regression

Baseline variant: `primitive_baseline_only`

| Variant | Solve rate | Avg runtime ms | Mean winning score | Solve delta | Runtime delta | Score delta |
| --- | --- | --- | --- | --- | --- | --- |
| primitive_baseline_only | 0.286 | 2.511 | 0.173 | +0.000 | +0.000 | +0.000 |
| primitive_plus_bounded_compositions | 0.571 | 3.232 | 0.463 | +0.286 | +0.721 | +0.290 |
| epistemic_no_refinement | 0.286 | 1.068 | -0.053 | +0.000 | -1.444 | -0.226 |
| full_epistemic_coagency | 0.571 | 3.262 | 0.387 | +0.286 | +0.750 | +0.215 |