"""Translation backend contract required by the application."""


class Translator:
    def translate(self, text: str, source_lang: str, target_lang: str = "zh") -> str:
        raise NotImplementedError

