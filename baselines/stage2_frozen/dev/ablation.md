# Ablation Report: dev

Baseline variant: `primitive_baseline_only`

| Variant | Solve rate | Avg runtime ms | Mean winning score | Solve delta | Runtime delta | Score delta |
| --- | --- | --- | --- | --- | --- | --- |
| primitive_baseline_only | 0.875 | 3.020 | 0.922 | +0.000 | +0.000 | +0.000 |
| primitive_plus_bounded_compositions | 1.000 | 7.644 | 1.050 | +0.125 | +4.624 | +0.128 |
| epistemic_no_refinement | 0.875 | 1.031 | 0.955 | +0.000 | -1.990 | +0.032 |
| full_epistemic_coagency | 1.000 | 3.225 | 1.150 | +0.125 | +0.204 | +0.227 |