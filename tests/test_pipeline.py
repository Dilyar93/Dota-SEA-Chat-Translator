import queue
import threading
import time
import unittest

import numpy as np

from app.capture.change_detector import ChangeDetector
from app.capture.dota_window import DotaWindow, ScreenRect
from app.capture.screen_capture import CapturedFrame
from app.language.detector import LanguageResult
from app.ocr.paddle_backend import OCRBatch, OCRToken
from app.ocr.line_reconstruction import OCRLine
from app.pipeline import CapturePipeline, MessageProcessor, put_latest


CONFIG = {
    "general": {"enabled": True, "pause_when_dota_inactive": True},
    "capture": {"fps": 100, "change_threshold": 5, "debounce_ms": 0, "black_frame_limit": 3},
    "roi": {"left": 0, "top": 0, "width": 1, "height": 1},
    "ocr": {
        "upscale": 1,
        "preset": "normal",
        "latin_model": "latin",
        "thai_model": "thai",
        "confidence_threshold": 0.55,
    },
    "language": {
        "model_path": "models/lid.176.bin",
        "confidence_threshold": 0.60,
        "skip_english": True,
        "skip_chinese": True,
    },
}


class FakeCapture:
    def __init__(self, _limit):
        self.count = 0

    def grab(self, _rect):
        self.count += 1
        value = 0 if self.count == 1 else 255
        image = np.full((40, 100, 3), value, dtype=np.uint8)
        return CapturedFrame(image, False, 0, False)

    def close(self):
        pass


class FakeBackend:
    def recognize(self, _frame):
        return OCRBatch((OCRToken("A: jangan mid", 0.9, (0, 0, 100, 20)),), "latin")


class BrokenBackend:
    def recognize(self, _frame):
        raise RuntimeError("model failure")


class FakeLanguageDetector:
    def __init__(self, code="id"):
        self.code = code

    def detect(self, _text):
        return LanguageResult(self.code, 0.81, False)


class FakeTranslationService:
    def translate(self, text, source_lang):
        return f"中文：{text} ({source_lang})"


class PipelineTests(unittest.TestCase):
    def test_message_processor_skips_english_but_keeps_sea_text(self):
        line = [OCRLine("A: wait", 0.9, (0, 0, 100, 20))]
        english = MessageProcessor(CONFIG["language"], FakeLanguageDetector("en"))
        self.assertEqual(english.process(line), [])

        indonesian = MessageProcessor(CONFIG["language"], FakeLanguageDetector("id"))
        self.assertEqual(indonesian.process(line)[0].source_lang, "id")

    def test_full_capture_event_emits_one_new_message(self):
        messages = []
        received = threading.Event()

        def on_message(message):
            messages.append(message)
            received.set()

        pipeline = CapturePipeline(
            CONFIG,
            on_message,
            window_provider=lambda: DotaWindow(1, "Dota 2", ScreenRect(0, 0, 100, 40), True),
            capture_factory=FakeCapture,
            detector=ChangeDetector(5, 0),
            backend=FakeBackend(),
            language_detector=FakeLanguageDetector(),
        )
        pipeline.start()
        self.assertTrue(received.wait(1))
        time.sleep(0.05)
        pipeline.stop()
        self.assertEqual([message.message for message in messages], ["jangan mid"])

    def test_translation_runs_on_its_own_worker(self):
        translated = []
        received = threading.Event()
        pipeline = CapturePipeline(
            CONFIG,
            lambda _message: None,
            on_translation=lambda message: (translated.append(message), received.set()),
            window_provider=lambda: DotaWindow(1, "Dota 2", ScreenRect(0, 0, 100, 40), True),
            capture_factory=FakeCapture,
            detector=ChangeDetector(5, 0),
            backend=FakeBackend(),
            language_detector=FakeLanguageDetector(),
            translation_service=FakeTranslationService(),
        )
        pipeline.start()
        self.assertIn("translation", [thread.name for thread in pipeline.threads])
        self.assertTrue(received.wait(1))
        pipeline.stop()
        self.assertEqual(translated[0].text, "中文：jangan mid (id)")

    def test_bounded_queue_drops_old_frame(self):
        frames = queue.Queue(maxsize=2)
        put_latest(frames, np.array([1]))
        put_latest(frames, np.array([2]))
        put_latest(frames, np.array([3]))
        self.assertEqual([frames.get().item(), frames.get().item()], [2, 3])

    def test_ocr_failure_is_reported_without_stopping_worker(self):
        failed = threading.Event()
        pipeline = CapturePipeline(
            CONFIG,
            lambda _message: None,
            on_status=lambda status: failed.set() if status.startswith("OCR failed") else None,
            window_provider=lambda: DotaWindow(1, "Dota 2", ScreenRect(0, 0, 100, 40), True),
            capture_factory=FakeCapture,
            detector=ChangeDetector(5, 0),
            backend=BrokenBackend(),
            language_detector=FakeLanguageDetector(),
        )
        with self.assertLogs(level="ERROR"):
            pipeline.start()
            self.assertTrue(failed.wait(1))
            self.assertTrue(next(thread for thread in pipeline.threads if thread.name == "ocr").is_alive())
            pipeline.stop()


if __name__ == "__main__":
    unittest.main()
