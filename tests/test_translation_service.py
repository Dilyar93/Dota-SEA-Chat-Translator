import unittest

from app.translation.glossary import Glossary
from app.translation.service import TranslationService


class FakeTranslator:
    def __init__(self):
        self.calls = []

    def translate(self, text, source_lang, target_lang="zh"):
        self.calls.append((text, source_lang, target_lang))
        return text


class TranslationServiceTests(unittest.TestCase):
    def test_glossary_protects_whole_terms_and_restores_values(self):
        glossary = Glossary({"rosh": "Roshan", "mid": "中路", "b": "撤"})
        protected, replacements = glossary.protect("go rosh then mid, not embarrassed")
        self.assertNotIn("rosh", protected)
        self.assertNotIn(" mid", protected)
        self.assertIn("embarrassed", protected)
        self.assertEqual(
            glossary.restore(protected, replacements),
            "go Roshan then 中路, not embarrassed",
        )

    def test_runtime_cache_uses_language_and_normalized_text(self):
        translator = FakeTranslator()
        service = TranslationService(translator, Glossary({"mid": "中路"}))
        first = service.translate("Jangan mid", "id")
        second = service.translate("  jangan   mid. ", "id")
        service.translate("jangan mid", "ms")
        self.assertEqual(first, second)
        self.assertEqual(len(translator.calls), 2)
        self.assertIn("__DOTA_TERM_0__", translator.calls[0][0])
        self.assertIn("中路", first)

    def test_unknown_language_falls_back_to_original_without_model(self):
        translator = FakeTranslator()
        service = TranslationService(translator, Glossary({"mid": "中路"}))
        self.assertEqual(service.translate("mystery mid", "unknown"), "mystery mid")
        self.assertEqual(translator.calls, [])


if __name__ == "__main__":
    unittest.main()
