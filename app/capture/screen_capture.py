"""Capture only the selected visible-screen rectangle."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import mss
import numpy as np

from app.capture.dota_window import ScreenRect


@dataclass(frozen=True, slots=True)
class CapturedFrame:
    image: np.ndarray
    black: bool
    black_streak: int
    suggest_borderless: bool


class ScreenCapture:
    def __init__(self, black_frame_limit: int = 5, factory: Callable | None = None):
        if black_frame_limit < 1:
            raise ValueError("black_frame_limit must be positive")
        self.black_frame_limit = black_frame_limit
        self._factory = factory or mss.mss
        self._backend = None
        self._black_streak = 0

    def grab(self, rect: ScreenRect) -> CapturedFrame:
        if rect.width <= 0 or rect.height <= 0:
            raise ValueError("Capture rectangle must have a positive size")
        if self._backend is None:
            self._backend = self._factory()
        shot = self._backend.grab(rect.as_mss_monitor())
        image = shot.to_numpy(channels="BGR")
        black = image.size == 0 or int(image.max(initial=0)) <= 3
        self._black_streak = self._black_streak + 1 if black else 0
        return CapturedFrame(
            image=image,
            black=black,
            black_streak=self._black_streak,
            suggest_borderless=self._black_streak >= self.black_frame_limit,
        )

    def close(self) -> None:
        if self._backend is not None:
            self._backend.close()
            self._backend = None

    def __enter__(self) -> "ScreenCapture":
        return self

    def __exit__(self, *_error: object) -> None:
        self.close()

