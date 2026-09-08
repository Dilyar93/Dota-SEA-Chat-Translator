import unittest

import numpy as np

from app.ocr.paddle_backend import OCRBatch, OCRToken
from app.ocr.service import recognize_frame


class FakeBackend:
    def recognize(self, frame):
        self.shape = frame.shape
        return OCRBatch((OCRToken("Player: tunggu", 0.9, (0, 0, 100, 20)),), "latin")


class OCRServiceTests(unittest.TestCase):
    def test_one_shot_ocr_preprocesses_and_rebuilds_lines(self):
        backend = FakeBackend()
        lines = recognize_frame(
            np.zeros((10, 20, 3), dtype=np.uint8),
            {
                "latin_model": "latin",
                "thai_model": "thai",
                "confidence_threshold": 0.55,
                "preset": "normal",
                "upscale": 2,
            },
            backend,
        )
        self.assertEqual(backend.shape, (20, 40, 3))
        self.assertEqual(lines[0].text, "Player: tunggu")


if __name__ == "__main__":
    unittest.main()
