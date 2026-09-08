"""Small system-tray surface for the translation application."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon


class TrayIcon(QSystemTrayIcon):
    enabled_changed = Signal(bool)
    calibration_requested = Signal()
    preview_requested = Signal()
    test_ocr_requested = Signal()
    overlay_edit_changed = Signal(bool)
    settings_requested = Signal()

    def __init__(self, enabled: bool = True):
        icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        super().__init__(icon)
        self.setToolTip("Dota SEA Translator")
        self.menu = QMenu()

        title = self.menu.addAction("Dota SEA Translator")
        title.setEnabled(False)
        self.menu.addSeparator()

        self.enabled_action = QAction("Translation Enabled", self.menu, checkable=True)
        self.enabled_action.setChecked(enabled)
        self.enabled_action.toggled.connect(self.enabled_changed)
        self.menu.addAction(self.enabled_action)

        calibrate = self.menu.addAction("Calibrate Chat Area")
        calibrate.triggered.connect(self.calibration_requested)
        preview = self.menu.addAction("Debug ROI Preview")
        preview.triggered.connect(self.preview_requested)
        test_ocr = self.menu.addAction("Test OCR Image")
        test_ocr.triggered.connect(self.test_ocr_requested)
        settings = self.menu.addAction("Settings")
        settings.triggered.connect(self.settings_requested)
        move_overlay = self.menu.addAction("Move Overlay")
        move_overlay.setCheckable(True)
        move_overlay.toggled.connect(self.overlay_edit_changed)

        pause = self.menu.addAction("Pause")
        pause.triggered.connect(lambda: self.enabled_action.setChecked(False))
        self.menu.addSeparator()
        self.menu.addAction("Exit", QApplication.quit)
        self.setContextMenu(self.menu)
