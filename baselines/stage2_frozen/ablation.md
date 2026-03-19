# Ablation Report: all

Baseline variant: `primitive_baseline_only`

| Variant | Solve rate | Avg runtime ms | Mean winning score | Solve delta | Runtime delta | Score delta |
| --- | --- | --- | --- | --- | --- | --- |
| primitive_baseline_only | 0.714 | 2.811 | 0.541 | +0.000 | +0.000 | +0.000 |
| primitive_plus_bounded_compositions | 0.786 | 4.481 | 0.613 | +0.071 | +1.670 | +0.073 |
| epistemic_no_refinement | 0.714 | 0.992 | 0.586 | +0.000 | -1.819 | +0.045 |
| full_epistemic_coagency | 0.786 | 3.906 | 0.697 | +0.071 | +1.095 | +0.157 |