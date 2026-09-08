"""Tray-only entry point for the screen OCR translation application."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import cv2
from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QApplication, QFileDialog, QSystemTrayIcon

from app.capture.dota_window import find_dota_window
from app.capture.roi import RatioROI, save_roi
from app.capture.screen_capture import ScreenCapture
from app.config import load_config, save_config
from app.ocr.service import recognize_frame
from app.pipeline import CapturePipeline, NewMessage, TranslatedMessage
from app.ui.calibrator import CalibrationWindow, DebugPreview
from app.ui.overlay import TranslationOverlay
from app.ui.settings import SettingsDialog
from app.ui.tray import TrayIcon


class PipelineBridge(QObject):
    message = Signal(object)
    translation = Signal(object)
    status = Signal(str)


class TestOCRWorker(QThread):
    lines_ready = Signal(object)
    failed = Signal(str)

    def __init__(self, image_path: str, ocr_config: dict):
        super().__init__()
        self.image_path = image_path
        self.ocr_config = ocr_config

    def run(self) -> None:
        try:
            image = cv2.imread(self.image_path)
            if image is None:
                raise ValueError("The selected image could not be read")
            self.lines_ready.emit(recognize_frame(image, self.ocr_config))
        except Exception as error:
            logging.exception("Test OCR failed")
            self.failed.emit(str(error))


class DesktopApp:
    def __init__(self, config_path: str | Path = "config.yaml"):
        self.config_path = Path(config_path)
        self.config = load_config(self.config_path)
        self.tray = TrayIcon(self.config["general"]["enabled"])
        self.calibrator: CalibrationWindow | None = None
        self.preview = DebugPreview()
        self.overlay = TranslationOverlay(self.config["overlay"])
        self.overlay_positioned = False
        self.ocr_worker: TestOCRWorker | None = None
        self.settings: SettingsDialog | None = None
        self.bridge = PipelineBridge()
        self.pipeline = CapturePipeline(
            self.config,
            self.bridge.message.emit,
            self.bridge.status.emit,
            self.bridge.translation.emit,
        )
        self.tray.enabled_changed.connect(self.set_enabled)
        self.tray.calibration_requested.connect(self.calibrate)
        self.tray.preview_requested.connect(self.show_preview)
        self.tray.test_ocr_requested.connect(self.test_ocr_image)
        self.tray.overlay_edit_changed.connect(self._set_overlay_edit_mode)
        self.tray.settings_requested.connect(self.show_settings)
        self.bridge.message.connect(self._show_new_message)
        self.bridge.translation.connect(self._show_translation)
        self.bridge.status.connect(self._show_pipeline_status)

    def notify(self, message: str) -> None:
        self.tray.showMessage("Dota SEA Translator", message)

    def set_enabled(self, enabled: bool) -> None:
        self.config["general"]["enabled"] = enabled
        save_config(self.config, self.config_path)
        self.pipeline.set_enabled(enabled)

    def calibrate(self) -> None:
        window = find_dota_window()
        if window is None:
            self.notify("Dota 2 window was not found.")
            return
        try:
            with ScreenCapture(self.config["capture"]["black_frame_limit"]) as capture:
                frame = capture.grab(window.client)
        except Exception:
            logging.exception("Unable to capture Dota client for calibration")
            self.notify("Screen capture failed. Try Borderless Window mode.")
            return
        if frame.suggest_borderless:
            self.notify("Capture is black. Switch Dota 2 to Borderless Window mode.")
            return
        self.calibrator = CalibrationWindow(window.client, frame.image)
        self.calibrator.roi_selected.connect(self._save_roi)
        self.calibrator.show()

    def _save_roi(self, roi: RatioROI) -> None:
        save_roi(roi, self.config_path)
        self.config["roi"] = roi.as_dict()
        self.notify("Chat area saved.")

    def show_preview(self) -> None:
        window = find_dota_window()
        if window is None:
            self.notify("Dota 2 window was not found.")
            return
        rect = RatioROI.from_mapping(self.config["roi"]).to_screen_rect(window.client)
        try:
            with ScreenCapture(self.config["capture"]["black_frame_limit"]) as capture:
                frame = capture.grab(rect)
        except Exception:
            logging.exception("Unable to capture ROI preview")
            self.notify("ROI capture failed.")
            return
        self.preview.update_frame(frame.image)
        self.preview.show()

    def test_ocr_image(self) -> None:
        if self.ocr_worker is not None and self.ocr_worker.isRunning():
            self.notify("OCR is already running.")
            return
        image_path, _filter = QFileDialog.getOpenFileName(
            None, "Test OCR Image", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if not image_path:
            return
        self.notify("Loading OCR model...")
        self.ocr_worker = TestOCRWorker(image_path, self.config["ocr"])
        self.ocr_worker.lines_ready.connect(self._show_ocr_lines)
        self.ocr_worker.failed.connect(lambda error: self.notify(f"OCR failed: {error}"))
        self.ocr_worker.finished.connect(self._ocr_finished)
        self.ocr_worker.start()

    def _show_ocr_lines(self, lines: list) -> None:
        print("OCR:")
        for line in lines:
            print(line.text)
        self.notify(f"OCR finished: {len(lines)} line(s). See console output.")

    def _ocr_finished(self) -> None:
        if self.ocr_worker is not None:
            self.ocr_worker.deleteLater()
            self.ocr_worker = None

    def _show_new_message(self, message: NewMessage) -> None:
        speaker = f"{message.speaker}: " if message.speaker else ""
        print(
            f"[{message.source_lang} {message.language_confidence:.2f}] "
            f"{speaker}{message.message}"
        )

    def _show_translation(self, message: TranslatedMessage) -> None:
        language = {
            "id": "印尼",
            "ms": "马来",
            "tl": "菲律宾",
            "th": "泰语",
            "vi": "越南",
        }.get(message.source.source_lang, "翻译")
        speaker = f"{message.source.speaker}\n" if message.source.speaker else ""
        self.overlay.add_message(f"{speaker}[{language}] {message.text}")
        if not self.overlay_positioned:
            self.overlay.move_to_default()
            self.overlay_positioned = True

    def _set_overlay_edit_mode(self, enabled: bool) -> None:
        if enabled and not self.overlay.labels:
            self.overlay.add_message("拖动此处调整字幕位置")
        self.overlay.set_edit_mode(enabled)

    def show_settings(self) -> None:
        if self.settings is not None and self.settings.isVisible():
            self.settings.raise_()
            self.settings.activateWindow()
            return
        self.settings = SettingsDialog(self.config)
        self.settings.accepted.connect(self._save_settings)
        self.settings.show()

    def _save_settings(self) -> None:
        if self.settings is None:
            return
        self.settings.apply(self.config)
        save_config(self.config, self.config_path)
        self.notify("Settings saved. Restart the app to apply all changes.")

    def _show_pipeline_status(self, status: str) -> None:
        print(status)
        if status.startswith(("Black", "Capture failed", "OCR failed")):
            self.notify(status)


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    qt_app = QApplication(sys.argv)
    qt_app.setQuitOnLastWindowClosed(False)
    if not QSystemTrayIcon.isSystemTrayAvailable():
        logging.error("No system tray is available")
        return 1
    desktop_app = DesktopApp()
    desktop_app.tray.show()
    desktop_app.pipeline.start()
    qt_app.aboutToQuit.connect(desktop_app.pipeline.stop)
    return qt_app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
