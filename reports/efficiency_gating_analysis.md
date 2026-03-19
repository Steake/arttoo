# Efficiency Gating Analysis

## Compute Deltas

| Experiment | Metric | Mean A | Mean B | Estimate | 95% CI |
| --- | --- | --- | --- | --- | --- |
| frozen | scored_hypotheses | 36.806 | 23.306 | -13.500 | [-15.667, -11.333] |
| frozen | refined_hypotheses | 30.000 | 16.500 | -13.500 | [-15.667, -11.333] |
| frozen | refined_output_classes | 8.389 | 1.778 | -6.611 | [-6.889, -6.333] |
| frozen | runtime_ms | 3.202 | 1.958 | -1.244 | [-1.483, -0.998] |
| native | scored_hypotheses | 36.806 | 23.306 | -13.500 | [-15.667, -11.333] |
| native | refined_hypotheses | 30.000 | 16.500 | -13.500 | [-15.667, -11.333] |
| native | refined_output_classes | 0.000 | 1.778 | +1.778 | [+1.639, +1.917] |
| native | runtime_ms | 4.992 | 4.182 | -0.810 | [-1.118, -0.493] |

## Solve-Rate Paired Audit

| Experiment | Rate A | Rate B | Estimate | 95% CI | Only A | Only B | Both | Neither | McNemar p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| frozen | 0.444 | 0.667 | +0.222 | [+0.028, +0.417] | 3 | 11 | 13 | 9 | 0.061369 |
| native | 0.444 | 0.639 | +0.194 | [+0.000, +0.389] | 3 | 10 | 13 | 10 | 0.096092 |