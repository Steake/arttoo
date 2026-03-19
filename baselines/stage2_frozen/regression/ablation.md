# Ablation Report: regression

Baseline variant: `primitive_baseline_only`

| Variant | Solve rate | Avg runtime ms | Mean winning score | Solve delta | Runtime delta | Score delta |
| --- | --- | --- | --- | --- | --- | --- |
| primitive_baseline_only | 0.000 | 11.091 | -0.733 | +0.000 | +0.000 | +0.000 |
| primitive_plus_bounded_compositions | 0.250 | 2.741 | -0.478 | +0.250 | -8.350 | +0.255 |
| epistemic_no_refinement | 0.000 | 0.954 | -0.824 | +0.000 | -10.137 | -0.091 |
| full_epistemic_coagency | 0.250 | 2.749 | -0.434 | +0.250 | -8.342 | +0.299 |