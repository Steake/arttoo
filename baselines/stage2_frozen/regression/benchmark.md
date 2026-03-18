# Benchmark Report: regression

| Metric | Value |
| --- | --- |
| Split | regression |
| Tasks | 4 |
| Test cases | 4 |
| Attempt 1 exact rate | 0.250 |
| Attempt 1 or 2 exact rate | 0.250 |
| Attempt 2 rescues | 0 |
| Average runtime ms | 8.513 |
| Max runtime ms | 20.303 |
| Average generated hypotheses | 9.00 |
| Average first-pass survivors | 3.00 |
| Average refined hypotheses | 18.00 |
| Average belief | 0.250 |
| Average disbelief | 0.750 |
| Average uncertainty | 0.000 |
| Average winning score | -0.434 |

## Failure Classes

| Primary Class | Count |
| --- | --- |
| unsupported_pattern | 3 |

## Per Task

| Task | Split | Attempt 1 | Solved by Attempt 2 | Runtime ms | Winner | Failure |
| --- | --- | --- | --- | --- | --- | --- |
| crop_rotate_task | regression | yes | yes | 7.951 | crop_to_content -> rotate90 |  |
| unsupported_pattern_four_objects_task | regression | no | no | 3.327 | crop_to_content | unsupported_pattern |
| unsupported_pattern_task | regression | no | no | 2.471 | crop_to_content | unsupported_pattern |
| unsupported_pattern_three_objects_task | regression | no | no | 20.303 | crop_to_content | unsupported_pattern |