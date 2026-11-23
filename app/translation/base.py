"""Translation backend contract required by the application."""


class Translator:
    def prepare(self) -> None:
        """Load any local models before the first translation."""

    def translate(self, text: str, source_lang: str, target_lang: str = "zh") -> str:
        raise NotImplementedError

