"""Suppress repeated and slightly noisy OCR messages for a short window."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass

from rapidfuzz import fuzz

from app.messages.normalizer import normalize_message


@dataclass(frozen=True, slots=True)
class RecentMessage:
    normalized_text: str
    timestamp: float
    source_lang: str


class MessageDeduplicator:
    def __init__(self, window_seconds: float = 15, similarity_threshold: float = 90, max_messages: int = 100):
        self.window_seconds = window_seconds
        self.similarity_threshold = similarity_threshold
        self.recent: deque[RecentMessage] = deque(maxlen=max_messages)

    def is_new(self, text: str, timestamp: float | None = None, source_lang: str = "unknown") -> bool:
        normalized = normalize_message(text)
        if not normalized:
            return False
        now = time.monotonic() if timestamp is None else timestamp
        while self.recent and now - self.recent[0].timestamp > self.window_seconds:
            self.recent.popleft()
        if any(
            normalized == item.normalized_text
            or fuzz.ratio(normalized, item.normalized_text) >= self.similarity_threshold
            for item in self.recent
        ):
            return False
        self.recent.append(RecentMessage(normalized, now, source_lang))
        return True

