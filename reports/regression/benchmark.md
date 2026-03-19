# Benchmark Report: regression

| Metric | Value |
| --- | --- |
| Split | regression |
| Tasks | 6 |
| Test cases | 6 |
| Attempt 1 exact rate | 0.500 |
| Attempt 1 or 2 exact rate | 0.500 |
| Attempt 2 rescues | 0 |
| Average runtime ms | 5.945 |
| Max runtime ms | 14.307 |
| Average generated hypotheses | 9.33 |
| Average first-pass survivors | 3.83 |
| Average refined hypotheses | 21.00 |
| Average belief | 0.500 |
| Average disbelief | 0.167 |
| Average uncertainty | 0.333 |
| Average winning score | 0.260 |

## Failure Classes

| Primary Class | Count |
| --- | --- |
| unsupported_pattern | 3 |

## Per Task

| Task | Split | Attempt 1 | Solved by Attempt 2 | Runtime ms | Winner | Failure |
| --- | --- | --- | --- | --- | --- | --- |
| crop_rotate_task | regression | yes | yes | 14.307 | crop_to_content -> rotate90 |  |
| object_count_mismatch_regression_task | regression | yes | yes | 5.959 | identity |  |
| shape_mismatch_regression_task | regression | yes | yes | 4.324 | crop_to_content |  |
| unsupported_pattern_four_objects_task | regression | no | no | 4.532 | crop_to_content | unsupported_pattern |
| unsupported_pattern_task | regression | no | no | 3.186 | crop_to_content | unsupported_pattern |
| unsupported_pattern_three_objects_task | regression | no | no | 3.364 | crop_to_content | unsupported_pattern |