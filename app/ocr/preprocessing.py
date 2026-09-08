"""Small, selectable preprocessing presets for chat text."""

from __future__ import annotations

import cv2
import numpy as np


PRESETS = ("normal", "high_contrast", "light_text")


def preprocess(frame: np.ndarray, preset: str = "normal", upscale: float = 2.0) -> np.ndarray:
    if preset not in PRESETS:
        raise ValueError(f"Unknown OCR preset: {preset}")
    if upscale <= 0:
        raise ValueError("upscale must be positive")
    if frame.ndim == 2:
        bgr = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    elif frame.ndim == 3 and frame.shape[2] in (3, 4):
        bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR) if frame.shape[2] == 4 else frame
    else:
        raise ValueError("OCR frame must be grayscale, BGR or BGRA")

    scaled = cv2.resize(
        bgr,
        None,
        fx=upscale,
        fy=upscale,
        interpolation=cv2.INTER_CUBIC,
    )
    clahe = cv2.createCLAHE(clipLimit=2.0 if preset == "normal" else 3.0, tileGridSize=(8, 8))

    if preset == "normal":
        lab = cv2.cvtColor(scaled, cv2.COLOR_BGR2LAB)
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)
    if preset == "light_text":
        highlight = cv2.morphologyEx(
            gray, cv2.MORPH_TOPHAT, np.ones((3, 9), dtype=np.uint8)
        )
        gray = cv2.addWeighted(gray, 0.7, highlight, 1.3, 0)
    return cv2.cvtColor(clahe.apply(gray), cv2.COLOR_GRAY2BGR)

