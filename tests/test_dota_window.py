import unittest
from unittest.mock import patch

from app.capture import dota_window


class FakeWindows:
    def GetForegroundWindow(self):
        return 7

    def GetWindowText(self, handle):
        return "Dota 2" if handle == 7 else "Other"

    def GetClientRect(self, _handle):
        return 0, 0, 1920, 1080

    def ClientToScreen(self, _handle, point):
        return point[0] + 100, point[1] + 50


class DotaWindowTests(unittest.TestCase):
    def test_title_match_is_strict(self):
        self.assertTrue(dota_window.is_dota_title(" DOTA 2 "))
        self.assertFalse(dota_window.is_dota_title("Dota 2 guide - Browser"))

    def test_non_windows_safely_returns_none(self):
        with patch.object(dota_window, "win32gui", None):
            self.assertIsNone(dota_window.foreground_dota_window())
            self.assertIsNone(dota_window.find_dota_window())

    def test_foreground_client_coordinates(self):
        with patch.object(dota_window, "win32gui", FakeWindows()):
            window = dota_window.foreground_dota_window()
        self.assertEqual(
            window.client,
            dota_window.ScreenRect(left=100, top=50, width=1920, height=1080),
        )
        self.assertTrue(window.foreground)


if __name__ == "__main__":
    unittest.main()
