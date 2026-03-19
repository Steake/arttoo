# Benchmark Report: all

| Metric | Value |
| --- | --- |
| Split | all |
| Tasks | 16 |
| Test cases | 16 |
| Attempt 1 exact rate | 0.812 |
| Attempt 1 or 2 exact rate | 0.812 |
| Attempt 2 rescues | 0 |
| Average runtime ms | 4.984 |
| Max runtime ms | 16.278 |
| Average generated hypotheses | 9.50 |
| Average first-pass survivors | 5.88 |
| Average refined hypotheses | 28.12 |
| Average belief | 0.812 |
| Average disbelief | 0.062 |
| Average uncertainty | 0.125 |
| Average winning score | 0.816 |

## Failure Classes

| Primary Class | Count |
| --- | --- |
| unsupported_pattern | 3 |

## Per Task

| Task | Split | Attempt 1 | Solved by Attempt 2 | Runtime ms | Winner | Failure |
| --- | --- | --- | --- | --- | --- | --- |
| color_map_task | all | yes | yes | 16.278 | color_map_[(0, 0), (1, 3), (2, 4)] |  |
| crop_bbox_task | all | yes | yes | 4.620 | crop_to_content |  |
| crop_rotate_task | all | yes | yes | 5.183 | crop_to_content -> rotate90 |  |
| holdout_flip_vertical_task | all | yes | yes | 4.531 | flip_vertical |  |
| holdout_rotate180_task | all | yes | yes | 4.879 | rotate180 |  |
| holdout_translate_task | all | yes | yes | 4.500 | translate_to_origin |  |
| identity_task | all | yes | yes | 5.197 | identity |  |
| object_count_mismatch_regression_task | all | yes | yes | 4.425 | identity |  |
| reflect_task | all | yes | yes | 4.003 | flip_horizontal |  |
| rotate_task | all | yes | yes | 4.904 | rotate90 |  |
| shape_mismatch_regression_task | all | yes | yes | 3.426 | crop_to_content |  |
| tile_task | all | yes | yes | 3.149 | tile_2x2 |  |
| translate_task | all | yes | yes | 4.495 | translate_to_origin |  |
| unsupported_pattern_four_objects_task | all | no | no | 3.723 | crop_to_content | unsupported_pattern |
| unsupported_pattern_task | all | no | no | 3.113 | crop_to_content | unsupported_pattern |
| unsupported_pattern_three_objects_task | all | no | no | 3.312 | crop_to_content | unsupported_pattern |