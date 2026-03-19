# Benchmark Report: blind_holdout

| Metric | Value |
| --- | --- |
| Split | blind_holdout |
| Tasks | 5 |
| Test cases | 5 |
| Attempt 1 exact rate | 1.000 |
| Attempt 1 or 2 exact rate | 1.000 |
| Attempt 2 rescues | 0 |
| Average runtime ms | 5.818 |
| Max runtime ms | 13.588 |
| Average generated hypotheses | 9.20 |
| Average first-pass survivors | 5.60 |
| Average refined hypotheses | 28.80 |
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
| holdout_composition_crop_flip_task | blind_holdout | yes | yes | 13.588 | crop_to_content -> flip_horizontal |  |
| holdout_composition_largest_rotate_task | blind_holdout | yes | yes | 3.692 | largest_object -> flip_vertical |  |
| holdout_flip_vertical_task | blind_holdout | yes | yes | 3.648 | flip_vertical |  |
| holdout_rotate180_task | blind_holdout | yes | yes | 4.279 | rotate180 |  |
| holdout_translate_task | blind_holdout | yes | yes | 3.885 | translate_to_origin |  |