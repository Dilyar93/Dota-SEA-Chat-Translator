import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.tray import TrayIcon


class TrayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_expected_capture_actions_exist(self):
        tray = TrayIcon()
        texts = [action.text() for action in tray.menu.actions()]
        self.assertIn("Translation Enabled", texts)
        self.assertIn("Calibrate Chat Area", texts)
        self.assertIn("Debug ROI Preview", texts)
        self.assertIn("Test OCR Image", texts)
        self.assertIn("Move Overlay", texts)
        self.assertIn("Settings", texts)
        self.assertIn("Pause", texts)
        self.assertIn("Exit", texts)

    def test_pause_disables_translation(self):
        tray = TrayIcon()
        pause = next(action for action in tray.menu.actions() if action.text() == "Pause")
        pause.trigger()
        self.assertFalse(tray.enabled_action.isChecked())


if __name__ == "__main__":
    unittest.main()
