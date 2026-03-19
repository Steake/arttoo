# Next Stage Summary

> ⚠️  This summary includes blind_holdout data. Do not use these numbers to guide tuning decisions.

## Current Strengths
- Split evaluated: blind_holdout.
- Determinism status: outputs=True, rankings=True, metrics=True.
- Current exact solve rate with full solver: 1.000.
- Most frequent winning families: geometry (2), symmetry (2), objects (1).

## Current Weaknesses
- Dominant failure classes: none.
- Average uncertainty of winning hypotheses: 0.000.
- Guardrail-sensitive search load: generated=9.20, refined=28.80.

## Bottlenecks And Dead Weight
- Final task failures: 0.
- Candidate transform crashes: 0.
- Shape mismatch rejections (search phase): 76.
- Unsupported pattern exits: 0.
- Failure tags seen: none.

## Recommended Priorities
1. Improve failure-heavy shape and object-count transforms before expanding search breadth.
2. Tighten ranking around contradiction-heavy or composition-sensitive losers.
3. Use blind holdout scorecards to judge whether fixes generalise beyond dev/regression.

## Thesis Assessment
- Measured solve-rate lift of full epistemic co-agency over primitive baseline: +0.400.
- Interpret lift jointly with split-specific scorecards and richer failure telemetry before expanding the approach further.