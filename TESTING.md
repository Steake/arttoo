# Testing Harness

This repository uses Python `unittest` consistently because `pytest` is not available in the current environment.

## Task Splits

Task membership is defined in [data/splits](data/splits):

- `dev`: supported development fixtures — **safe for tuning**.
- `regression`: regression-focused fixtures, including retained failure-family coverage — **safe for tuning**.
- `blind_holdout`: isolated holdout fixtures for less gameable evaluation — **not tuning-safe**.
- `all`: every fixture under [data/fixtures](data/fixtures) — **not tuning-safe**.

## Run Tests

```bash
python -m unittest discover -s tests -p 'test_*.py'
python -m unittest tests.test_regressions
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

Current findings (see `reports/uncertainty_audit.md`):
- Uncertainty is zero for all solved tasks (binary-signal tasks: one transform matches perfectly, all others fail).
- Uncertainty is non-zero for some unsolved tasks (partial-match cases in the regression split).
- Uncertainty does **not** affect final ranking in the current fixture suite, because no task has competing partial hypotheses that uncertainty would need to disambiguate.
- This is honest, not a bug. To make uncertainty decision-relevant, add tasks where multiple candidate transforms each partially satisfy training pairs.

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
| `reports/scorecard.json` (all) | ❌ no — includes holdout |
| `reports/final_split_diagnostics.md` | ⚠️ read all columns; blind_holdout column is marked |
| `reports/uncertainty_audit.md` | ⚠️ read split labels; holdout rows are marked |
| `reports/multi_split_summary.md` | ⚠️ read split labels; holdout rows are marked |

## What To Read First

- Read [reports/final_split_diagnostics.md](reports/final_split_diagnostics.md) for a complete cross-split view with explicit blind holdout verdict.
- Read [reports/dev/next_stage_summary.md](reports/dev/next_stage_summary.md) for optimisation handoff on the development split.
- Read [reports/uncertainty_audit.md](reports/uncertainty_audit.md) to understand whether the epistemic layer is providing decision-relevant uncertainty.
- Use `scorecard.json` for quick numerical comparison.
- Use per-task diagnostics when a failure class needs deeper inspection.
