"""Event-driven capture → OCR → new-message pipeline."""

from __future__ import annotations

import logging
import queue
import threading
from dataclasses import dataclass
from typing import Callable

import numpy as np

from app.capture.change_detector import ChangeDetector
from app.capture.dota_window import find_dota_window, foreground_dota_window
from app.capture.roi import RatioROI
from app.capture.screen_capture import ScreenCapture
from app.language.detector import LanguageDetector, should_translate
from app.messages.deduplicator import MessageDeduplicator
from app.messages.parser import parse_chat_line
from app.ocr.line_reconstruction import OCRLine
from app.ocr.paddle_backend import PaddleOCRBackend
from app.ocr.service import recognize_frame
from app.translation.service import TranslationService, create_translation_service


@dataclass(frozen=True, slots=True)
class NewMessage:
    speaker: str | None
    message: str
    ocr_confidence: float
    source_lang: str
    language_confidence: float
    low_language_confidence: bool


@dataclass(frozen=True, slots=True)
class TranslatedMessage:
    source: NewMessage
    text: str


def put_latest(target: queue.Queue, item: object) -> None:
    try:
        target.put_nowait(item)
    except queue.Full:
        try:
            target.get_nowait()
        except queue.Empty:
            pass
        else:
            target.task_done()
        try:
            target.put_nowait(item)
        except queue.Full:
            pass


class MessageProcessor:
    def __init__(self, language_config: dict, detector: LanguageDetector | None = None):
        self.deduplicator = MessageDeduplicator()
        self.language_config = language_config
        self.detector = detector or LanguageDetector(
            language_config["model_path"],
            float(language_config["confidence_threshold"]),
        )

    def process(self, lines: list[OCRLine]) -> list[NewMessage]:
        messages = []
        for line in lines:
            parsed = parse_chat_line(line.text)
            if self.deduplicator.is_new(parsed.message):
                language = self.detector.detect(parsed.message)
                if should_translate(language, self.language_config):
                    messages.append(
                        NewMessage(
                            parsed.speaker,
                            parsed.message,
                            line.confidence,
                            language.code,
                            language.confidence,
                            language.low_confidence,
                        )
                    )
        return messages


class CapturePipeline:
    def __init__(
        self,
        config: dict,
        on_message: Callable[[NewMessage], None],
        on_status: Callable[[str], None] = lambda _status: None,
        on_translation: Callable[[TranslatedMessage], None] = lambda _message: None,
        window_provider: Callable | None = None,
        capture_factory: Callable[[int], ScreenCapture] = ScreenCapture,
        detector: ChangeDetector | None = None,
        backend: PaddleOCRBackend | None = None,
        language_detector: LanguageDetector | None = None,
        translation_service: TranslationService | None = None,
    ):
        self.config = config
        self.on_message = on_message
        self.on_status = on_status
        self.on_translation = on_translation
        self.window_provider = window_provider
        self.capture_factory = capture_factory
        capture_config = config["capture"]
        self.detector = detector or ChangeDetector(
            float(capture_config["change_threshold"]),
            int(capture_config["debounce_ms"]),
        )
        ocr_config = config["ocr"]
        self.backend = backend or PaddleOCRBackend(
            ocr_config["latin_model"],
            ocr_config["thai_model"],
            float(ocr_config["confidence_threshold"]),
            ocr_config.get("detection_model_path"),
            ocr_config.get("latin_model_path"),
            ocr_config.get("thai_model_path"),
        )
        self.frames: queue.Queue[np.ndarray] = queue.Queue(maxsize=2)
        self.translations: queue.Queue[NewMessage] = queue.Queue(maxsize=3)
        self.processor = MessageProcessor(config["language"], language_detector)
        translation_config = config.get("translation")
        if translation_service is None and translation_config:
            translation_service = create_translation_service(translation_config)
        self.translation_service = translation_service
        self._translator_ready = False
        self.stop_event = threading.Event()
        self.enabled = threading.Event()
        if config["general"]["enabled"]:
            self.enabled.set()
        self.threads: list[threading.Thread] = []
        self._last_status: str | None = None

    def start(self) -> None:
        if self.threads:
            return
        self.stop_event.clear()
        self.threads = [
            threading.Thread(target=self._capture_loop, name="capture", daemon=True),
            threading.Thread(target=self._ocr_loop, name="ocr", daemon=True),
        ]
        if self.translation_service is not None:
            self.threads.append(
                threading.Thread(target=self._translation_loop, name="translation", daemon=True)
            )
        for thread in self.threads:
            thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        for thread in self.threads:
            thread.join(timeout=2)
        self.threads.clear()

    def set_enabled(self, enabled: bool) -> None:
        self.enabled.set() if enabled else self.enabled.clear()

    def _status_once(self, status: str) -> None:
        if status != self._last_status:
            self._last_status = status
            self.on_status(status)

    def _capture_loop(self) -> None:
        capture_config = self.config["capture"]
        interval = 1 / max(1, int(capture_config["fps"]))
        capture = self.capture_factory(int(capture_config["black_frame_limit"]))
        try:
            while not self.stop_event.is_set():
                if not self.enabled.is_set():
                    self.detector.reset()
                    self.stop_event.wait(0.25)
                    continue
                provider = self.window_provider or (
                    foreground_dota_window
                    if self.config["general"]["pause_when_dota_inactive"]
                    else find_dota_window
                )
                window = provider()
                if window is None:
                    self.detector.reset()
                    self._status_once("Waiting for Dota 2 foreground window")
                    self.stop_event.wait(0.5)
                    continue
                try:
                    rect = RatioROI.from_mapping(self.config["roi"]).to_screen_rect(window.client)
                    frame = capture.grab(rect)
                    if frame.suggest_borderless:
                        self._status_once("Black capture detected; use Borderless Window mode")
                    elif not frame.black and self.detector.update(frame.image).trigger_ocr:
                        self._last_status = None
                        self.on_status("CHAT REGION CHANGED")
                        put_latest(self.frames, frame.image)
                except Exception:
                    logging.exception("Capture event failed")
                    self._status_once("Capture failed; recalibrate the chat area")
                self.stop_event.wait(interval)
        finally:
            capture.close()

    def _ocr_loop(self) -> None:
        while not self.stop_event.is_set():
            try:
                frame = self.frames.get(timeout=0.25)
            except queue.Empty:
                continue
            try:
                lines = recognize_frame(frame, self.config["ocr"], self.backend)
                for message in self.processor.process(lines):
                    self.on_message(message)
                    if self.translation_service is not None:
                        put_latest(self.translations, message)
            except Exception:
                logging.exception("OCR event failed")
                self._status_once("OCR failed; see the application log")
            finally:
                self.frames.task_done()

    def _translation_loop(self) -> None:
        while not self.stop_event.is_set():
            try:
                message = self.translations.get(timeout=0.25)
            except queue.Empty:
                continue
            try:
                if not self._translator_ready:
                    self._status_once("Loading translation model...")
                text = self.translation_service.translate(message.message, message.source_lang)
                self.on_translation(TranslatedMessage(message, text))
                if not self._translator_ready:
                    self._translator_ready = True
                    self._status_once("Translator Ready")
            except Exception:
                logging.exception("Translation failed")
                self.on_translation(TranslatedMessage(message, message.message))
                self._status_once("Translation failed; showing original text")
            finally:
                self.translations.task_done()
