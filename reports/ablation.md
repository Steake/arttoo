# Ablation Report: all

Baseline variant: `primitive_baseline_only`

| Variant | Solve rate | Avg runtime ms | Mean winning score | Solve delta | Runtime delta | Score delta |
| --- | --- | --- | --- | --- | --- | --- |
| primitive_baseline_only | 0.750 | 2.173 | 0.729 | +0.000 | +0.000 | +0.000 |
| primitive_plus_bounded_compositions | 0.812 | 4.156 | 0.793 | +0.062 | +1.983 | +0.064 |
| epistemic_no_refinement | 0.750 | 1.338 | 0.719 | +0.000 | -0.835 | -0.010 |
| full_epistemic_coagency | 0.812 | 4.114 | 0.816 | +0.062 | +1.941 | +0.087 |