# Ablation Report: regression

Baseline variant: `primitive_baseline_only`

| Variant | Solve rate | Avg runtime ms | Mean winning score | Solve delta | Runtime delta | Score delta |
| --- | --- | --- | --- | --- | --- | --- |
| primitive_baseline_only | 0.333 | 3.163 | 0.195 | +0.000 | +0.000 | +0.000 |
| primitive_plus_bounded_compositions | 0.500 | 3.902 | 0.365 | +0.167 | +0.739 | +0.170 |
| epistemic_no_refinement | 0.333 | 1.219 | 0.000 | +0.000 | -1.944 | -0.194 |
| full_epistemic_coagency | 0.500 | 3.572 | 0.260 | +0.167 | +0.409 | +0.066 |