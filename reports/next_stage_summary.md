# Next Stage Summary

> ⚠️  This summary includes blind_holdout data. Do not use these numbers to guide tuning decisions.

## Current Strengths
- Split evaluated: all.
- Determinism status: outputs=True, rankings=True, metrics=True.
- Current exact solve rate with full solver: 0.842.
- Most frequent winning families: geometry (9), symmetry (6), objects (2).

## Current Weaknesses
- Dominant failure classes: unsupported_pattern (3).
- Average uncertainty of winning hypotheses: 0.105.
- Guardrail-sensitive search load: generated=9.42, refined=26.53.

## Bottlenecks And Dead Weight
- Final task failures: 3.
- Candidate transform crashes: 0.
- Shape mismatch rejections (search phase): 316.
- Unsupported pattern exits: 3.
- Failure tags seen: known_regression_fixture, object_count_mismatch, unsupported_pattern.

## Recommended Priorities
1. Improve failure-heavy shape and object-count transforms before expanding search breadth.
2. Tighten ranking around contradiction-heavy or composition-sensitive losers.
3. Use blind holdout scorecards to judge whether fixes generalise beyond dev/regression.

## Thesis Assessment
- Measured solve-rate lift of full epistemic co-agency over primitive baseline: +0.211.
- Interpret lift jointly with split-specific scorecards and richer failure telemetry before expanding the approach further.