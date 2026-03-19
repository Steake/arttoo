# Benchmark Report: blind_holdout

| Metric | Value |
| --- | --- |
| Split | blind_holdout |
| Tasks | 3 |
| Test cases | 3 |
| Attempt 1 exact rate | 1.000 |
| Attempt 1 or 2 exact rate | 1.000 |
| Attempt 2 rescues | 0 |
| Average runtime ms | 8.966 |
| Max runtime ms | 14.415 |
| Average generated hypotheses | 9.33 |
| Average first-pass survivors | 7.33 |
| Average refined hypotheses | 36.00 |
| Average belief | 1.000 |
| Average disbelief | 0.000 |
| Average uncertainty | 0.000 |
| Average winning score | 1.150 |

## Failure Classes

| Primary Class | Count |
| --- | --- |
| none | 0 |

## Per Task

| Task | Split | Attempt 1 | Solved by Attempt 2 | Runtime ms | Winner | Failure |
| --- | --- | --- | --- | --- | --- | --- |
| holdout_flip_vertical_task | blind_holdout | yes | yes | 14.415 | flip_vertical |  |
| holdout_rotate180_task | blind_holdout | yes | yes | 6.562 | rotate180 |  |
| holdout_translate_task | blind_holdout | yes | yes | 5.920 | translate_to_origin |  |