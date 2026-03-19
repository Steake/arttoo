# Benchmark Report: dev

| Metric | Value |
| --- | --- |
| Split | dev |
| Tasks | 8 |
| Test cases | 8 |
| Attempt 1 exact rate | 1.000 |
| Attempt 1 or 2 exact rate | 1.000 |
| Attempt 2 rescues | 0 |
| Average runtime ms | 5.998 |
| Max runtime ms | 15.812 |
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
| color_map_task | dev | yes | yes | 15.812 | color_map_[(0, 0), (1, 3), (2, 4)] |  |
| crop_bbox_task | dev | yes | yes | 4.617 | crop_to_content |  |
| crop_rotate_task | dev | yes | yes | 5.156 | crop_to_content -> rotate90 |  |
| identity_task | dev | yes | yes | 5.857 | identity |  |
| reflect_task | dev | yes | yes | 3.987 | flip_horizontal |  |
| rotate_task | dev | yes | yes | 4.915 | rotate90 |  |
| tile_task | dev | yes | yes | 3.186 | tile_2x2 |  |
| translate_task | dev | yes | yes | 4.452 | translate_to_origin |  |