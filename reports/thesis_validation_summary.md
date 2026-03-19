# Thesis Validation Summary

> ⚠️  The `blind_holdout` column is for honest reporting only — not for tuning.

This document answers the six core questions about the epistemic co-agency thesis.

## Six Core Questions

### 1. Is blind_holdout currently discriminative?

**YES**

Primitive baseline fails 2/5 blind_holdout tasks (rate=0.600).  The holdout is discriminative: it contains tasks that require epistemic refinement (composition) to solve.

### 2. Does the full solver beat the primitive baseline on blind_holdout?

**YES**

Full solver=1.000, primitive baseline=0.600, lift=+0.400 on 5 blind_holdout tasks.

### 3. Is uncertainty present on any solved tasks?

**YES**

Non-zero first-pass uncertainty on 4 solved task(s): holdout_composition_crop_flip_task (split=blind_holdout), holdout_composition_largest_rotate_task (split=blind_holdout), ambiguous_competing_regression_task (split=regression), crop_rotate_task (split=regression).  This means the first-pass winner did not fully explain all training pairs before refinement corrected it.

### 4. Is uncertainty decision-relevant?

**YES**

9 successful reordering(s) across all splits: refinement replaced a non-certain first-pass winner with a correct composed hypothesis.  Uncertainty (non-zero on the first-pass winner) directly determined the final answer.

### 5. Do epistemic reorderings occur?

**YES**

9 reordering(s) detected (all=4, blind_holdout=2, dev=1, regression=2).

### 6. Is current evidence sufficient to claim generalisation?

#### What is proven

Full solver beats primitive baseline on blind_holdout (measured lift > 0).  Epistemic refinement reorders candidates in at least one task, demonstrating that the co-agency loop provides value beyond the first-pass primitives.

#### What is suggested but not proven

No additional evidence suggests generalisation beyond what is proven.

#### What remains untestable because of benchmark design

No known gaps in the current benchmark design.

## Overall Verdict

The thesis is currently **testable and shows positive evidence**: the holdout is discriminative, the full solver outperforms the primitive baseline on unseen tasks, and epistemic reorderings have been observed.  Further evidence is needed to establish that uncertainty-aware ranking (rather than refinement alone) drives the lift.