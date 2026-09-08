import tempfile
import unittest
from pathlib import Path

from app.capture.dota_window import ScreenRect
from app.capture.roi import RatioROI, save_roi
from app.config import load_config


class ROITests(unittest.TestCase):
    def test_ratios_scale_with_client_resolution(self):
        roi = RatioROI(0.2, 0.5, 0.6, 0.25)
        self.assertEqual(roi.to_screen_rect(ScreenRect(0, 0, 1920, 1080)), ScreenRect(384, 540, 1152, 270))
        self.assertEqual(roi.to_screen_rect(ScreenRect(100, 50, 2560, 1440)), ScreenRect(612, 770, 1536, 360))

    def test_screen_selection_round_trips(self):
        client = ScreenRect(100, 50, 1000, 800)
        selection = ScreenRect(300, 450, 600, 200)
        self.assertEqual(RatioROI.from_screen_rect(selection, client).to_screen_rect(client), selection)

    def test_invalid_roi_is_rejected(self):
        for values in ((-0.1, 0, 0.2, 0.2), (0, 0, 0, 0.2), (0.8, 0, 0.3, 0.2)):
            with self.subTest(values=values), self.assertRaises(ValueError):
                RatioROI(*values)

    def test_save_updates_config(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            save_roi(RatioROI(0.1, 0.2, 0.3, 0.4), path)
            self.assertEqual(load_config(path)["roi"]["left"], 0.1)


if __name__ == "__main__":
    unittest.main()
