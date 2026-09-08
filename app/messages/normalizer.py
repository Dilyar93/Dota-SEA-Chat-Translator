"""Stable comparison form for noisy OCR chat text."""

from __future__ import annotations

import re
import unicodedata


def normalize_message(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"([,.;:!?])\1+", r"\1", text)
    return text.rstrip(".,;:!?")

