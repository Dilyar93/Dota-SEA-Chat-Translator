"""Lazy PaddleOCR v3 adapter with Latin-first, Thai-fallback recognition."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping

import numpy as np


@dataclass(frozen=True, slots=True)
class OCRToken:
    text: str
    confidence: float
    box: tuple[float, float, float, float]


@dataclass(frozen=True, slots=True)
class OCRBatch:
    tokens: tuple[OCRToken, ...]
    model: str
    has_detections: bool = True

    @property
    def confidence(self) -> float:
        return sum(token.confidence for token in self.tokens) / len(self.tokens) if self.tokens else 0.0


def _default_factory(
    model_name: str,
    detection_model_dir: str | None,
    recognition_model_dir: str | None,
):
    for path in (detection_model_dir, recognition_model_dir):
        if not path or not Path(path).is_dir():
            raise FileNotFoundError(f"Local PaddleOCR model not found: {path}")
    try:
        from paddleocr import PaddleOCR
    except ImportError as error:
        raise RuntimeError("PaddleOCR is not installed; run pip install -r requirements.txt") from error
    return PaddleOCR(
        text_detection_model_name="PP-OCRv5_mobile_det",
        text_detection_model_dir=detection_model_dir,
        text_recognition_model_name=model_name,
        text_recognition_model_dir=recognition_model_dir,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        enable_mkldnn=False,
        device="cpu",
    )


def _box_bounds(box: Iterable) -> tuple[float, float, float, float]:
    values = np.asarray(box, dtype=float)
    if values.shape == (4,):
        return tuple(float(value) for value in values)
    points = values.reshape(-1, 2)
    return (
        float(points[:, 0].min()),
        float(points[:, 1].min()),
        float(points[:, 0].max()),
        float(points[:, 1].max()),
    )


def _result_data(result) -> Mapping:
    if isinstance(result, Mapping):
        return result.get("res", result)
    payload = result.json
    if callable(payload):
        payload = payload()
    return payload.get("res", payload)


def _tokens(results: Iterable[Mapping]) -> tuple[OCRToken, ...]:
    tokens: list[OCRToken] = []
    for data in results:
        texts = data.get("rec_texts", [])
        scores = data.get("rec_scores", [])
        boxes = data.get("rec_boxes")
        if boxes is None:
            boxes = data.get("rec_polys", [])
        tokens.extend(
            OCRToken(str(text).strip(), float(score), _box_bounds(box))
            for text, score, box in zip(texts, scores, boxes)
            if str(text).strip()
        )
    return tuple(tokens)


class PaddleOCRBackend:
    def __init__(
        self,
        latin_model: str = "latin_PP-OCRv5_mobile_rec",
        thai_model: str = "th_PP-OCRv5_mobile_rec",
        confidence_threshold: float = 0.55,
        detection_model_dir: str | None = None,
        latin_model_dir: str | None = None,
        thai_model_dir: str | None = None,
        factory: Callable[[str], object] | None = None,
    ):
        self.model_names = {"latin": latin_model, "thai": thai_model}
        self.confidence_threshold = confidence_threshold
        self.model_dirs = {
            "detection": detection_model_dir,
            "latin": latin_model_dir,
            "thai": thai_model_dir,
        }
        self._factory = factory
        self._engines: dict[str, object] = {}

    def _engine(self, model: str):
        if model not in self._engines:
            self._engines[model] = (
                self._factory(self.model_names[model])
                if self._factory
                else _default_factory(
                    self.model_names[model],
                    self.model_dirs["detection"],
                    self.model_dirs[model],
                )
            )
        return self._engines[model]

    def prepare(self) -> None:
        self._engine("latin")
        self._engine("thai")

    def _run(self, model: str, frame: np.ndarray) -> OCRBatch:
        data = [_result_data(result) for result in self._engine(model).predict(frame)]
        detected = any(boxes is None or len(boxes) > 0 for boxes in (item.get("dt_polys") for item in data))
        return OCRBatch(_tokens(data), model, detected)

    def recognize(
        self,
        frame: np.ndarray,
        *,
        retry_thai: Callable[[tuple[OCRToken, ...]], bool] | None = None,
    ) -> OCRBatch:
        latin = self._run("latin", frame)
        if not latin.has_detections:
            return latin
        latin_confident = bool(latin.tokens) and latin.confidence >= self.confidence_threshold
        retry_for_language = retry_thai is not None and bool(latin.tokens) and retry_thai(latin.tokens)
        if latin_confident and not retry_for_language:
            return latin

        thai = self._run("thai", frame)
        if retry_for_language and any(
            sum("\u0e00" <= char <= "\u0e7f" and char.isalpha() for char in token.text) >= 2
            for token in thai.tokens
        ):
            return thai
        if latin_confident:
            return latin
        return thai if thai.confidence > latin.confidence else latin
