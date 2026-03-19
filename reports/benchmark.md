# Benchmark Report: all

| Metric | Value |
| --- | --- |
| Split | all |
| Tasks | 19 |
| Test cases | 19 |
| Attempt 1 exact rate | 0.842 |
| Attempt 1 or 2 exact rate | 0.842 |
| Attempt 2 rescues | 0 |
| Average runtime ms | 4.158 |
| Max runtime ms | 13.591 |
| Average generated hypotheses | 9.42 |
| Average first-pass survivors | 5.42 |
| Average refined hypotheses | 26.53 |
| Average belief | 0.842 |
| Average disbelief | 0.053 |
| Average uncertainty | 0.105 |
| Average winning score | 0.869 |

## Failure Classes

| Primary Class | Count |
| --- | --- |
| unsupported_pattern | 3 |

## Per Task

| Task | Split | Attempt 1 | Solved by Attempt 2 | Runtime ms | Winner | Failure |
| --- | --- | --- | --- | --- | --- | --- |
| ambiguous_competing_regression_task | all | yes | yes | 13.591 | largest_object -> flip_horizontal |  |
| color_map_task | all | yes | yes | 4.714 | color_map_[(0, 0), (1, 3), (2, 4)] |  |
| crop_bbox_task | all | yes | yes | 3.048 | crop_to_content |  |
| crop_rotate_task | all | yes | yes | 3.420 | crop_to_content -> rotate90 |  |
| holdout_composition_crop_flip_task | all | yes | yes | 3.740 | crop_to_content -> flip_horizontal |  |
| holdout_composition_largest_rotate_task | all | yes | yes | 3.542 | largest_object -> flip_vertical |  |
| holdout_flip_vertical_task | all | yes | yes | 3.610 | flip_vertical |  |
| holdout_rotate180_task | all | yes | yes | 4.339 | rotate180 |  |
| holdout_translate_task | all | yes | yes | 3.960 | translate_to_origin |  |
| identity_task | all | yes | yes | 4.559 | identity |  |
| object_count_mismatch_regression_task | all | yes | yes | 3.778 | identity |  |
| reflect_task | all | yes | yes | 3.622 | flip_horizontal |  |
| rotate_task | all | yes | yes | 4.327 | rotate90 |  |
| shape_mismatch_regression_task | all | yes | yes | 2.874 | crop_to_content |  |
| tile_task | all | yes | yes | 2.859 | tile_2x2 |  |
| translate_task | all | yes | yes | 3.973 | translate_to_origin |  |
| unsupported_pattern_four_objects_task | all | no | no | 3.296 | crop_to_content | unsupported_pattern |
| unsupported_pattern_task | all | no | no | 2.819 | crop_to_content | unsupported_pattern |
| unsupported_pattern_three_objects_task | all | no | no | 2.925 | crop_to_content | unsupported_pattern |