import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PySide6.QtWidgets import QApplication

from app.capture.dota_window import ScreenRect
from app.ui.calibrator import CalibrationWindow, bgr_to_qimage


class CalibratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_bgr_conversion_preserves_dimensions(self):
        image = bgr_to_qimage(np.zeros((20, 30, 3), dtype=np.uint8))
        self.assertEqual((image.width(), image.height()), (30, 20))

    def test_window_matches_client_area(self):
        window = CalibrationWindow(
            ScreenRect(10, 20, 300, 200), np.zeros((200, 300, 3), dtype=np.uint8)
        )
        self.assertEqual((window.width(), window.height()), (300, 200))
        window.close()


if __name__ == "__main__":
    unittest.main()
