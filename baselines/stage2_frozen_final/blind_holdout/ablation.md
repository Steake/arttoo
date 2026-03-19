# Ablation Report: blind_holdout

Baseline variant: `primitive_baseline_only`

| Variant | Solve rate | Avg runtime ms | Mean winning score | Solve delta | Runtime delta | Score delta |
| --- | --- | --- | --- | --- | --- | --- |
| primitive_baseline_only | 1.000 | 14.729 | 1.050 | +0.000 | +0.000 | +0.000 |
| primitive_plus_bounded_compositions | 1.000 | 3.643 | 1.050 | +0.000 | -11.086 | +0.000 |
| epistemic_no_refinement | 1.000 | 1.099 | 1.150 | +0.000 | -13.630 | +0.100 |
| full_epistemic_coagency | 1.000 | 3.434 | 1.150 | +0.000 | -11.295 | +0.100 |