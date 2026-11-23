"""Mouse-driven ROI calibration over a snapshot of the Dota client."""

from __future__ import annotations

import cv2
import numpy as np
from PySide6.QtCore import QPoint, QRect, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QGuiApplication, QImage, QKeyEvent, QMouseEvent, QPainter, QPen, QPixmap, QShowEvent
from PySide6.QtWidgets import QLabel, QWidget

from app.capture.dota_window import ScreenRect
from app.capture.roi import RatioROI


def bgr_to_qimage(frame: np.ndarray) -> QImage:
    if frame.ndim == 2:
        image = np.ascontiguousarray(frame)
        height, width = image.shape
        return QImage(
            image.data, width, height, image.strides[0], QImage.Format.Format_Grayscale8
        ).copy()
    if frame.ndim != 3 or frame.shape[2] not in (3, 4):
        raise ValueError("Preview frame must be grayscale, BGR or BGRA")
    rgb = cv2.cvtColor(
        frame, cv2.COLOR_BGRA2RGBA if frame.shape[2] == 4 else cv2.COLOR_BGR2RGB
    )
    height, width, _channels = rgb.shape
    image_format = (
        QImage.Format.Format_RGBA8888
        if rgb.shape[2] == 4
        else QImage.Format.Format_RGB888
    )
    return QImage(rgb.data, width, height, rgb.strides[0], image_format).copy()


class CalibrationWindow(QWidget):
    roi_selected = Signal(object)

    def __init__(self, client: ScreenRect, screenshot: np.ndarray):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self._client = client
        self._snapshot = QPixmap.fromImage(bgr_to_qimage(screenshot))
        self._start: QPoint | None = None
        self._selection = QRect()
        self.setGeometry(client.left, client.top, client.width, client.height)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        if QGuiApplication.platformName() == "windows":
            QTimer.singleShot(0, self, self._fit_native_client)

    def _fit_native_client(self) -> None:
        import win32con
        import win32gui

        # Use desktop pixels after Qt has finished showing the logical window.
        client = self._client
        win32gui.SetWindowPos(
            int(self.winId()), win32con.HWND_TOP,
            client.left, client.top, client.width, client.height,
            win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE,
        )

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self._snapshot)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 95))
        painter.setPen(QColor("white"))
        painter.drawText(
            self.rect().adjusted(20, 20, -20, -20),
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
            "请选择 Dota 2 屏幕中下方聊天消息出现的区域（Esc 取消）",
        )
        if not self._selection.isNull():
            painter.setPen(QPen(QColor(0, 220, 120), 3))
            painter.drawRect(self._selection)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._start = event.position().toPoint()
            self._selection = QRect(self._start, self._start)
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._start is not None:
            self._selection = QRect(self._start, event.position().toPoint()).normalized().intersected(self.rect())
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton or self._start is None:
            return
        self.mouseMoveEvent(event)
        self._start = None
        if self._selection.width() < 20 or self._selection.height() < 20:
            return
        selection = ScreenRect(
            self._selection.left(),
            self._selection.top(),
            self._selection.width(),
            self._selection.height(),
        )
        client = ScreenRect(0, 0, self.width(), self.height())
        self.roi_selected.emit(RatioROI.from_screen_rect(selection, client))
        self.close()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


class DebugPreview(QLabel):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dota Chat ROI — Debug Preview")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(480, 180)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

    def update_frame(self, frame: np.ndarray) -> None:
        pixmap = QPixmap.fromImage(bgr_to_qimage(frame))
        self.setPixmap(
            pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

