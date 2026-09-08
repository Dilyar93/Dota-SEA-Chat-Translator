"""Runtime translation cache plus glossary protection."""

from __future__ import annotations

from app.messages.normalizer import normalize_message
from app.translation.base import Translator
from app.translation.glossary import Glossary


class TranslationService:
    def __init__(self, translator: Translator, glossary: Glossary):
        self.translator = translator
        self.glossary = glossary
        self.cache: dict[tuple[str, str], str] = {}

    def translate(self, text: str, source_lang: str) -> str:
        normalized = normalize_message(text)
        if not normalized:
            return ""
        if source_lang == "unknown":
            return text
        key = source_lang, normalized
        if key not in self.cache:
            protected, replacements = self.glossary.protect(text)
            translated = self.translator.translate(protected, source_lang)
            self.cache[key] = self.glossary.restore(translated, replacements)
        return self.cache[key]


def create_translation_service(config: dict) -> TranslationService:
    if config.get("backend") != "nllb":
        raise ValueError(f"Unsupported translation backend: {config.get('backend')}")
    from app.translation.nllb import NLLBTranslator

    return TranslationService(
        NLLBTranslator(
            config["model_path"],
            config["tokenizer_path"],
            config["device"],
            config["compute_type"],
            config["target"],
        ),
        Glossary.from_yaml("resources/dota_glossary.yaml"),
    )
