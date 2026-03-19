# Output Selection Causal Analysis

## Hostile Audit Quick View

| Experiment | Family | Contrast | Estimate | 95% CI | Only A | Only B | Both | Neither | McNemar p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| frozen | overall | m2_vs_m0 | +0.333 | [+0.167, +0.500] | 0 | 12 | 16 | 8 | 0.001496 |
| native | overall | m2_vs_m0 | +0.306 | [+0.167, +0.472] | 0 | 11 | 16 | 9 | 0.002569 |
| frozen | selector_divergence | m2_vs_m0 | +1.000 | [+1.000, +1.000] | 0 | 12 | 0 | 0 | 0.001496 |
| native | selector_divergence | m2_vs_m0 | +0.917 | [+0.750, +1.000] | 0 | 11 | 0 | 1 | 0.002569 |
| frozen | diversity_sensitive | m3_vs_m2 | +1.000 | [+1.000, +1.000] | 0 | 8 | 0 | 0 | 0.013328 |
| native | diversity_sensitive | m3_vs_m2 | +1.000 | [+1.000, +1.000] | 0 | 8 | 0 | 0 | 0.013328 |
| frozen | overall | m4_vs_anchor | +0.222 | [+0.028, +0.417] | 3 | 11 | 13 | 9 | 0.061369 |
| native | overall | m4_vs_anchor | +0.194 | [+0.000, +0.389] | 3 | 10 | 13 | 10 | 0.096092 |

## Full Pairwise Contrast Table

| Experiment | Family | Contrast | Estimate | 95% CI | Only A | Only B | Both | Neither | McNemar p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| frozen | overall | m2_vs_m0 | +0.333 | [+0.167, +0.500] | 0 | 12 | 16 | 8 | 0.001496 |
| frozen | overall | m2_vs_m1 | +0.333 | [+0.167, +0.500] | 0 | 12 | 16 | 8 | 0.001496 |
| frozen | overall | m3_vs_m2 | -0.056 | [-0.278, +0.194] | 10 | 8 | 18 | 0 | 0.813664 |
| frozen | overall | m4_vs_m3 | -0.056 | [-0.306, +0.194] | 11 | 9 | 15 | 1 | 0.823063 |
| frozen | overall | m4_vs_anchor | +0.222 | [+0.028, +0.417] | 3 | 11 | 13 | 9 | 0.061369 |
| frozen | selector_divergence | m2_vs_m0 | +1.000 | [+1.000, +1.000] | 0 | 12 | 0 | 0 | 0.001496 |
| frozen | selector_divergence | m2_vs_m1 | +1.000 | [+1.000, +1.000] | 0 | 12 | 0 | 0 | 0.001496 |
| frozen | selector_divergence | m3_vs_m2 | -0.167 | [-0.417, +0.000] | 2 | 0 | 10 | 0 | 0.479500 |
| frozen | selector_divergence | m4_vs_m3 | +0.083 | [+0.000, +0.250] | 0 | 1 | 10 | 1 | 1.000000 |
| frozen | selector_divergence | m4_vs_anchor | +0.917 | [+0.750, +1.000] | 0 | 11 | 0 | 1 | 0.002569 |
| frozen | diversity_sensitive | m2_vs_m0 | +0.000 | [+0.000, +0.000] | 0 | 0 | 0 | 8 | — |
| frozen | diversity_sensitive | m2_vs_m1 | +0.000 | [+0.000, +0.000] | 0 | 0 | 0 | 8 | — |
| frozen | diversity_sensitive | m3_vs_m2 | +1.000 | [+1.000, +1.000] | 0 | 8 | 0 | 0 | 0.013328 |
| frozen | diversity_sensitive | m4_vs_m3 | -1.000 | [-1.000, -1.000] | 8 | 0 | 0 | 0 | 0.013328 |
| frozen | diversity_sensitive | m4_vs_anchor | +0.000 | [+0.000, +0.000] | 0 | 0 | 0 | 8 | — |
| frozen | refinement_composition | m2_vs_m0 | +0.000 | [+0.000, +0.000] | 0 | 0 | 8 | 0 | — |
| frozen | refinement_composition | m2_vs_m1 | +0.000 | [+0.000, +0.000] | 0 | 0 | 8 | 0 | — |
| frozen | refinement_composition | m3_vs_m2 | -1.000 | [-1.000, -1.000] | 8 | 0 | 0 | 0 | 0.013328 |
| frozen | refinement_composition | m4_vs_m3 | +1.000 | [+1.000, +1.000] | 0 | 8 | 0 | 0 | 0.013328 |
| frozen | refinement_composition | m4_vs_anchor | +0.000 | [+0.000, +0.000] | 0 | 0 | 8 | 0 | — |
| frozen | control | m2_vs_m0 | +0.000 | [+0.000, +0.000] | 0 | 0 | 8 | 0 | — |
| frozen | control | m2_vs_m1 | +0.000 | [+0.000, +0.000] | 0 | 0 | 8 | 0 | — |
| frozen | control | m3_vs_m2 | +0.000 | [+0.000, +0.000] | 0 | 0 | 8 | 0 | — |
| frozen | control | m4_vs_m3 | -0.375 | [-0.750, -0.125] | 3 | 0 | 5 | 0 | 0.248213 |
| frozen | control | m4_vs_anchor | -0.375 | [-0.750, -0.125] | 3 | 0 | 5 | 0 | 0.248213 |
| native | overall | m2_vs_m0 | +0.306 | [+0.167, +0.472] | 0 | 11 | 16 | 9 | 0.002569 |
| native | overall | m2_vs_m1 | +0.306 | [+0.167, +0.472] | 0 | 11 | 16 | 9 | 0.002569 |
| native | overall | m3_vs_m2 | -0.028 | [-0.250, +0.194] | 9 | 8 | 18 | 1 | 1.000000 |
| native | overall | m4_vs_m3 | -0.083 | [-0.333, +0.139] | 11 | 8 | 15 | 2 | 0.646355 |
| native | overall | m4_vs_anchor | +0.194 | [+0.000, +0.389] | 3 | 10 | 13 | 10 | 0.096092 |
| native | selector_divergence | m2_vs_m0 | +0.917 | [+0.750, +1.000] | 0 | 11 | 0 | 1 | 0.002569 |
| native | selector_divergence | m2_vs_m1 | +0.917 | [+0.750, +1.000] | 0 | 11 | 0 | 1 | 0.002569 |
| native | selector_divergence | m3_vs_m2 | -0.083 | [-0.250, +0.000] | 1 | 0 | 10 | 1 | 1.000000 |
| native | selector_divergence | m4_vs_m3 | +0.000 | [+0.000, +0.000] | 0 | 0 | 10 | 2 | — |
| native | selector_divergence | m4_vs_anchor | +0.833 | [+0.583, +1.000] | 0 | 10 | 0 | 2 | 0.004427 |
| native | diversity_sensitive | m2_vs_m0 | +0.000 | [+0.000, +0.000] | 0 | 0 | 0 | 8 | — |
| native | diversity_sensitive | m2_vs_m1 | +0.000 | [+0.000, +0.000] | 0 | 0 | 0 | 8 | — |
| native | diversity_sensitive | m3_vs_m2 | +1.000 | [+1.000, +1.000] | 0 | 8 | 0 | 0 | 0.013328 |
| native | diversity_sensitive | m4_vs_m3 | -1.000 | [-1.000, -1.000] | 8 | 0 | 0 | 0 | 0.013328 |
| native | diversity_sensitive | m4_vs_anchor | +0.000 | [+0.000, +0.000] | 0 | 0 | 0 | 8 | — |
| native | refinement_composition | m2_vs_m0 | +0.000 | [+0.000, +0.000] | 0 | 0 | 8 | 0 | — |
| native | refinement_composition | m2_vs_m1 | +0.000 | [+0.000, +0.000] | 0 | 0 | 8 | 0 | — |
| native | refinement_composition | m3_vs_m2 | -1.000 | [-1.000, -1.000] | 8 | 0 | 0 | 0 | 0.013328 |
| native | refinement_composition | m4_vs_m3 | +1.000 | [+1.000, +1.000] | 0 | 8 | 0 | 0 | 0.013328 |
| native | refinement_composition | m4_vs_anchor | +0.000 | [+0.000, +0.000] | 0 | 0 | 8 | 0 | — |
| native | control | m2_vs_m0 | +0.000 | [+0.000, +0.000] | 0 | 0 | 8 | 0 | — |
| native | control | m2_vs_m1 | +0.000 | [+0.000, +0.000] | 0 | 0 | 8 | 0 | — |
| native | control | m3_vs_m2 | +0.000 | [+0.000, +0.000] | 0 | 0 | 8 | 0 | — |
| native | control | m4_vs_m3 | -0.375 | [-0.750, -0.125] | 3 | 0 | 5 | 0 | 0.248213 |
| native | control | m4_vs_anchor | -0.375 | [-0.750, -0.125] | 3 | 0 | 5 | 0 | 0.248213 |