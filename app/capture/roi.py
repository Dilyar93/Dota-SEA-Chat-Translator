"""Resolution-independent chat-region coordinates."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from app.capture.dota_window import ScreenRect
from app.config import load_config, save_config


@dataclass(frozen=True, slots=True)
class RatioROI:
    left: float
    top: float
    width: float
    height: float

    def __post_init__(self) -> None:
        values = self.left, self.top, self.width, self.height
        if not all(math.isfinite(value) for value in values):
            raise ValueError("ROI values must be finite")
        if self.left < 0 or self.top < 0 or self.width <= 0 or self.height <= 0:
            raise ValueError("ROI must have a positive size inside the client area")
        if self.left + self.width > 1 or self.top + self.height > 1:
            raise ValueError("ROI extends beyond the client area")

    @classmethod
    def from_mapping(cls, values: Mapping[str, float]) -> "RatioROI":
        try:
            return cls(*(float(values[key]) for key in ("left", "top", "width", "height")))
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("ROI requires numeric left, top, width and height") from error

    @classmethod
    def from_screen_rect(cls, selection: ScreenRect, client: ScreenRect) -> "RatioROI":
        if client.width <= 0 or client.height <= 0:
            raise ValueError("Client area is empty")
        if (
            selection.width <= 0
            or selection.height <= 0
            or selection.left < client.left
            or selection.top < client.top
            or selection.left + selection.width > client.left + client.width
            or selection.top + selection.height > client.top + client.height
        ):
            raise ValueError("Selection must be inside the client area")
        return cls(
            (selection.left - client.left) / client.width,
            (selection.top - client.top) / client.height,
            selection.width / client.width,
            selection.height / client.height,
        )

    def to_screen_rect(self, client: ScreenRect) -> ScreenRect:
        left = round(client.left + client.width * self.left)
        top = round(client.top + client.height * self.top)
        right = round(client.left + client.width * (self.left + self.width))
        bottom = round(client.top + client.height * (self.top + self.height))
        if right <= left or bottom <= top:
            raise ValueError("ROI is too small for the current client area")
        return ScreenRect(left, top, right - left, bottom - top)

    def as_dict(self) -> dict[str, float]:
        return {
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height,
        }


def save_roi(roi: RatioROI, config_path: str | Path = "config.yaml") -> None:
    config = load_config(config_path)
    config["roi"] = roi.as_dict()
    save_config(config, config_path)

