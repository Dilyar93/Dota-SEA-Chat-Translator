import unittest
from types import SimpleNamespace

from app.translation.nllb import NLLB_LANG_MAP, NLLBTranslator


class FakeTokenizer:
    def set_src_lang_special_tokens(self, code):
        self.source_code = code

    def encode(self, text):
        self.text = text
        return [1, 2]

    def convert_ids_to_tokens(self, values):
        return [f"token-{value}" for value in values]

    def convert_tokens_to_ids(self, values):
        self.target_tokens = values
        return [3]

    def decode(self, values, skip_special_tokens):
        assert values == [3]
        assert skip_special_tokens
        return " 先别去中路。 "


class FakeEngine:
    def translate_batch(self, source, target_prefix, beam_size):
        self.source = source
        self.target_prefix = target_prefix
        self.beam_size = beam_size
        return [SimpleNamespace(hypotheses=[["zho_Hans", "translated", "</s>"]])]


class NLLBTests(unittest.TestCase):
    def test_language_mapping_matches_nllb_codes(self):
        self.assertEqual(NLLB_LANG_MAP["id"], "ind_Latn")
        self.assertEqual(NLLB_LANG_MAP["th"], "tha_Thai")
        self.assertEqual(NLLB_LANG_MAP["zh"], "zho_Hans")

    def test_model_and_tokenizer_are_lazy_and_reused(self):
        engine = FakeEngine()
        tokenizer = FakeTokenizer()
        loads = []
        translator = NLLBTranslator(
            "model",
            "tokenizer",
            engine_factory=lambda path, device, compute: loads.append((path, device, compute)) or engine,
            tokenizer_factory=lambda path: loads.append(path) or tokenizer,
        )
        self.assertEqual(loads, [])
        self.assertEqual(translator.translate("jangan pergi mid", "id"), "先别去中路。")
        self.assertEqual(translator.translate("tunggu", "ms"), "先别去中路。")
        self.assertEqual(len(loads), 2)
        self.assertEqual(tokenizer.source_code, "zsm_Latn")
        self.assertEqual(engine.target_prefix, [["zho_Hans"]])
        self.assertEqual(engine.beam_size, 1)

    def test_empty_input_does_not_load_model(self):
        translator = NLLBTranslator(
            "model", "tokenizer", engine_factory=lambda *_args: self.fail("loaded")
        )
        self.assertEqual(translator.translate("  ", "id"), "")

    def test_unknown_language_is_rejected_before_load(self):
        translator = NLLBTranslator(
            "model", "tokenizer", engine_factory=lambda *_args: self.fail("loaded")
        )
        with self.assertRaises(ValueError):
            translator.translate("bonjour", "unknown")


if __name__ == "__main__":
    unittest.main()
