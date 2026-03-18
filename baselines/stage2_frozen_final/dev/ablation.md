# Ablation Report: dev

Baseline variant: `primitive_baseline_only`

| Variant | Solve rate | Avg runtime ms | Mean winning score | Solve delta | Runtime delta | Score delta |
| --- | --- | --- | --- | --- | --- | --- |
| primitive_baseline_only | 0.875 | 3.072 | 0.922 | +0.000 | +0.000 | +0.000 |
| primitive_plus_bounded_compositions | 1.000 | 3.398 | 1.050 | +0.125 | +0.326 | +0.128 |
| epistemic_no_refinement | 0.875 | 1.040 | 0.955 | +0.000 | -2.032 | +0.032 |
| full_epistemic_coagency | 1.000 | 3.244 | 1.150 | +0.125 | +0.173 | +0.227 |