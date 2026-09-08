"""Focus-safe, click-through translation subtitles."""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsOpacityEffect,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class TranslationOverlay(QWidget):
    def __init__(self, config: dict):
        super().__init__()
        self.max_messages = int(config["max_messages"])
        self.display_ms = int(float(config["display_seconds"]) * 1000)
        self.font_size = int(config["font_size"])
        self.opacity = max(0.0, min(1.0, float(config["opacity"])))
        self.labels: list[QLabel] = []
        self.animations: dict[QLabel, QPropertyAnimation] = {}
        self.edit_mode = False
        self.drag_offset = QPoint()

        self.base_flags = (
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setWindowFlags(self.base_flags | Qt.WindowType.WindowTransparentForInput)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(4)

    def add_message(self, text: str) -> None:
        if not text.strip():
            return
        while len(self.labels) >= self.max_messages:
            self._remove(self.labels[0])
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(
            f"color: white; background: rgba(0, 0, 0, {round(self.opacity * 255)});"
            f"font-size: {self.font_size}px; padding: 6px 10px; border-radius: 4px;"
        )
        self.labels.append(label)
        self.layout.addWidget(label)
        self.adjustSize()
        self.show()
        QTimer.singleShot(self.display_ms, lambda item=label: self._fade(item))

    def set_edit_mode(self, enabled: bool) -> None:
        was_visible = self.isVisible()
        self.edit_mode = enabled
        self.setWindowFlags(
            self.base_flags
            if enabled
            else self.base_flags | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, not enabled)
        if was_visible:
            self.show()

    def move_to_default(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        area = screen.availableGeometry()
        self.adjustSize()
        self.move(area.right() - self.width() - 80, area.bottom() - self.height() - 180)

    def _fade(self, label: QLabel) -> None:
        if label not in self.labels:
            return
        effect = QGraphicsOpacityEffect(label)
        label.setGraphicsEffect(effect)
        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(500)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.finished.connect(lambda: self._remove(label))
        self.animations[label] = animation
        animation.start()

    def _remove(self, label: QLabel) -> None:
        if label not in self.labels:
            return
        self.labels.remove(label)
        self.animations.pop(label, None)
        self.layout.removeWidget(label)
        label.deleteLater()
        self.adjustSize()
        if not self.labels and not self.edit_mode:
            self.hide()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self.edit_mode and event.button() == Qt.MouseButton.LeftButton:
            self.drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.edit_mode and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_offset)
            event.accept()
