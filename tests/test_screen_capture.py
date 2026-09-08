import unittest

import numpy as np

from app.capture.dota_window import ScreenRect
from app.capture.screen_capture import ScreenCapture


class FakeShot:
    def __init__(self, image):
        self.image = image

    def to_numpy(self, channels):
        assert channels == "BGR"
        return self.image


class FakeMSS:
    def __init__(self, images):
        self.images = iter(images)
        self.monitors = []
        self.closed = False

    def grab(self, monitor):
        self.monitors.append(monitor)
        return FakeShot(next(self.images))

    def close(self):
        self.closed = True


class CaptureTests(unittest.TestCase):
    def test_capture_shape_and_monitor(self):
        backend = FakeMSS([np.full((20, 30, 3), 100, dtype=np.uint8)])
        capture = ScreenCapture(factory=lambda: backend)
        frame = capture.grab(ScreenRect(5, 7, 30, 20))
        self.assertEqual(frame.image.shape, (20, 30, 3))
        self.assertFalse(frame.black)
        self.assertEqual(backend.monitors, [{"left": 5, "top": 7, "width": 30, "height": 20}])
        capture.close()
        self.assertTrue(backend.closed)

    def test_repeated_black_frames_suggest_borderless_mode(self):
        black = np.zeros((10, 10, 3), dtype=np.uint8)
        backend = FakeMSS([black, black, black])
        capture = ScreenCapture(black_frame_limit=3, factory=lambda: backend)
        rect = ScreenRect(0, 0, 10, 10)
        self.assertFalse(capture.grab(rect).suggest_borderless)
        self.assertFalse(capture.grab(rect).suggest_borderless)
        self.assertTrue(capture.grab(rect).suggest_borderless)

    def test_non_black_frame_resets_streak(self):
        black = np.zeros((10, 10, 3), dtype=np.uint8)
        visible = np.full((10, 10, 3), 10, dtype=np.uint8)
        backend = FakeMSS([black, visible])
        capture = ScreenCapture(factory=lambda: backend)
        capture.grab(ScreenRect(0, 0, 10, 10))
        self.assertEqual(capture.grab(ScreenRect(0, 0, 10, 10)).black_streak, 0)


if __name__ == "__main__":
    unittest.main()
