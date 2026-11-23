import unittest

from app.language.detector import LanguageDetector, LanguageResult, should_translate


class FakeModel:
    def __init__(self, code="id", confidence=0.81):
        self.code = code
        self.confidence = confidence

    def predict(self, texts, k):
        assert k == 1
        assert isinstance(texts, list) and len(texts) == 1
        return [(f"__label__{self.code}",)], [(self.confidence,)]


class LanguageDetectorTests(unittest.TestCase):
    def test_unicode_rules_do_not_load_model(self):
        loads = []
        detector = LanguageDetector(model_loader=lambda path: loads.append(path))
        self.assertEqual(detector.detect("อย่าไปคนเดียว").code, "th")
        self.assertEqual(detector.detect("先别去中路").code, "zh")
        self.assertEqual(loads, [])

    def test_latin_detection_loads_fasttext_once(self):
        loads = []

        def load(path):
            loads.append(path)
            return FakeModel()

        detector = LanguageDetector("models/lid.176.bin", model_loader=load)
        first = detector.detect("jangan pergi mid dulu")
        second = detector.detect("tunggu sebentar")
        self.assertEqual((first.code, first.confidence), ("id", 0.81))
        self.assertEqual(second.code, "id")
        self.assertEqual(len(loads), 1)

    def test_unsupported_language_becomes_unknown(self):
        detector = LanguageDetector(model_loader=lambda _path: FakeModel("fr", 0.9))
        self.assertEqual(detector.detect("bonjour tout le monde").code, "unknown")

    def test_low_confidence_keeps_top_prediction(self):
        detector = LanguageDetector(
            confidence_threshold=0.60,
            model_loader=lambda _path: FakeModel("ms", 0.31),
        )
        result = detector.detect("tunggu dulu")
        self.assertEqual(result.code, "ms")
        self.assertTrue(result.low_confidence)

    def test_detection_failure_falls_back_to_unknown(self):
        detector = LanguageDetector(model_loader=lambda _path: (_ for _ in ()).throw(OSError("missing")))
        with self.assertLogs(level="ERROR"):
            result = detector.detect("jangan mid")
        self.assertEqual(result, LanguageResult("unknown", 0.0, True))

    def test_default_skip_policy_only_skips_english_and_chinese(self):
        config = {"skip_english": True, "skip_chinese": True}
        self.assertFalse(should_translate(LanguageResult("en", 0.9, False), config))
        self.assertFalse(should_translate(LanguageResult("zh", 1.0, False), config))
        self.assertTrue(should_translate(LanguageResult("id", 0.3, True), config))
        self.assertTrue(should_translate(LanguageResult("unknown", 0.0, True), config))


if __name__ == "__main__":
    unittest.main()
