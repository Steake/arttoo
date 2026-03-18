# Ablation Report: regression

Baseline variant: `primitive_baseline_only`

| Variant | Solve rate | Avg runtime ms | Mean winning score | Solve delta | Runtime delta | Score delta |
| --- | --- | --- | --- | --- | --- | --- |
| primitive_baseline_only | 0.000 | 2.240 | -0.733 | +0.000 | +0.000 | +0.000 |
| primitive_plus_bounded_compositions | 0.250 | 7.920 | -0.478 | +0.250 | +5.680 | +0.255 |
| epistemic_no_refinement | 0.000 | 0.955 | -0.824 | +0.000 | -1.285 | -0.091 |
| full_epistemic_coagency | 0.250 | 2.689 | -0.434 | +0.250 | +0.450 | +0.299 |