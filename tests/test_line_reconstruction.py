import unittest

from app.ocr.line_reconstruction import reconstruct_lines
from app.ocr.paddle_backend import OCRToken


class LineReconstructionTests(unittest.TestCase):
    def test_unordered_tokens_form_ordered_lines(self):
        tokens = (
            OCRToken("mid", 0.8, (130, 10, 170, 30)),
            OCRToken("tunggu", 0.95, (90, 50, 160, 70)),
            OCRToken("Player2:", 0.9, (0, 51, 80, 71)),
            OCRToken("Player1:", 1.0, (0, 12, 80, 32)),
            OCRToken("jangan", 0.9, (85, 11, 125, 31)),
        )
        lines = reconstruct_lines(tokens)
        self.assertEqual([line.text for line in lines], ["Player1: jangan mid", "Player2: tunggu"])
        self.assertEqual(lines[0].box, (0, 10, 170, 32))

    def test_empty_input_returns_no_lines(self):
        self.assertEqual(reconstruct_lines(()), [])


if __name__ == "__main__":
    unittest.main()
