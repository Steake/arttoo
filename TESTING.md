# Testing Harness

This repository uses Python `unittest` consistently because `pytest` is not available in the current environment.

## Task Splits

Task membership is defined in [data/splits](/workspace/arttoo/data/splits):

- `dev`: supported development fixtures
- `regression`: regression-focused fixtures, including retained failure-family coverage
- `blind_holdout`: isolated holdout fixtures for less gameable evaluation
- `all`: every fixture under [data/fixtures](/workspace/arttoo/data/fixtures)

## Run Tests

```bash
python -m unittest discover -s tests -p 'test_*.py'
python -m unittest tests.test_regressions
```

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

`scorecard.json` is the fastest top-line artifact to compare splits or solver revisions. It includes split, exact solve rate, primitive baseline solve rate, lift, determinism pass/fail, failure counts, runtime, task count, and timestamp.

## Snapshot A Frozen Baseline

```bash
python tools/snapshot_baseline.py --reports reports --output baselines --name stage2_frozen
```

This copies the report bundle into `baselines/<name>/` and writes `baseline_manifest.json` with task set, solve rates, lift, determinism status, timestamp, and git commit when available.

## Run The Full Validation Battery

```bash
python tools/run_full_validation.py --tasks data/fixtures --reports reports --splits all dev regression blind_holdout
```

This keeps the legacy root `reports/` flow for `all`, and writes split-aware outputs into:

- [reports/dev](/workspace/arttoo/reports/dev)
- [reports/regression](/workspace/arttoo/reports/regression)
- [reports/blind_holdout](/workspace/arttoo/reports/blind_holdout)

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

## Telemetry

Per-task telemetry is stored in `benchmark.json` and copied into `per_task_diagnostics.json` by the full validation command. Each task record includes:

- deterministic fingerprint
- generated and refined candidates
- ranked hypothesis snapshots
- prune records and prune reasons
- agent disagreement summary
- selected hypotheses
- confidence values
- step counts and evaluation counts

## What To Read First

- Read [reports/dev/next_stage_summary.md](/workspace/arttoo/reports/dev/next_stage_summary.md) first for optimisation handoff on the development split.
- Use `scorecard.json` for quick comparison.
- Use per-task diagnostics when a failure class needs deeper inspection.
