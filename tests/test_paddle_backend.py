import unittest

import numpy as np

from app.ocr.paddle_backend import PaddleOCRBackend


def result(text, confidence):
    return {
        "res": {
            "rec_texts": [text] if text else [],
            "rec_scores": [confidence] if text else [],
            "rec_boxes": [[0, 0, 100, 20]] if text else [],
        }
    }


class FakeEngine:
    def __init__(self, output):
        self.output = output

    def predict(self, _frame):
        return [self.output]


class PaddleBackendTests(unittest.TestCase):
    def test_high_confidence_latin_does_not_load_thai(self):
        loaded = []

        def factory(name):
            loaded.append(name)
            return FakeEngine(result("jangan mid", 0.9))

        batch = PaddleOCRBackend(factory=factory).recognize(np.zeros((10, 10, 3), dtype=np.uint8))
        self.assertEqual(batch.model, "latin")
        self.assertEqual(len(loaded), 1)
        self.assertEqual(batch.tokens[0].box, (0.0, 0.0, 100.0, 20.0))

    def test_low_latin_confidence_uses_better_thai_result(self):
        def factory(name):
            output = result("low", 0.2) if name.startswith("latin") else result("อย่าไป", 0.95)
            return FakeEngine(output)

        batch = PaddleOCRBackend(factory=factory).recognize(np.zeros((10, 10, 3), dtype=np.uint8))
        self.assertEqual(batch.model, "thai")
        self.assertEqual(batch.tokens[0].text, "อย่าไป")

    def test_empty_results_are_safe(self):
        backend = PaddleOCRBackend(factory=lambda _name: FakeEngine(result("", 0)))
        batch = backend.recognize(np.zeros((10, 10, 3), dtype=np.uint8))
        self.assertEqual(batch.tokens, ())


if __name__ == "__main__":
    unittest.main()
