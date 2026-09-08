import copy
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.config import DEFAULT_CONFIG
from app.ui.settings import SettingsDialog


class SettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_values_are_bounded_and_applied(self):
        config = copy.deepcopy(DEFAULT_CONFIG)
        dialog = SettingsDialog(config)
        dialog.fps.setValue(999)
        dialog.translate_english.setChecked(True)
        dialog.max_messages.setValue(3)
        dialog.apply(config)
        self.assertEqual(config["capture"]["fps"], 30)
        self.assertFalse(config["language"]["skip_english"])
        self.assertEqual(config["overlay"]["max_messages"], 3)


if __name__ == "__main__":
    unittest.main()
