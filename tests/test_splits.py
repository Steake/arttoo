import unittest

from arc_epistemic.eval.fixtures import discover_splits, load_fixture_split


class SplitTests(unittest.TestCase):
    def test_split_discovery(self) -> None:
        splits = discover_splits("data/splits")
        self.assertIn("dev", splits)
        self.assertIn("regression", splits)
        self.assertIn("blind_holdout", splits)

    def test_split_isolation(self) -> None:
        dev_tasks = {fixture.task_id for fixture in load_fixture_split("data/fixtures", split="dev")}
        holdout_tasks = {fixture.task_id for fixture in load_fixture_split("data/fixtures", split="blind_holdout")}
        regression_tasks = {fixture.task_id for fixture in load_fixture_split("data/fixtures", split="regression")}
        self.assertTrue(dev_tasks)
        self.assertTrue(holdout_tasks)
        self.assertTrue(regression_tasks)
        self.assertTrue(dev_tasks.isdisjoint(holdout_tasks))
        self.assertIn("unsupported_pattern_task", regression_tasks)


if __name__ == "__main__":
    unittest.main()
