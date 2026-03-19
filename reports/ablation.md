# Ablation Report: all

Baseline variant: `primitive_baseline_only`

| Variant | Solve rate | Avg runtime ms | Mean winning score | Solve delta | Runtime delta | Score delta |
| --- | --- | --- | --- | --- | --- | --- |
| primitive_baseline_only | 0.750 | 2.189 | 0.729 | +0.000 | +0.000 | +0.000 |
| primitive_plus_bounded_compositions | 0.812 | 4.115 | 0.793 | +0.062 | +1.927 | +0.064 |
| epistemic_no_refinement | 0.750 | 1.383 | 0.719 | +0.000 | -0.806 | -0.010 |
| full_epistemic_coagency | 0.812 | 4.124 | 0.816 | +0.062 | +1.935 | +0.087 |