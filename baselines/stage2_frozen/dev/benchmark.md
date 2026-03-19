# Benchmark Report: dev

| Metric | Value |
| --- | --- |
| Split | dev |
| Tasks | 8 |
| Test cases | 8 |
| Attempt 1 exact rate | 1.000 |
| Attempt 1 or 2 exact rate | 1.000 |
| Attempt 2 rescues | 0 |
| Average runtime ms | 8.486 |
| Max runtime ms | 38.358 |
| Average generated hypotheses | 9.62 |
| Average first-pass survivors | 6.25 |
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
| color_map_task | dev | yes | yes | 9.340 | color_map_[(0, 0), (1, 3), (2, 4)] |  |
| crop_bbox_task | dev | yes | yes | 38.358 | crop_to_content |  |
| crop_rotate_task | dev | yes | yes | 3.183 | crop_to_content -> rotate90 |  |
| identity_task | dev | yes | yes | 3.864 | identity |  |
| reflect_task | dev | yes | yes | 3.179 | flip_horizontal |  |
| rotate_task | dev | yes | yes | 3.869 | rotate90 |  |
| tile_task | dev | yes | yes | 2.569 | tile_2x2 |  |
| translate_task | dev | yes | yes | 3.530 | translate_to_origin |  |