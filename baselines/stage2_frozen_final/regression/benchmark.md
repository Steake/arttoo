# Benchmark Report: regression

| Metric | Value |
| --- | --- |
| Split | regression |
| Tasks | 4 |
| Test cases | 4 |
| Attempt 1 exact rate | 0.250 |
| Attempt 1 or 2 exact rate | 0.250 |
| Attempt 2 rescues | 0 |
| Average runtime ms | 13.889 |
| Max runtime ms | 42.214 |
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
| crop_rotate_task | regression | yes | yes | 8.288 | crop_to_content -> rotate90 |  |
| unsupported_pattern_four_objects_task | regression | no | no | 42.214 | crop_to_content | unsupported_pattern |
| unsupported_pattern_task | regression | no | no | 2.521 | crop_to_content | unsupported_pattern |
| unsupported_pattern_three_objects_task | regression | no | no | 2.534 | crop_to_content | unsupported_pattern |