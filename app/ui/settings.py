"""Small settings dialog for frequently tuned runtime values."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QSpinBox,
)


class SettingsDialog(QDialog):
    def __init__(self, config: dict):
        super().__init__()
        self.setWindowTitle("Dota SEA Translator Settings")
        form = QFormLayout(self)

        self.offline = QCheckBox()
        self.offline.setChecked(config["general"]["offline_mode"])
        self.ocr_confidence = self._double(0, 1, config["ocr"]["confidence_threshold"], 0.05)
        self.translate_english = QCheckBox()
        self.translate_english.setChecked(not config["language"]["skip_english"])
        self.translate_chinese = QCheckBox()
        self.translate_chinese.setChecked(not config["language"]["skip_chinese"])
        self.max_messages = self._spin(1, 5, config["overlay"]["max_messages"])
        self.display_seconds = self._spin(1, 60, config["overlay"]["display_seconds"])
        self.font_size = self._spin(10, 48, config["overlay"]["font_size"])
        self.opacity = self._double(0.1, 1, config["overlay"]["opacity"], 0.05)

        for label, widget in (
            ("Offline mode", self.offline),
            ("OCR confidence", self.ocr_confidence),
            ("Translate English", self.translate_english),
            ("Translate Chinese", self.translate_chinese),
            ("Overlay messages", self.max_messages),
            ("Display seconds", self.display_seconds),
            ("Font size", self.font_size),
            ("Overlay opacity", self.opacity),
        ):
            form.addRow(label, widget)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    @staticmethod
    def _spin(minimum: int, maximum: int, value: int) -> QSpinBox:
        field = QSpinBox()
        field.setRange(minimum, maximum)
        field.setValue(int(value))
        return field

    @staticmethod
    def _double(minimum: float, maximum: float, value: float, step: float = 0.1) -> QDoubleSpinBox:
        field = QDoubleSpinBox()
        field.setRange(minimum, maximum)
        field.setSingleStep(step)
        field.setValue(float(value))
        return field

    def apply(self, config: dict) -> None:
        config["general"]["offline_mode"] = self.offline.isChecked()
        config["ocr"]["confidence_threshold"] = self.ocr_confidence.value()
        config["language"]["skip_english"] = not self.translate_english.isChecked()
        config["language"]["skip_chinese"] = not self.translate_chinese.isChecked()
        config["overlay"]["max_messages"] = self.max_messages.value()
        config["overlay"]["display_seconds"] = self.display_seconds.value()
        config["overlay"]["font_size"] = self.font_size.value()
        config["overlay"]["opacity"] = self.opacity.value()
