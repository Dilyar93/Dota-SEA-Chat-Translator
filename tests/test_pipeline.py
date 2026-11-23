import queue
import threading
import unittest

import numpy as np

from app.capture.dota_window import DotaWindow, ScreenRect
from app.capture.screen_capture import CapturedFrame
from app.language.detector import LanguageResult
from app.ocr.paddle_backend import OCRBatch, OCRToken
from app.ocr.line_reconstruction import OCRLine
from app.pipeline import CapturePipeline, MessageProcessor, put_latest


CONFIG = {
    "general": {"enabled": True},
    "capture": {"black_frame_limit": 3},
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
        image = np.full((40, 100, 3), 255, dtype=np.uint8)
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

    def test_each_request_captures_once_and_can_repeat_the_same_chat(self):
        messages = []
        received = threading.Event()
        capture = FakeCapture(3)

        def on_message(message):
            messages.append(message)
            received.set()

        pipeline = CapturePipeline(
            CONFIG,
            on_message,
            window_provider=lambda: DotaWindow(1, "Dota 2", ScreenRect(0, 0, 100, 40), True),
            capture_factory=lambda _limit: capture,
            backend=FakeBackend(),
            language_detector=FakeLanguageDetector(),
        )
        pipeline.start()
        self.addCleanup(pipeline.stop)
        self.assertFalse(received.wait(0.1))
        self.assertEqual(capture.count, 0)

        self.assertTrue(pipeline.capture_once())
        self.assertTrue(received.wait(1))
        self.assertEqual(capture.count, 1)
        pipeline.frames.join()

        received.clear()
        self.assertTrue(pipeline.capture_once())
        self.assertTrue(received.wait(1))
        self.assertEqual(capture.count, 2)
        self.assertEqual([message.message for message in messages], ["jangan mid", "jangan mid"])

    def test_capture_ignores_other_windows_and_disabled_translation(self):
        client = ScreenRect(0, 0, 100, 40)
        current = DotaWindow(1, "Dota 2", client, False)
        capture = FakeCapture(3)
        pipeline = CapturePipeline(
            CONFIG,
            lambda _message: None,
            window_provider=lambda: current,
            capture_factory=lambda _limit: capture,
            backend=FakeBackend(),
            language_detector=FakeLanguageDetector(),
        )
        pipeline.start()
        self.addCleanup(pipeline.stop)
        self.assertFalse(pipeline.capture_once())
        current = DotaWindow(1, "Dota 2", client, True)
        pipeline.set_enabled(False)
        self.assertFalse(pipeline.capture_once())
        self.assertEqual(capture.count, 0)

    def test_translation_runs_on_its_own_worker(self):
        translated = []
        received = threading.Event()
        pipeline = CapturePipeline(
            CONFIG,
            lambda _message: None,
            on_translation=lambda message: (translated.append(message), received.set()),
            window_provider=lambda: DotaWindow(1, "Dota 2", ScreenRect(0, 0, 100, 40), True),
            capture_factory=FakeCapture,
            backend=FakeBackend(),
            language_detector=FakeLanguageDetector(),
            translation_service=FakeTranslationService(),
        )
        pipeline.start()
        self.addCleanup(pipeline.stop)
        self.assertIn("translation", [thread.name for thread in pipeline.threads])
        self.assertTrue(pipeline.capture_once())
        self.assertTrue(received.wait(1))
        self.assertEqual(translated[0].text, "中文：jangan mid (id)")

    def test_empty_translation_produces_feedback_instead_of_a_subtitle(self):
        feedback = queue.Queue()
        translated = []

        class EmptyTranslationService:
            def translate(self, _text, _source_lang):
                return " "

        pipeline = CapturePipeline(
            CONFIG,
            lambda _message: None,
            on_status=feedback.put,
            on_translation=translated.append,
            window_provider=lambda: DotaWindow(1, "Dota 2", ScreenRect(0, 0, 100, 40), True),
            capture_factory=FakeCapture,
            backend=FakeBackend(),
            language_detector=FakeLanguageDetector(),
            translation_service=EmptyTranslationService(),
        )
        pipeline.start()
        self.addCleanup(pipeline.stop)
        self.assertTrue(pipeline.capture_once())
        self.assertEqual(
            [feedback.get(timeout=1) for _ in range(3)],
            ["Recognizing chat", "Translating chat", "No translated text"],
        )
        self.assertEqual(translated, [])

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
            backend=BrokenBackend(),
            language_detector=FakeLanguageDetector(),
        )
        with self.assertLogs(level="ERROR"):
            pipeline.start()
            self.addCleanup(pipeline.stop)
            self.assertTrue(pipeline.capture_once())
            self.assertTrue(failed.wait(1))
            self.assertTrue(next(thread for thread in pipeline.threads if thread.name == "ocr").is_alive())


if __name__ == "__main__":
    unittest.main()
