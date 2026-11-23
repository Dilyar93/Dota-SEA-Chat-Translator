"""Register the tray app's Windows translation shortcut."""

import logging
from ctypes.wintypes import MSG
from typing import Callable

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget


HOTKEY_LABEL = "F8"


class TranslateHotkey(QWidget):
    unavailable = Signal()
    ID = 1

    def __init__(self, callback: Callable[[], object]):
        super().__init__()
        self.callback = callback
        self._active = False
        self._registered = False

    def set_active(self, active: bool) -> None:
        if active == self._active:
            return

        import pywintypes
        import win32con
        import win32gui

        self._active = active
        if active:
            try:
                win32gui.RegisterHotKey(
                    int(self.winId()), self.ID, win32con.MOD_NOREPEAT, win32con.VK_F8
                )
            except pywintypes.error:
                logging.exception("Unable to register %s", HOTKEY_LABEL)
                self.unavailable.emit()
            else:
                self._registered = True
        elif self._registered:
            win32gui.UnregisterHotKey(int(self.winId()), self.ID)
            self._registered = False

    def nativeEvent(self, event_type, message):
        if self._registered and event_type == b"windows_generic_MSG":
            import win32con

            event = MSG.from_address(int(message))
            if event.message == win32con.WM_HOTKEY and event.wParam == self.ID:
                self.callback()
                return True, 0
        return False, 0
