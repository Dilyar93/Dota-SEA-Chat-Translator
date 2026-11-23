"""Unicode-first language detection with lazy fastText fallback."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


SUPPORTED_LANGUAGES = {"id", "ms", "tl", "th", "vi", "en", "zh"}


@dataclass(frozen=True, slots=True)
class LanguageResult:
    code: str
    confidence: float
    low_confidence: bool


def should_translate(result: LanguageResult, config: dict) -> bool:
    return not (
        (result.code == "en" and config.get("skip_english", True))
        or (result.code == "zh" and config.get("skip_chinese", True))
    )


def _default_model_loader(path: Path):
    if not path.is_file():
        raise FileNotFoundError(f"fastText language model not found: {path}")
    try:
        import fasttext
    except ImportError as error:
        raise RuntimeError("fastText is not installed; run pip install -r requirements.txt") from error
    return fasttext.load_model(str(path))


class LanguageDetector:
    def __init__(
        self,
        model_path: str | Path = "models/lid.176.bin",
        confidence_threshold: float = 0.60,
        model_loader: Callable[[Path], object] | None = None,
    ):
        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold
        self._model_loader = model_loader or _default_model_loader
        self._model = None

    def detect(self, text: str) -> LanguageResult:
        text = " ".join(text.split())
        if not text:
            return LanguageResult("unknown", 0.0, True)

        letters = max(1, sum(character.isalpha() for character in text))
        thai = sum("\u0e00" <= character <= "\u0e7f" and character.isalpha() for character in text)
        if thai >= 2 and thai / letters >= 0.30:
            return LanguageResult("th", thai / letters, False)

        cjk = sum(
            ("\u3400" <= character <= "\u4dbf" or "\u4e00" <= character <= "\u9fff")
            and character.isalpha()
            for character in text
        )
        if cjk and cjk / letters >= 0.50:
            return LanguageResult("zh", cjk / letters, False)

        try:
            if self._model is None:
                self._model = self._model_loader(self.model_path)
            # fasttext-wheel's single-string prediction is incompatible with NumPy 2.
            (labels,), (probabilities,) = self._model.predict([text], k=1)
            label = labels[0].decode() if isinstance(labels[0], bytes) else labels[0]
            code = label.removeprefix("__label__")
            confidence = float(probabilities[0])
            if code not in SUPPORTED_LANGUAGES:
                return LanguageResult("unknown", confidence, True)
            return LanguageResult(code, confidence, confidence < self.confidence_threshold)
        except Exception:
            logging.exception("Language detection failed")
            return LanguageResult("unknown", 0.0, True)
