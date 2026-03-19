# Testing Harness

This repository uses Python `unittest` consistently because `pytest` is not available in the current environment.

## Task Splits

Task membership is defined in [data/splits](data/splits):

- `dev`: supported development fixtures — **safe for tuning**.
- `regression`: regression-focused fixtures, including retained failure-family coverage — **safe for tuning**.
- `blind_holdout`: isolated holdout fixtures for less gameable evaluation — **not tuning-safe**.
- `blind_holdout_v2`: second holdout cohort of 5 discriminative tasks used in the 2×2 factorial causal attribution experiment — **not tuning-safe**.
- `blind_holdout_v3`: 24-task frozen attribution-v2 holdout (8 ranking_conflict, 8 refinement_composition, 8 control) and the **primary inferential target** for current causal claims — **not tuning-safe**.
- `all`: every fixture under [data/fixtures](data/fixtures) — **not tuning-safe**.

## Run Tests

```bash
python -m unittest discover -s tests -p 'test_*.py'
python -m unittest tests.test_regressions
python -m unittest tests.test_causal_factorial_v2
```

## Run The Full Validation Battery

```bash
python tools/run_full_validation.py --tasks data/fixtures --reports reports --splits dev regression blind_holdout all
```

This runs tests, benchmarks, ablations, determinism checks, failure summaries, and scorecards for all four splits.
It also generates:

- `reports/multi_split_summary.md` — one-glance split comparison table
- `reports/final_split_diagnostics.json` / `.md` — machine-readable diagnostics with blind holdout verdict
- `reports/uncertainty_audit.json` / `.md` — uncertainty calibration and decision-relevance analysis
- `reports/blind_holdout_v3_freeze_manifest.json` / `.md` — frozen task manifest hash and timestamp
- `reports/causal_factorial_v2.json` — full attribution-v2 machine-readable bundle
- `reports/task_level_attribution_v2.json` / `.md` — richer per-task attribution and audit telemetry
- `reports/uncertainty_causal_analysis.json` / `.md` — uncertainty-specific causal analysis on the frozen benchmark
- `reports/causal_verdict_v2.json` / `.md` — explicit factor verdicts (`proven` / `supported but not isolated` / `still inconclusive`)
- `reports/thesis_final_attribution_summary.json` / `.md` — final blind_holdout_v3 thesis summary
- `reports/output_competition_benchmark.json` / `.md` — output-level evidential aggregation vs single-best selection on ranking-conflict tasks, plus contested-refinement efficiency

Per-split outputs go to `reports/dev/`, `reports/regression/`, `reports/blind_holdout/`. Aggregate outputs go to `reports/`.

## Run Benchmarks By Split

```bash
python tools/run_benchmarks.py --tasks data/fixtures --split dev --report reports/dev/benchmark.md --json reports/dev/benchmark.json
python tools/run_benchmarks.py --tasks data/fixtures --split blind_holdout --report reports/blind_holdout/benchmark.md --json reports/blind_holdout/benchmark.json
```

## Run Ablations

```bash
python tools/run_ablation.py --tasks data/fixtures --split dev --report reports/dev/ablation.md --json reports/dev/ablation.json
```

## Run Determinism Checks

```bash
python tools/check_determinism.py --tasks data/fixtures --split dev --runs 5 --report reports/dev/determinism.md --json reports/dev/determinism.json
```

The determinism report states whether stability held across:

- repeated identical runs
- reversed task order
- logically separate subprocess invocations
- seed perturbations passed through the environment

## Run Failure Summaries

```bash
python tools/summarize_failures.py --input reports/dev/benchmark.json --output reports/dev/failures.md --json reports/dev/failures.json
```

## Generate A Scorecard

```bash
python tools/generate_scorecard.py \
  --benchmark reports/dev/benchmark.json \
  --ablation reports/dev/ablation.json \
  --determinism reports/dev/determinism.json \
  --failures reports/dev/failures.json \
  --output reports/dev/scorecard.json \
  --markdown reports/dev/scorecard.md
```

`scorecard.json` is the fastest top-line artifact to compare splits or solver revisions. It includes split, exact solve rate, primitive baseline solve rate, lift, determinism pass/fail, failure counts (4 separate categories), runtime, task count, and timestamp.

## Generate Final Split Diagnostics

```bash
python tools/generate_final_split_diagnostics.py --reports reports
```

Reads per-split scorecard and failure JSON files and writes:
- `reports/final_split_diagnostics.json` — machine-readable table with all required fields for all 4 splits
- `reports/final_split_diagnostics.md` — markdown with split provenance, full table, and an explicit blind holdout verdict section

### How to interpret lift by split

- **dev lift > 0**: epistemic co-agency adds value on tuning fixtures.
- **regression lift > 0**: epistemic layer improves over primitive-only baseline on known-failure tasks.
- **blind_holdout lift > 0**: genuine generalisation beyond tuning-facing splits.
- **blind_holdout lift = 0 with baseline = 1.0**: the holdout set is too easy — baseline already solves all tasks. No headroom for the epistemic layer to demonstrate value. Expand the holdout set with harder tasks.
- **blind_holdout lift < 0**: regression on unseen data — investigate before further tuning.

### How to interpret blind holdout verdicts

`final_split_diagnostics.md` contains a "Blind Holdout Verdict" section with explicit conclusions:
- Does the full solver beat the primitive baseline on blind_holdout?
- By how much?
- Is uncertainty meaningfully present on blind_holdout?
- What is the dominant failure family?
- Does current evidence support generalisation?

## Generate Uncertainty Audit

```bash
python tools/generate_uncertainty_audit.py --reports reports
```

Reads per-split `per_task_diagnostics.json` and writes:
- `reports/uncertainty_audit.json` — per-split analysis of uncertainty presence and decision-relevance
- `reports/uncertainty_audit.md` — markdown with verdict, per-task detail, and conclusion

### What the uncertainty audit means

The audit answers three questions:
1. **Is uncertainty present?** Are any winning hypotheses non-zero in uncertainty?
2. **Is it calibrated?** Is uncertainty higher for unsolved tasks than solved tasks?
3. **Is it decision-relevant?** Does uncertainty change which hypothesis wins the final ranking?

## Generate Epistemic Reordering Analysis

```bash
python tools/generate_epistemic_reorderings.py --reports reports
```

Reads per-split `per_task_diagnostics.json` (all splits under `reports/`) and writes:
- `reports/epistemic_reorderings.json` — machine-readable per-split reordering counts
- `reports/epistemic_reorderings.md` — markdown table with per-task detail and verdict

A **reordering** occurs when the first-pass winner (top hypothesis after the initial primitive
evaluation) differs from the final winner after the co-agency refinement pass.

The report emits per-split:
- `tasks_with_multiple_competing_candidates` — tasks where ≥ 2 first-pass hypotheses are viable
- `tasks_with_nonzero_winning_uncertainty` — tasks where the first-pass winner has uncertainty > 0
- `tasks_where_first_pass_winner_changed_after_refinement` — reorderings
- `reorder_success_count` — reorderings that led to a correct final answer
- `reorder_failure_count` — reorderings that still produced a wrong answer

Reorderings are the primary operational signal that the co-agency loop adds value beyond the
primitive baseline.  The benchmark contains verified reordering tasks:
- `crop_rotate_task` (regression): `crop_to_content` → `crop_to_content -> rotate90`
- `holdout_composition_crop_flip_task` (blind_holdout): `crop_to_content` → `crop_to_content -> flip_horizontal`
- `holdout_composition_largest_rotate_task` (blind_holdout): `largest_object` → `largest_object -> flip_vertical`
- `ambiguous_competing_regression_task` (regression): `largest_object` → `largest_object -> flip_horizontal`

## Generate Thesis Validation Summary

```bash
python tools/generate_thesis_validation_summary.py --reports reports
```

Reads `final_split_diagnostics.json`, `epistemic_reorderings.json`, and per-split
`per_task_diagnostics.json`, then writes:
- `reports/thesis_validation_summary.json` — machine-readable answers to the six core questions
- `reports/thesis_validation_summary.md` — markdown with direct YES/NO answers and evidence

The summary answers these six questions without ambiguity:
1. Is `blind_holdout` currently discriminative?
2. Does the full solver beat the primitive baseline on `blind_holdout`?
3. Is uncertainty present on any solved tasks?
4. Is uncertainty decision-relevant?
5. Do epistemic reorderings occur?
6. Is current evidence sufficient to claim generalisation of epistemic co-agency?

### How to interpret the discriminativeness gate

The holdout is considered **discriminative** if either:
- The primitive baseline fails ≥ 1 holdout task (solve rate < 1.0), OR
- The full solver beats the primitive baseline on ≥ 1 holdout task.

The current blind_holdout passes this gate: 2/5 holdout tasks require composition and are **not**
solved by the primitive baseline alone.

## Run The 2×2 Factorial Causal Attribution Experiment

```bash
python tools/run_causal_factorial.py --tasks data/fixtures --split blind_holdout_v2 --report reports/blind_holdout_v2/causal_factorial.md --json reports/blind_holdout_v2/causal_factorial.json
```

Runs all four factorial conditions (C00, C10, C01, C11) on every task in the specified split and writes:
- `causal_factorial.json` — machine-readable contrasts, attribution table, and verdict
- `causal_factorial.md` — markdown report with solve-rate table, five contrasts + interaction, task attribution, and causal verdict

### 2×2 Factorial Design

| Condition | use_refinement | use_epistemic_scoring | Config |
| --- | --- | --- | --- |
| C00 | False | False | `primitive_baseline_only` |
| C10 | True  | False | `primitive_plus_bounded_compositions` |
| C01 | False | True  | `epistemic_no_refinement` |
| C11 | True  | True  | `full_epistemic_coagency` |

**Naming convention**: C{refinement_bit}{epistemic_bit}.

### Five pairwise contrasts + interaction

| Contrast | Question answered |
| --- | --- |
| `c10_vs_c00` | Does refinement alone help? (simple effect of R at E=0) |
| `c01_vs_c00` | Does epistemic scoring alone help? (simple effect of E at R=0) |
| `c11_vs_c10` | Does epistemic scoring help given refinement? (simple effect of E at R=1) |
| `c11_vs_c01` | Does refinement help given epistemic scoring? (simple effect of R at E=1) |
| `c11_vs_c00` | Full co-agency vs primitive baseline (overall lift) |
| `interaction_RxE` | R×E synergy: (C11 − C01) − (C10 − C00) |

## Run The Output Competition Benchmark

```bash
python tools/run_output_competition_benchmark.py --tasks data/fixtures --split blind_holdout_v3 --reports-dir reports
```

This benchmark keeps the current attribution infrastructure intact while adding the next hypothesis test:

- **Frozen candidate pool**: compare single-best-hypothesis selection against output-level evidential aggregation on the sealed `ranking_conflict` subset.
- **Native pipeline**: compare the current broad refinement loop against output aggregation with and without contested-output gating, and report compute savings.

Each contrast reports:
- Solve rate in each condition
- Estimate (difference in solve rates)
- Paired bootstrap 95% CI (2000 resamples, default seed 42)
- McNemar chi-squared statistic and p-value (continuity-corrected)

### Task Attribution Categories

Each task is assigned one of these causal categories based on its 4-bit solve pattern (C00, C10, C01, C11):

| Category | Pattern | Interpretation |
| --- | --- | --- |
| `all_solve` | (T,T,T,T) | Task is trivially easy — all configs solve it |
| `none_solve` | (F,F,F,F) | Task is beyond current capability |
| `trivially_solved` | C00=T | Primitive baseline already solves it |
| `baseline_only` | (T,F,F,F) | Baseline solves; other configs regress |
| `refinement_resolves` | (F,T,F,T) | Refinement (R) is the sole causal factor |
| `epistemic_resolves` | (F,F,T,T) | Epistemic scoring (E) is the sole causal factor |
| `synergy_required` | (F,F,F,T) | Both factors together are required (pure interaction) |
| `either_factor_sufficient` | (F,T,T,T) | Either R or E alone suffices |

### blind_holdout_v2 Cohort

The five new discriminative tasks in `blind_holdout_v2`:

| Task | Pattern | Category | Notes |
| --- | --- | --- | --- |
| `holdout_v2_crop_flip_v_task` | (F,T,F,T) | `refinement_resolves` | `crop_to_content -> flip_vertical` |
| `holdout_v2_crop_rotate90_task` | (F,T,F,T) | `refinement_resolves` | `crop_to_content -> rotate90` |
| `holdout_v2_flip_h_task` | (T,T,T,T) | `all_solve` | `flip_horizontal` primitive |
| `holdout_v2_largest_rotate180_task` | (F,T,F,T) | `refinement_resolves` | `largest_object -> rotate180` |
| `holdout_v2_rotate270_task` | (T,T,T,T) | `all_solve` | `rotate270` primitive |

The dominant causal factor on `blind_holdout_v2` is **Refinement**: ME_R ≈ +0.60, ME_E ≈ 0.00, interaction ≈ 0.00.

## Attribution v2: blind_holdout_v3

`blind_holdout_v3` is now the primary causal benchmark because it freezes intended task mechanisms before solver evaluation. Labels come from the manifest, **not** from observed solver outcomes.

### Freeze protocol

After authoring or editing the v3 split, freeze it immediately:

```bash
python tools/generate_freeze_manifest.py
```

This writes:
- `reports/blind_holdout_v3_freeze_manifest.json`
- `reports/blind_holdout_v3_freeze_manifest.md`

The freeze manifest records timestamp plus SHA-256 hashes for both:
- `data/splits/blind_holdout_v3.json`
- `data/splits/blind_holdout_v3_manifest.json`

Do not relabel tasks after freezing based on solver outcomes.

### Run attribution v2

```bash
python tools/run_causal_factorial_v2.py --tasks data/fixtures --reports-dir reports
python tools/generate_uncertainty_causal_analysis.py --input reports/causal_factorial_v2.json
python tools/generate_thesis_final_attribution_summary.py --causal-input reports/causal_factorial_v2.json --freeze-input reports/blind_holdout_v3_freeze_manifest.json
```

### Required validation order

```bash
python -m unittest tests.test_causal_factorial_v2
python -m unittest discover -s tests -p 'test_*.py'
python tools/generate_freeze_manifest.py
python tools/run_causal_factorial_v2.py --tasks data/fixtures --reports-dir reports
python tools/generate_uncertainty_causal_analysis.py --input reports/causal_factorial_v2.json
python tools/generate_thesis_final_attribution_summary.py --causal-input reports/causal_factorial_v2.json --freeze-input reports/blind_holdout_v3_freeze_manifest.json
```

### v3 subset interpretation

- `all_blind_holdout_v3`: overall benchmark, reported honestly but not used to relabel mechanism.
- `ranking_conflict`: intended uncertainty-sensitive tasks. Positive uncertainty evidence is assessed **here**, not on the aggregate alone.
- `refinement_composition`: intended bounded-composition tasks. Positive refinement evidence is assessed **here**.
- `control`: sanity-check tasks where all conditions should usually agree.

### Evidence rules encoded in attribution v2

**Strong evidence that uncertainty is causal** requires all of:
1. positive uncertainty effect on the `ranking_conflict` subset,
2. materially one-sided evidence (`95% CI` excludes 0 **or** exact paired wins are one-sided, with an honest caveat if only the latter holds),
3. nonzero successful uncertainty-driven reorderings,
4. at least one `uncertainty_only_gain` or `synergy_gain`,
5. directional consistency between frozen-pool and native-pipeline analyses.

**Strong evidence that refinement is causal** uses the analogous rule on the `refinement_composition` subset.

Final factor verdicts must explicitly distinguish:
- `proven`
- `supported but not isolated`
- `still inconclusive`

Each verdict also reports conviction:
- `high`
- `moderate`
- `low`

An honestly null or inconclusive uncertainty result is acceptable. The benchmark goal is a fair frozen test with an explicit verdict, not a forced positive claim.

## Snapshot A Frozen Baseline

```bash
python tools/snapshot_baseline.py --reports reports --output baselines --name stage2_frozen
```

This copies the report bundle into `baselines/<name>/` and writes `baseline_manifest.json` with task set, solve rates, lift, determinism status, timestamp, and git commit when available.

## Failure Taxonomy

Failures are typed with a primary class plus optional tags. Primary classes currently include:

- `unsupported_pattern`
- `wrong_shape`
- `object_count_mismatch`
- `symmetry_failure`
- `colour_mapping_failure`
- `size_inference_failure`
- `composition_failure`
- `ranking_error`
- `no_candidate_solution`

Tags add extra context such as `unsupported_pattern`, `object_count_mismatch`, `high_uncertainty`, or `attempt_2_rescue_available`.

The scorecard and failure reports now emit four separate failure counters (not one collapsed number):
- `final_task_failure_count` — tasks that ultimately produced a wrong answer
- `candidate_transform_failure_count` — transform crashes during hypothesis evaluation
- `shape_mismatch_rejection_count` — shape-incompatible hypotheses rejected during search
- `unsupported_pattern_exit_count` — tasks classified as unsupported pattern family

## Per-Task Telemetry Schema

Per-task telemetry is stored in `benchmark.json` and copied into `per_task_diagnostics.json`. Each task record has a `telemetry` sub-dict with the following fields:

| Field | Description |
| --- | --- |
| `deterministic_fingerprint` | SHA-256 hex of the full prediction + ranking, for exact reproducibility checks |
| `expected_fingerprint` | Short hex fingerprint of the expected output grid |
| `runtime_ms` | Wall-clock time for the full solve loop (included in telemetry for self-contained analysis) |
| `generated_candidates` | List of hypothesis descriptions proposed by the generator |
| `refined_candidates` | List of composed hypothesis descriptions from the refinement pass |
| `first_pass_ranking` | Snapshot dicts of all hypotheses after first evaluation pass (before refinement) |
| `final_ranking` | Snapshot dicts of all hypotheses after second evaluation pass (after refinement) |
| `first_pass_pruned` | Records of hypotheses pruned after first pass, with reason |
| `final_pruned` | Records of hypotheses pruned after second pass, with reason |
| `agent_disagreements` | Top-5 hypothesis family vote counts and score band — proxy for divergence |
| `selection.attempt_1_hypothesis` | Description of the hypothesis used for attempt 1 |
| `selection.attempt_2_hypothesis` | Description of the hypothesis used for attempt 2 (if distinct) |
| `selection.selected_hypotheses` | Full list of selected hypothesis descriptions per test case |
| `confidence.belief` | Belief of the winning hypothesis (support_count / total_train_pairs) |
| `confidence.disbelief` | Disbelief of the winning hypothesis (contradiction_count / total_train_pairs) |
| `confidence.uncertainty` | Uncertainty (unresolved_count / total_train_pairs) |
| `confidence.score` | Final ranking score (`belief + 0.15*partial - 0.5*uncertainty - disbelief`) |
| `step_counts.generated_count` | Number of hypotheses generated |
| `step_counts.first_pass_scored_count` | Hypotheses evaluated in first pass |
| `step_counts.first_pass_survivor_count` | Hypotheses surviving first-pass pruning |
| `step_counts.refined_count` | Composed hypotheses generated in refinement pass |
| `step_counts.second_pass_scored_count` | Hypotheses evaluated in second pass |
| `step_counts.final_survivor_count` | Hypotheses surviving second-pass pruning |
| `step_counts.evaluation_count` | Total (hypothesis × train_pair) evaluations |

The `runtime_ms` field is also available at the task root level (outside the `telemetry` sub-dict) for aggregate reporting. The `telemetry.runtime_ms` field mirrors it for self-contained per-task analysis.

Fields that might be expected but are **not currently available**:
- Per-hypothesis runtime (transforms are not individually timed; only the full loop is timed)
- Per-train-pair prediction detail (only aggregate support/contradiction counts are tracked)
- Search tree structure (the loop is flat, not tree-shaped)

## Tuning Safety

| Artifact | Safe for tuning? |
| --- | --- |
| `reports/dev/scorecard.json` | ✅ yes |
| `reports/regression/scorecard.json` | ✅ yes |
| `reports/blind_holdout/scorecard.json` | ❌ no — holdout numbers |
| `reports/blind_holdout_v2/causal_factorial.json` | ❌ no — holdout numbers |
| `reports/causal_factorial_v2.json` | ❌ no — frozen blind_holdout_v3 attribution benchmark |
| `reports/task_level_attribution_v2.md` | ❌ no — frozen blind_holdout_v3 task-level evidence |
| `reports/uncertainty_causal_analysis.md` | ❌ no — frozen blind_holdout_v3 uncertainty verdict |
| `reports/thesis_final_attribution_summary.md` | ❌ no — frozen blind_holdout_v3 final thesis verdict |
| `reports/scorecard.json` (all) | ❌ no — includes holdout |
| `reports/final_split_diagnostics.md` | ⚠️ read all columns; blind_holdout column is marked |
| `reports/uncertainty_audit.md` | ⚠️ read split labels; holdout rows are marked |
| `reports/multi_split_summary.md` | ⚠️ read split labels; holdout rows are marked |
| `reports/epistemic_reorderings.md` | ⚠️ read split labels; blind_holdout rows are marked |
| `reports/thesis_validation_summary.md` | ⚠️ read all sections; holdout evidence is clearly labeled |

## What To Read First

- Read [reports/thesis_validation_summary.md](reports/thesis_validation_summary.md) for the six-question thesis verdict (discriminativeness, lift, uncertainty, reorderings, generalisation).
- Read [reports/epistemic_reorderings.md](reports/epistemic_reorderings.md) for the first-pass vs final ranking comparison across all splits.
- Read [reports/final_split_diagnostics.md](reports/final_split_diagnostics.md) for a complete cross-split view with explicit blind holdout verdict.
- Read [reports/dev/next_stage_summary.md](reports/dev/next_stage_summary.md) for optimisation handoff on the development split.
- Read [reports/uncertainty_audit.md](reports/uncertainty_audit.md) to understand whether the epistemic layer is providing decision-relevant uncertainty.
- Use `scorecard.json` for quick numerical comparison.
- Use per-task diagnostics when a failure class needs deeper inspection.
