# 2×2 Factorial Causal Attribution

**Split**: `blind_holdout_v2` | **Tasks**: 5 | **Generated**: 2026-03-19T03:39:57.288915+00:00

## Factorial Design

| Condition | use_refinement | use_epistemic_scoring | Config |
| --- | --- | --- | --- |
| C00 | False | False | `primitive_baseline_only` |
| C10 | True | False | `primitive_plus_bounded_compositions` |
| C01 | False | True | `epistemic_no_refinement` |
| C11 | True | True | `full_epistemic_coagency` |

## Condition Solve Rates

| Condition | Solved | Total | Solve Rate |
| --- | --- | --- | --- |
| C00 | 2 | 5 | 0.400 |
| C10 | 5 | 5 | 1.000 |
| C01 | 2 | 5 | 0.400 |
| C11 | 5 | 5 | 1.000 |

## Causal Verdict

**Dominant factor**: `refinement`

- Main effect of Refinement (ME_R): `+0.6000`
- Main effect of Epistemic scoring (ME_E): `+0.0000`
- R×E Interaction: `+0.0000`

> Refinement (R) is the dominant causal factor (ME_R=+0.600 vs ME_E=+0.000). Adding bounded composition explains most of the +0.600 full-vs-primitive lift.

## Five Pairwise Contrasts

| Contrast | Rate_A | Rate_B | Estimate | 95% CI | McNemar p |
| --- | --- | --- | --- | --- | --- |
| c10_vs_c00 | 0.400 | 1.000 | +0.600 | [+0.200, +1.000] | 0.2482 |
| c01_vs_c00 | 0.400 | 0.400 | +0.000 | [+0.000, +0.000] | — |
| c11_vs_c10 | 1.000 | 1.000 | +0.000 | [+0.000, +0.000] | — |
| c11_vs_c01 | 0.400 | 1.000 | +0.600 | [+0.200, +1.000] | 0.2482 |
| c11_vs_c00 | 0.400 | 1.000 | +0.600 | [+0.200, +1.000] | 0.2482 |

## R×E Interaction

- Estimate: `+0.0000`
- 95% Bootstrap CI: `[+0.0000, +0.0000]`
- Concordant task pairs (no synergy/anti-synergy): `5`
- Synergistic pairs (R×E > 0): `0`
- Anti-synergistic pairs (R×E < 0): `0`

## Task Attribution

| Task | C00 | C10 | C01 | C11 | Category |
| --- | --- | --- | --- | --- | --- |
| `holdout_v2_crop_flip_v_task` | ✗ | ✓ | ✗ | ✓ | `refinement_resolves` |
| `holdout_v2_crop_rotate90_task` | ✗ | ✓ | ✗ | ✓ | `refinement_resolves` |
| `holdout_v2_flip_h_task` | ✓ | ✓ | ✓ | ✓ | `all_solve` |
| `holdout_v2_largest_rotate180_task` | ✗ | ✓ | ✗ | ✓ | `refinement_resolves` |
| `holdout_v2_rotate270_task` | ✓ | ✓ | ✓ | ✓ | `all_solve` |

### Attribution Category Counts

| Category | Count |
| --- | --- |
| `all_solve` | 2 |
| `refinement_resolves` | 3 |
