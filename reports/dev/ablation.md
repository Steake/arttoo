# Ablation Report: dev

Baseline variant: `primitive_baseline_only`

| Variant | Solve rate | Avg runtime ms | Mean winning score | Solve delta | Runtime delta | Score delta |
| --- | --- | --- | --- | --- | --- | --- |
| primitive_baseline_only | 0.875 | 2.981 | 0.922 | +0.000 | +0.000 | +0.000 |
| primitive_plus_bounded_compositions | 1.000 | 4.420 | 1.050 | +0.125 | +1.440 | +0.128 |
| epistemic_no_refinement | 0.875 | 1.406 | 0.955 | +0.000 | -1.575 | +0.032 |
| full_epistemic_coagency | 1.000 | 4.289 | 1.150 | +0.125 | +1.308 | +0.227 |