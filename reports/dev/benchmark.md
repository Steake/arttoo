# Benchmark Report: dev

| Metric | Value |
| --- | --- |
| Split | dev |
| Tasks | 8 |
| Test cases | 8 |
| Attempt 1 exact rate | 1.000 |
| Attempt 1 or 2 exact rate | 1.000 |
| Attempt 2 rescues | 0 |
| Average runtime ms | 5.911 |
| Max runtime ms | 15.626 |
| Average generated hypotheses | 9.62 |
| Average first-pass survivors | 6.50 |
| Average refined hypotheses | 29.25 |
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
| color_map_task | dev | yes | yes | 15.626 | color_map_[(0, 0), (1, 3), (2, 4)] |  |
| crop_bbox_task | dev | yes | yes | 4.630 | crop_to_content |  |
| crop_rotate_task | dev | yes | yes | 5.164 | crop_to_content -> rotate90 |  |
| identity_task | dev | yes | yes | 5.479 | identity |  |
| reflect_task | dev | yes | yes | 3.967 | flip_horizontal |  |
| rotate_task | dev | yes | yes | 4.847 | rotate90 |  |
| tile_task | dev | yes | yes | 3.191 | tile_2x2 |  |
| translate_task | dev | yes | yes | 4.386 | translate_to_origin |  |