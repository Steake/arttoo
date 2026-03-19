# Epistemic Process Verdict

- Status: `proven_strongly`
- Conviction level: `high`
- Uncertainty causal effect: `proven_strongly`
- Efficiency gain: `proven_strongly`
- Output-selection answer changes: `12`
- Diversity-aware answer changes: `18`

## Summary

blind_holdout_v5 passed the mechanism-exercise gates. Uncertainty verdict: proven_strongly. Efficiency verdict: proven_strongly.

## Proven strongly
- output-level selection has an independent causal effect on selector_divergence tasks
- diversity-aware coalition support has an independent causal effect on diversity_sensitive tasks
- margin-gated refinement reduces compute while preserving accuracy

## Suggestive
- none

## Falsified
- diversity-aware selection is not a generally safe replacement for refinement-composition tasks on this benchmark