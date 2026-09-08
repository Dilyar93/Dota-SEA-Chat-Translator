import unittest

import numpy as np

from app.capture.change_detector import ChangeDetector


class ChangeDetectorTests(unittest.TestCase):
    def test_static_frame_does_not_trigger(self):
        detector = ChangeDetector(threshold=5, debounce_ms=150)
        frame = np.zeros((100, 200, 3), dtype=np.uint8)
        self.assertFalse(detector.update(frame, now=0).trigger_ocr)
        self.assertFalse(detector.update(frame, now=1).trigger_ocr)

    def test_change_triggers_once_after_debounce(self):
        detector = ChangeDetector(threshold=5, debounce_ms=150)
        before = np.zeros((100, 200, 3), dtype=np.uint8)
        after = before.copy()
        after[20:80, 20:180] = 255
        detector.update(before, now=0)
        changed = detector.update(after, now=0.01)
        self.assertGreater(changed.score, 5)
        self.assertFalse(changed.trigger_ocr)
        self.assertTrue(detector.update(after, now=0.16).trigger_ocr)
        self.assertFalse(detector.update(after, now=0.32).trigger_ocr)

    def test_new_frame_size_resets_baseline(self):
        detector = ChangeDetector()
        detector.update(np.zeros((100, 100), dtype=np.uint8), now=0)
        result = detector.update(np.ones((50, 50), dtype=np.uint8) * 255, now=1)
        self.assertEqual(result.score, 0)
        self.assertFalse(result.trigger_ocr)


if __name__ == "__main__":
    unittest.main()
