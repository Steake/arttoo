# Ablation Report: all

Baseline variant: `primitive_baseline_only`

| Variant | Solve rate | Avg runtime ms | Mean winning score | Solve delta | Runtime delta | Score delta |
| --- | --- | --- | --- | --- | --- | --- |
| primitive_baseline_only | 0.714 | 3.623 | 0.541 | +0.000 | +0.000 | +0.000 |
| primitive_plus_bounded_compositions | 0.786 | 3.088 | 0.613 | +0.071 | -0.535 | +0.073 |
| epistemic_no_refinement | 0.714 | 0.989 | 0.586 | +0.000 | -2.634 | +0.045 |
| full_epistemic_coagency | 0.786 | 3.122 | 0.697 | +0.071 | -0.501 | +0.157 |