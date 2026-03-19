# Next Stage Summary

> Split provenance: dev (safe for tuning feedback).

## Current Strengths
- Split evaluated: dev.
- Determinism status: outputs=True, rankings=True, metrics=True.
- Current exact solve rate with full solver: 1.000.
- Most frequent winning families: geometry (3), symmetry (3), color (1).

## Current Weaknesses
- Dominant failure classes: none.
- Average uncertainty of winning hypotheses: 0.000.
- Guardrail-sensitive search load: generated=9.62, refined=29.25.

## Bottlenecks And Dead Weight
- Final task failures: 0.
- Candidate transform crashes: 0.
- Shape mismatch rejections (search phase): 90.
- Unsupported pattern exits: 0.
- Failure tags seen: none.

## Recommended Priorities
1. Improve failure-heavy shape and object-count transforms before expanding search breadth.
2. Tighten ranking around contradiction-heavy or composition-sensitive losers.
3. Use blind holdout scorecards to judge whether fixes generalise beyond dev/regression.

## Thesis Assessment
- Measured solve-rate lift of full epistemic co-agency over primitive baseline: +0.125.
- Interpret lift jointly with split-specific scorecards and richer failure telemetry before expanding the approach further.