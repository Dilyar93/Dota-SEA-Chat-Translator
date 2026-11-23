"""One OCR event: preprocess, recognize, then rebuild lines."""

from __future__ import annotations

from typing import Callable, Mapping

import numpy as np

from app.ocr.line_reconstruction import OCRLine, reconstruct_lines
from app.ocr.paddle_backend import PaddleOCRBackend
from app.ocr.preprocessing import preprocess


def recognize_frame(
    frame: np.ndarray,
    config: Mapping,
    backend: PaddleOCRBackend | None = None,
    *,
    retry_thai: Callable[[list[OCRLine]], bool] | None = None,
) -> list[OCRLine]:
    backend = backend or PaddleOCRBackend(
        latin_model=config["latin_model"],
        thai_model=config["thai_model"],
        confidence_threshold=float(config["confidence_threshold"]),
        detection_model_dir=config.get("detection_model_path"),
        latin_model_dir=config.get("latin_model_path"),
        thai_model_dir=config.get("thai_model_path"),
    )
    prepared = preprocess(frame, config["preset"], float(config["upscale"]))
    if retry_thai is not None and isinstance(backend, PaddleOCRBackend):
        result = backend.recognize(prepared, retry_thai=lambda tokens: retry_thai(reconstruct_lines(tokens)))
    else:
        result = backend.recognize(prepared)
    return reconstruct_lines(result.tokens)
