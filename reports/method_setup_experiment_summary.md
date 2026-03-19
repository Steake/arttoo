# Method Setup Experiment Summary

- Primary dataset: `blind_holdout_v5`
- Selector-divergence quality valid: `True`
- Diversity quality valid: `True`
- Verdict: `proven_strongly` (high)

| Method | Frozen solve rate | Native solve rate |
| --- | --- | --- |
| M0 | 0.4444 | 0.4444 |
| M1 | 0.4444 | 0.4444 |
| M2 | 0.7778 | 0.75 |
| M3 | 0.7222 | 0.7222 |
| M4 | 0.6667 | 0.6389 |
| R_anchor | 0.4444 | 0.4444 |

## Hostile Audit Quick View

| Experiment | Contrast | Estimate | 95% CI | Only A | Only B | Both | Neither | McNemar p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| frozen | overall M2-M0 | +0.333 | [+0.167, +0.500] | 0 | 12 | 16 | 8 | 0.001496 |
| native | overall M2-M0 | +0.306 | [+0.167, +0.472] | 0 | 11 | 16 | 9 | 0.002569 |
| frozen | selector_divergence M2-M0 | +1.000 | [+1.000, +1.000] | 0 | 12 | 0 | 0 | 0.001496 |
| native | selector_divergence M2-M0 | +0.917 | [+0.750, +1.000] | 0 | 11 | 0 | 1 | 0.002569 |
| frozen | diversity_sensitive M3-M2 | +1.000 | [+1.000, +1.000] | 0 | 8 | 0 | 0 | 0.013328 |
| native | diversity_sensitive M3-M2 | +1.000 | [+1.000, +1.000] | 0 | 8 | 0 | 0 | 0.013328 |
| frozen | overall M4-R_anchor | +0.222 | [+0.028, +0.417] | 3 | 11 | 13 | 9 | 0.061369 |
| native | overall M4-R_anchor | +0.194 | [+0.000, +0.389] | 3 | 10 | 13 | 10 | 0.096092 |

## Key Efficiency Deltas (M4 vs R_anchor)

| Experiment | Metric | Mean A | Mean B | Estimate | 95% CI |
| --- | --- | --- | --- | --- | --- |
| frozen | scored_hypotheses | 36.806 | 23.306 | -13.500 | [-15.667, -11.333] |
| frozen | refined_hypotheses | 30.000 | 16.500 | -13.500 | [-15.667, -11.333] |
| frozen | runtime_ms | 3.202 | 1.958 | -1.244 | [-1.483, -0.998] |
| native | scored_hypotheses | 36.806 | 23.306 | -13.500 | [-15.667, -11.333] |
| native | refined_hypotheses | 30.000 | 16.500 | -13.500 | [-15.667, -11.333] |
| native | runtime_ms | 4.992 | 4.182 | -0.810 | [-1.118, -0.493] |