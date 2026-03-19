# Benchmark Report: all

| Metric | Value |
| --- | --- |
| Split | all |
| Tasks | 14 |
| Test cases | 14 |
| Attempt 1 exact rate | 0.786 |
| Attempt 1 or 2 exact rate | 0.786 |
| Attempt 2 rescues | 0 |
| Average runtime ms | 4.079 |
| Max runtime ms | 10.544 |
| Average generated hypotheses | 9.43 |
| Average first-pass survivors | 5.79 |
| Average refined hypotheses | 28.29 |
| Average belief | 0.786 |
| Average disbelief | 0.214 |
| Average uncertainty | 0.000 |
| Average winning score | 0.697 |

## Failure Classes

| Primary Class | Count |
| --- | --- |
| unsupported_pattern | 3 |

## Per Task

| Task | Split | Attempt 1 | Solved by Attempt 2 | Runtime ms | Winner | Failure |
| --- | --- | --- | --- | --- | --- | --- |
| color_map_task | all | yes | yes | 9.653 | color_map_[(0, 0), (1, 3), (2, 4)] |  |
| crop_bbox_task | all | yes | yes | 2.821 | crop_to_content |  |
| crop_rotate_task | all | yes | yes | 3.036 | crop_to_content -> rotate90 |  |
| holdout_flip_vertical_task | all | yes | yes | 3.127 | flip_vertical |  |
| holdout_rotate180_task | all | yes | yes | 3.635 | rotate180 |  |
| holdout_translate_task | all | yes | yes | 3.311 | translate_to_origin |  |
| identity_task | all | yes | yes | 3.753 | identity |  |
| reflect_task | all | yes | yes | 3.011 | flip_horizontal |  |
| rotate_task | all | yes | yes | 3.850 | rotate90 |  |
| tile_task | all | yes | yes | 2.521 | tile_2x2 |  |
| translate_task | all | yes | yes | 10.544 | translate_to_origin |  |
| unsupported_pattern_four_objects_task | all | no | no | 2.899 | crop_to_content | unsupported_pattern |
| unsupported_pattern_task | all | no | no | 2.418 | crop_to_content | unsupported_pattern |
| unsupported_pattern_three_objects_task | all | no | no | 2.531 | crop_to_content | unsupported_pattern |