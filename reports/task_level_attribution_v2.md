# Task-Level Attribution v2

| Task | Family | Ranking conflict | Refinement changed winner | C00 | C10 | C01 | C11 | Category |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| holdout_v3_refine_crop_flip_h_01_task | refinement_composition | no | yes | no | yes | no | yes | refinement_only_gain |
| holdout_v3_refine_crop_flip_h_02_task | refinement_composition | no | yes | no | yes | no | yes | refinement_only_gain |
| holdout_v3_refine_crop_flip_h_03_task | refinement_composition | no | yes | no | yes | no | yes | refinement_only_gain |
| holdout_v3_refine_crop_rotate90_01_task | refinement_composition | no | yes | no | yes | no | yes | refinement_only_gain |
| holdout_v3_refine_crop_rotate90_02_task | refinement_composition | no | yes | no | yes | no | yes | refinement_only_gain |
| holdout_v3_refine_crop_rotate90_03_task | refinement_composition | no | yes | no | yes | no | yes | refinement_only_gain |
| holdout_v3_refine_largest_rotate180_01_task | refinement_composition | no | yes | no | yes | no | yes | refinement_only_gain |
| holdout_v3_refine_largest_rotate180_02_task | refinement_composition | no | yes | no | yes | no | yes | refinement_only_gain |
| holdout_v3_control_flip_horizontal_01_task | control | no | no | yes | yes | yes | yes | control_all_agree |
| holdout_v3_control_flip_horizontal_02_task | control | no | no | yes | yes | yes | yes | control_all_agree |
| holdout_v3_control_flip_horizontal_03_task | control | no | no | yes | yes | yes | yes | control_all_agree |
| holdout_v3_control_translate_to_origin_01_task | control | no | no | yes | yes | yes | yes | control_all_agree |
| holdout_v3_control_translate_to_origin_02_task | control | no | no | yes | yes | yes | yes | control_all_agree |
| holdout_v3_control_translate_to_origin_03_task | control | no | no | yes | yes | yes | yes | control_all_agree |
| holdout_v3_control_tile_1x2_01_task | control | no | no | yes | yes | yes | yes | control_all_agree |
| holdout_v3_control_tile_1x2_02_task | control | no | no | yes | yes | yes | yes | control_all_agree |
| holdout_v3_ranking_conflict_01_task | ranking_conflict | no | yes | no | yes | no | yes | refinement_only_gain |
| holdout_v3_ranking_conflict_02_task | ranking_conflict | no | yes | no | yes | no | yes | refinement_only_gain |
| holdout_v3_ranking_conflict_03_task | ranking_conflict | no | yes | no | yes | no | yes | refinement_only_gain |
| holdout_v3_ranking_conflict_04_task | ranking_conflict | no | yes | no | yes | no | yes | refinement_only_gain |
| holdout_v3_ranking_conflict_05_task | ranking_conflict | no | yes | no | yes | no | yes | refinement_only_gain |
| holdout_v3_ranking_conflict_06_task | ranking_conflict | no | yes | no | yes | no | yes | refinement_only_gain |
| holdout_v3_ranking_conflict_07_task | ranking_conflict | no | yes | no | yes | no | yes | refinement_only_gain |
| holdout_v3_ranking_conflict_08_task | ranking_conflict | no | yes | no | yes | no | yes | refinement_only_gain |

## Telemetry Notes

- `point_estimate_first_pass_ordering` and `uncertainty_aware_first_pass_ordering` come from the frozen primitives-only pool (C00 vs C01).
- `final_ordering_after_refinement` comes from the native full pipeline (C11).
- Missing values would be reported as `unavailable`; none were withheld here.
