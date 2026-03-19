# Ablation Report: all

Baseline variant: `primitive_baseline_only`

| Variant | Solve rate | Avg runtime ms | Mean winning score | Solve delta | Runtime delta | Score delta |
| --- | --- | --- | --- | --- | --- | --- |
| primitive_baseline_only | 0.632 | 1.712 | 0.620 | +0.000 | +0.000 | +0.000 |
| primitive_plus_bounded_compositions | 0.842 | 3.590 | 0.834 | +0.211 | +1.878 | +0.214 |
| epistemic_no_refinement | 0.632 | 1.152 | 0.544 | +0.000 | -0.560 | -0.076 |
| full_epistemic_coagency | 0.842 | 3.581 | 0.869 | +0.211 | +1.869 | +0.249 |