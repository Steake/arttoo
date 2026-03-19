# Uncertainty Audit

> ⚠️  blind_holdout and all-split data appear in this audit for transparency. Do not use these rows to tune the solver.

This audit checks whether uncertainty is present, calibrated, and decision-relevant.

| Split | Tasks | Solved | Unsolved | Avg unc (all) | Avg unc (solved) | Avg unc (unsolved) | Tasks w/ nonzero unc | Epistemic reorderings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dev | 8 | 8 | 0 | 0.0000 | 0.0000 | n/a | 0 | 0 |
| regression | 6 | 3 | 3 | 0.3333 | 0.0000 | 0.6667 | 2 | 0 |
| blind_holdout ⚠️ | 3 | 3 | 0 | 0.0000 | 0.0000 | n/a | 0 | 0 |
| all ⚠️ | 16 | 13 | 3 | 0.1250 | 0.0000 | 0.6667 | 2 | 0 |

### Uncertainty Decision-Relevance Verdict

**Uncertainty is non-zero in 2/16 tasks.** 
On the regression split: avg uncertainty for **solved** tasks = 0.000, for **unsolved** tasks = 0.667.

**Uncertainty did not affect final ranking in any task.** In all observed tasks, the highest-belief hypothesis also had the highest score. This is expected when tasks have clean binary signal: belief alone drives ranking. Uncertainty would become decision-relevant on tasks where multiple hypotheses have non-zero partial match across training pairs — i.e. genuinely ambiguous tasks.

**Conclusion:** Uncertainty is correctly computed and non-zero where partial matches occur (primarily unsupported-pattern regression tasks). It is not currently decision-relevant because the fixture suite lacks tasks with *competing partial hypotheses* — tasks where two or more candidates each partially satisfy training pairs. Adding such tasks would make epistemic ranking demonstrably superior to belief-only ranking.

## Per-Task Uncertainty Detail (canonical split assignment)

Each task shown once, using its most specific split (dev/regression/blind_holdout). The 'Top-5 unc spread' column shows the range of uncertainty across the top-5 ranked hypotheses — a nonzero value means the solver had competing candidates with different uncertainty levels, even if the winning hypothesis was certain.

| Task | Split | Solved | Winning uncertainty | Top-5 unc spread |
| --- | --- | --- | --- | --- |
| color_map_task | dev | yes | 0.0000 | 1.0000 |
| crop_bbox_task | dev | yes | 0.0000 | 0.0000 |
| crop_rotate_task | dev | yes | 0.0000 | 1.0000 |
| identity_task | dev | yes | 0.0000 | 0.0000 |
| reflect_task | dev | yes | 0.0000 | 0.0000 |
| rotate_task | dev | yes | 0.0000 | 0.0000 |
| tile_task | dev | yes | 0.0000 | 1.0000 |
| translate_task | dev | yes | 0.0000 | 1.0000 |
| crop_rotate_task | regression | yes | 0.0000 | 1.0000 |
| object_count_mismatch_regression_task | regression | yes | 0.0000 | 0.5000 |
| shape_mismatch_regression_task | regression | yes | 0.0000 | 0.0000 |
| unsupported_pattern_four_objects_task | regression | no | 0.0000 | 0.0000 |
| unsupported_pattern_task | regression | no | 1.0000 | 0.0000 |
| unsupported_pattern_three_objects_task | regression | no | 1.0000 | 0.0000 |
| holdout_flip_vertical_task | blind_holdout | yes | 0.0000 | 0.0000 |
| holdout_rotate180_task | blind_holdout | yes | 0.0000 | 0.0000 |
| holdout_translate_task | blind_holdout | yes | 0.0000 | 1.0000 |