"""Cheap frame differencing so OCR only runs after visible changes."""

from __future__ import annotations

import time
from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True, slots=True)
class ChangeResult:
    score: float
    trigger_ocr: bool


class ChangeDetector:
    def __init__(self, threshold: float = 5.0, debounce_ms: int = 150):
        if threshold < 0 or debounce_ms < 0:
            raise ValueError("threshold and debounce_ms cannot be negative")
        self.threshold = threshold
        self.debounce_seconds = debounce_ms / 1000
        self._previous: np.ndarray | None = None
        self._pending_since: float | None = None

    @staticmethod
    def _prepare(frame: np.ndarray) -> np.ndarray:
        if frame.ndim == 3:
            code = cv2.COLOR_BGRA2GRAY if frame.shape[2] == 4 else cv2.COLOR_BGR2GRAY
            frame = cv2.cvtColor(frame, code)
        elif frame.ndim != 2:
            raise ValueError("Frame must be a grayscale, BGR or BGRA image")
        height, width = frame.shape
        small = cv2.resize(
            frame,
            (max(1, width // 4), max(1, height // 4)),
            interpolation=cv2.INTER_AREA,
        )
        return cv2.GaussianBlur(small, (5, 5), 0)

    def update(self, frame: np.ndarray, now: float | None = None) -> ChangeResult:
        now = time.monotonic() if now is None else now
        current = self._prepare(frame)
        if self._previous is None or current.shape != self._previous.shape:
            self._previous = current
            self._pending_since = None
            return ChangeResult(0.0, False)

        score = float(cv2.absdiff(self._previous, current).mean())
        self._previous = current
        if score >= self.threshold and self._pending_since is None:
            self._pending_since = now

        trigger = (
            self._pending_since is not None
            and now - self._pending_since >= self.debounce_seconds
        )
        if trigger:
            self._pending_since = None
        return ChangeResult(score, trigger)

    def reset(self) -> None:
        self._previous = None
        self._pending_since = None

