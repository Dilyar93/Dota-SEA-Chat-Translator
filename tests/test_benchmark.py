import unittest

from scripts.benchmark import timed


class BenchmarkTests(unittest.TestCase):
    def test_timed_uses_clock_instead_of_fixed_numbers(self):
        ticks = iter((10.0, 10.125))
        result, elapsed = timed(lambda: "measured", lambda: next(ticks))
        self.assertEqual(result, "measured")
        self.assertEqual(elapsed, 125.0)


if __name__ == "__main__":
    unittest.main()
