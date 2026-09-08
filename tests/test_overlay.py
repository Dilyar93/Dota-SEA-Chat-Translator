import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.ui.overlay import TranslationOverlay


class OverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.overlay = TranslationOverlay(
            {"max_messages": 2, "display_seconds": 60, "font_size": 18, "opacity": 0.8}
        )

    def tearDown(self):
        self.overlay.close()

    def test_window_is_focus_safe_and_click_through(self):
        flags = self.overlay.windowFlags()
        self.assertTrue(flags & Qt.WindowType.Tool)
        self.assertTrue(flags & Qt.WindowType.FramelessWindowHint)
        self.assertTrue(flags & Qt.WindowType.WindowStaysOnTopHint)
        self.assertTrue(flags & Qt.WindowType.WindowDoesNotAcceptFocus)
        self.assertTrue(flags & Qt.WindowType.WindowTransparentForInput)

    def test_message_limit_and_edit_mode(self):
        for text in ("一", "二", "三"):
            self.overlay.add_message(text)
        self.assertEqual([label.text() for label in self.overlay.labels], ["二", "三"])
        self.overlay.set_edit_mode(True)
        self.assertFalse(self.overlay.windowFlags() & Qt.WindowType.WindowTransparentForInput)


if __name__ == "__main__":
    unittest.main()
