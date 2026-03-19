# Ablation Report: regression

Baseline variant: `primitive_baseline_only`

| Variant | Solve rate | Avg runtime ms | Mean winning score | Solve delta | Runtime delta | Score delta |
| --- | --- | --- | --- | --- | --- | --- |
| primitive_baseline_only | 0.333 | 3.015 | 0.195 | +0.000 | +0.000 | +0.000 |
| primitive_plus_bounded_compositions | 0.500 | 3.888 | 0.365 | +0.167 | +0.872 | +0.170 |
| epistemic_no_refinement | 0.333 | 1.196 | 0.000 | +0.000 | -1.819 | -0.194 |
| full_epistemic_coagency | 0.500 | 3.564 | 0.260 | +0.167 | +0.549 | +0.066 |