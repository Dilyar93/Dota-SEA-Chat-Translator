import unittest

import numpy as np

from app.ocr.preprocessing import PRESETS, preprocess


class PreprocessingTests(unittest.TestCase):
    def test_all_presets_preserve_type_and_upscale(self):
        source = np.full((20, 30, 3), 80, dtype=np.uint8)
        original = source.copy()
        for preset in PRESETS:
            with self.subTest(preset=preset):
                result = preprocess(source, preset, upscale=2)
                self.assertEqual(result.shape, (40, 60, 3))
                self.assertEqual(result.dtype, np.uint8)
        np.testing.assert_array_equal(source, original)

    def test_grayscale_input_is_supported(self):
        result = preprocess(np.zeros((10, 10), dtype=np.uint8), upscale=1)
        self.assertEqual(result.shape, (10, 10, 3))

    def test_unknown_preset_is_rejected(self):
        with self.assertRaises(ValueError):
            preprocess(np.zeros((10, 10), dtype=np.uint8), "magic")


if __name__ == "__main__":
    unittest.main()
