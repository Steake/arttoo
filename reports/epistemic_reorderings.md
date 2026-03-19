# Epistemic Reordering Analysis

> A **reordering** occurs when the first-pass winner (highest-ranked primitive hypothesis) is replaced by a different hypothesis after the refinement pass.  Reorderings are the primary operational signal that the co-agency refinement loop adds value beyond the primitive baseline.

## Summary by Split

| Split | Tasks | Multiple competing candidates | Nonzero 1st-pass uncertainty | Reorderings | Reorder success | Reorder failure | Unchanged correct | Unchanged incorrect |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | 19 | 19 | 6 | 4 | 4 | 0 | 12 | 3 |
| blind_holdout | 5 | 5 | 2 | 2 | 2 | 0 | 3 | 0 |
| dev | 8 | 8 | 1 | 1 | 1 | 0 | 7 | 0 |
| regression | 7 | 7 | 4 | 2 | 2 | 0 | 2 | 3 |

## Column Definitions

- **Multiple competing candidates**: tasks where ≥ 2 first-pass hypotheses are viable
  (non-zero belief, uncertainty, or score > −1.0).
- **Nonzero 1st-pass uncertainty**: tasks where the first-pass winner has uncertainty > 0,
  meaning it did not perfectly explain all training pairs.
- **Reorderings**: tasks where `first_pass_winner ≠ final_winner` after refinement.
- **Reorder success**: reordering occurred AND task was ultimately solved correctly.
- **Reorder failure**: reordering occurred AND task was still solved incorrectly.
- **Unchanged correct**: no reordering AND task solved correctly.
- **Unchanged incorrect**: no reordering AND task still wrong.

## Per-Task Detail: all

| Task | Solved | 1st-pass winner | Final winner | Reordered | Competing | 1st-pass uncertainty |
| --- | --- | --- | --- | --- | --- | --- |
| ambiguous_competing_regression_task | yes | largest_object | largest_object -> flip_horizontal | yes | 2 | 1.000 |
| color_map_task | yes | color_map_[(0, 0), (1, 3), (2, 4)] | color_map_[(0, 0), (1, 3), (2, 4)] | no | 10 | 0.000 |
| crop_bbox_task | yes | crop_to_content | crop_to_content | no | 2 | 0.000 |
| crop_rotate_task | yes | crop_to_content | crop_to_content -> rotate90 | yes | 2 | 1.000 |
| holdout_composition_crop_flip_task | yes | crop_to_content | crop_to_content -> flip_horizontal | yes | 2 | 1.000 |
| holdout_composition_largest_rotate_task | yes | largest_object | largest_object -> flip_vertical | yes | 2 | 1.000 |
| holdout_flip_vertical_task | yes | flip_vertical | flip_vertical | no | 7 | 0.000 |
| holdout_rotate180_task | yes | rotate180 | rotate180 | no | 10 | 0.000 |
| holdout_translate_task | yes | translate_to_origin | translate_to_origin | no | 9 | 0.000 |
| identity_task | yes | identity | identity | no | 11 | 0.000 |
| object_count_mismatch_regression_task | yes | identity | identity | no | 9 | 0.000 |
| reflect_task | yes | flip_horizontal | flip_horizontal | no | 7 | 0.000 |
| rotate_task | yes | rotate90 | rotate90 | no | 10 | 0.000 |
| shape_mismatch_regression_task | yes | crop_to_content | crop_to_content | no | 2 | 0.000 |
| tile_task | yes | tile_2x2 | tile_2x2 | no | 3 | 0.000 |
| translate_task | yes | translate_to_origin | translate_to_origin | no | 9 | 0.000 |
| unsupported_pattern_four_objects_task | no | crop_to_content | crop_to_content | no | 2 | 0.000 |
| unsupported_pattern_task | no | crop_to_content | crop_to_content | no | 2 | 1.000 |
| unsupported_pattern_three_objects_task | no | crop_to_content | crop_to_content | no | 2 | 1.000 |

## Per-Task Detail: blind_holdout

| Task | Solved | 1st-pass winner | Final winner | Reordered | Competing | 1st-pass uncertainty |
| --- | --- | --- | --- | --- | --- | --- |
| holdout_composition_crop_flip_task | yes | crop_to_content | crop_to_content -> flip_horizontal | yes | 2 | 1.000 |
| holdout_composition_largest_rotate_task | yes | largest_object | largest_object -> flip_vertical | yes | 2 | 1.000 |
| holdout_flip_vertical_task | yes | flip_vertical | flip_vertical | no | 7 | 0.000 |
| holdout_rotate180_task | yes | rotate180 | rotate180 | no | 10 | 0.000 |
| holdout_translate_task | yes | translate_to_origin | translate_to_origin | no | 9 | 0.000 |

## Per-Task Detail: dev

| Task | Solved | 1st-pass winner | Final winner | Reordered | Competing | 1st-pass uncertainty |
| --- | --- | --- | --- | --- | --- | --- |
| color_map_task | yes | color_map_[(0, 0), (1, 3), (2, 4)] | color_map_[(0, 0), (1, 3), (2, 4)] | no | 10 | 0.000 |
| crop_bbox_task | yes | crop_to_content | crop_to_content | no | 2 | 0.000 |
| crop_rotate_task | yes | crop_to_content | crop_to_content -> rotate90 | yes | 2 | 1.000 |
| identity_task | yes | identity | identity | no | 11 | 0.000 |
| reflect_task | yes | flip_horizontal | flip_horizontal | no | 7 | 0.000 |
| rotate_task | yes | rotate90 | rotate90 | no | 10 | 0.000 |
| tile_task | yes | tile_2x2 | tile_2x2 | no | 3 | 0.000 |
| translate_task | yes | translate_to_origin | translate_to_origin | no | 9 | 0.000 |

## Per-Task Detail: regression

| Task | Solved | 1st-pass winner | Final winner | Reordered | Competing | 1st-pass uncertainty |
| --- | --- | --- | --- | --- | --- | --- |
| ambiguous_competing_regression_task | yes | largest_object | largest_object -> flip_horizontal | yes | 2 | 1.000 |
| crop_rotate_task | yes | crop_to_content | crop_to_content -> rotate90 | yes | 2 | 1.000 |
| object_count_mismatch_regression_task | yes | identity | identity | no | 9 | 0.000 |
| shape_mismatch_regression_task | yes | crop_to_content | crop_to_content | no | 2 | 0.000 |
| unsupported_pattern_four_objects_task | no | crop_to_content | crop_to_content | no | 2 | 0.000 |
| unsupported_pattern_task | no | crop_to_content | crop_to_content | no | 2 | 1.000 |
| unsupported_pattern_three_objects_task | no | crop_to_content | crop_to_content | no | 2 | 1.000 |

## Verdict

**9 reordering(s) detected, 9 successful** (refinement found the correct answer after changing the first-pass winner).
Reorderings confirm that the co-agency refinement loop is providing value: the first-pass hypothesis was replaced by a composition that better explains the training evidence.