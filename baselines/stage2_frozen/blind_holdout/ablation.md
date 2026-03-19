# Ablation Report: blind_holdout

Baseline variant: `primitive_baseline_only`

| Variant | Solve rate | Avg runtime ms | Mean winning score | Solve delta | Runtime delta | Score delta |
| --- | --- | --- | --- | --- | --- | --- |
| primitive_baseline_only | 1.000 | 2.808 | 1.050 | +0.000 | +0.000 | +0.000 |
| primitive_plus_bounded_compositions | 1.000 | 15.187 | 1.050 | +0.000 | +12.379 | +0.000 |
| epistemic_no_refinement | 1.000 | 1.086 | 1.150 | +0.000 | -1.722 | +0.100 |
| full_epistemic_coagency | 1.000 | 3.338 | 1.150 | +0.000 | +0.529 | +0.100 |