# Benchmark Report: regression

| Metric | Value |
| --- | --- |
| Split | regression |
| Tasks | 7 |
| Test cases | 7 |
| Attempt 1 exact rate | 0.571 |
| Attempt 1 or 2 exact rate | 0.571 |
| Attempt 2 rescues | 0 |
| Average runtime ms | 4.682 |
| Max runtime ms | 13.388 |
| Average generated hypotheses | 9.29 |
| Average first-pass survivors | 3.71 |
| Average refined hypotheses | 20.57 |
| Average belief | 0.571 |
| Average disbelief | 0.143 |
| Average uncertainty | 0.286 |
| Average winning score | 0.387 |

## Failure Classes

| Primary Class | Count |
| --- | --- |
| unsupported_pattern | 3 |

## Per Task

| Task | Split | Attempt 1 | Solved by Attempt 2 | Runtime ms | Winner | Failure |
| --- | --- | --- | --- | --- | --- | --- |
| ambiguous_competing_regression_task | regression | yes | yes | 13.388 | largest_object -> flip_horizontal |  |
| crop_rotate_task | regression | yes | yes | 3.626 | crop_to_content -> rotate90 |  |
| object_count_mismatch_regression_task | regression | yes | yes | 3.770 | identity |  |
| shape_mismatch_regression_task | regression | yes | yes | 2.891 | crop_to_content |  |
| unsupported_pattern_four_objects_task | regression | no | no | 3.354 | crop_to_content | unsupported_pattern |
| unsupported_pattern_task | regression | no | no | 2.759 | crop_to_content | unsupported_pattern |
| unsupported_pattern_three_objects_task | regression | no | no | 2.986 | crop_to_content | unsupported_pattern |