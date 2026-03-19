# Ablation Report: blind_holdout

Baseline variant: `primitive_baseline_only`

| Variant | Solve rate | Avg runtime ms | Mean winning score | Solve delta | Runtime delta | Score delta |
| --- | --- | --- | --- | --- | --- | --- |
| primitive_baseline_only | 1.000 | 4.819 | 1.050 | +0.000 | +0.000 | +0.000 |
| primitive_plus_bounded_compositions | 1.000 | 5.610 | 1.050 | +0.000 | +0.791 | +0.000 |
| epistemic_no_refinement | 1.000 | 1.458 | 1.150 | +0.000 | -3.361 | +0.100 |
| full_epistemic_coagency | 1.000 | 4.491 | 1.150 | +0.000 | -0.328 | +0.100 |