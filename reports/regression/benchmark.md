# Benchmark Report: regression

| Metric | Value |
| --- | --- |
| Split | regression |
| Tasks | 6 |
| Test cases | 6 |
| Attempt 1 exact rate | 0.500 |
| Attempt 1 or 2 exact rate | 0.500 |
| Attempt 2 rescues | 0 |
| Average runtime ms | 7.623 |
| Max runtime ms | 27.514 |
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
| crop_rotate_task | regression | yes | yes | 27.514 | crop_to_content -> rotate90 |  |
| object_count_mismatch_regression_task | regression | yes | yes | 4.544 | identity |  |
| shape_mismatch_regression_task | regression | yes | yes | 3.392 | crop_to_content |  |
| unsupported_pattern_four_objects_task | regression | no | no | 3.770 | crop_to_content | unsupported_pattern |
| unsupported_pattern_task | regression | no | no | 3.203 | crop_to_content | unsupported_pattern |
| unsupported_pattern_three_objects_task | regression | no | no | 3.316 | crop_to_content | unsupported_pattern |