# ARC Epistemic Solver

This repository now includes a runnable Python ARC-style solver in [`arc_epistemic/`](/workspace/arttoo/arc_epistemic). The implementation is engineered around a bounded thesis:

- Epistemic sovereignty: each candidate transform is kept as an explicit hypothesis with belief, disbelief, and uncertainty rather than collapsing immediately to a single best fit.
- Co-agency: a small fixed loop splits work into generator, critic, and arbiter roles so multiple plausible explanations survive one pass before final ranking.

## Practical design

The solver stays compact and deterministic:

- `generator` proposes a bounded set of primitive hypotheses from symmetries, crop and translation rules, largest-object extraction, inferred color remaps, and cheap tiling.
- `critic` evaluates exact train-pair matches first, then uses conservative partial similarity only to distinguish unresolved cases from outright contradiction.
- `arbiter` computes explicit epistemic values:
  - `belief = support_count / total_pairs`
  - `disbelief = contradiction_count / total_pairs`
  - `uncertainty = unresolved_count / total_pairs`
  - `score = belief + 0.15 * partial_credit - 0.5 * uncertainty - disbelief`
- A single refinement pass composes top survivors with one extra primitive transform, capped at depth 2.

The result emits up to two ranked attempts per test case in Kaggle submission format.

## Layout

- [`main.py`](/workspace/arttoo/main.py): CLI entrypoint
- [`arc_epistemic/solver/`](/workspace/arttoo/arc_epistemic/solver): parser, hypotheses, epistemic scoring, co-agency loop, selection, and submission formatting
- [`arc_epistemic/primitives/`](/workspace/arttoo/arc_epistemic/primitives): connected components, object extraction, symmetry, color, geometry, and pattern helpers
- [`arc_epistemic/utils/`](/workspace/arttoo/arc_epistemic/utils): grid wrapper, metrics, cache
- [`tests/`](/workspace/arttoo/tests): primitive, epistemic, and smoke tests

## Run

```bash
python -m pip install -r requirements-arc.txt
python main.py --input data/tasks.json --output submission.json
python -m unittest discover -s tests -p 'test_*.py'
```

Input can be either a single ARC task JSON or a dictionary keyed by task id. Output is Kaggle-style:

```json
{
  "task_id": [
    {
      "attempt_1": [[0, 1]],
      "attempt_2": [[1, 0]]
    }
  ]
}
```

## Current limits

This solver is intentionally bounded. It does not brute-force arbitrary ARC programs, train a model, or maintain deep search trees. It favors correctness, determinism, and a compact end-to-end pipeline over broad pattern coverage.
