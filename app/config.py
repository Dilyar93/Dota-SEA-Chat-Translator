"""YAML configuration loading and persistence."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG: dict[str, Any] = {
    "general": {
        "enabled": True,
        "offline_mode": True,
    },
    "capture": {
        "black_frame_limit": 5,
    },
    "roi": {"left": 0.20, "top": 0.58, "width": 0.60, "height": 0.27},
    "ocr": {
        "upscale": 2.0,
        "preset": "normal",
        "latin_model": "latin_PP-OCRv5_mobile_rec",
        "thai_model": "th_PP-OCRv5_mobile_rec",
        "detection_model_path": "models/PP-OCRv5_mobile_det",
        "latin_model_path": "models/latin_PP-OCRv5_mobile_rec",
        "thai_model_path": "models/th_PP-OCRv5_mobile_rec",
        "confidence_threshold": 0.55,
    },
    "language": {
        "model_path": "models/lid.176.bin",
        "confidence_threshold": 0.60,
        "skip_english": True,
        "skip_chinese": True,
    },
    "translation": {
        "backend": "nllb",
        "model_path": "models/nllb-200-distilled-600M-ct2",
        "tokenizer_path": "models/nllb-200-distilled-600M-ct2",
        "device": "cpu",
        "compute_type": "int8",
        "target": "zho_Hans",
    },
    "overlay": {
        "max_messages": 5,
        "display_seconds": 8,
        "font_size": 20,
        "opacity": 0.88,
    },
    "privacy": {"save_screenshots": False, "save_chat_logs": False},
    "debug": {"enabled": False},
}


def _merge(base: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    for key, value in values.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge(base[key], value)
        else:
            base[key] = value
    return base


def load_config(path: str | Path = "config.yaml") -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        return deepcopy(DEFAULT_CONFIG)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("Configuration root must be a mapping")
    return _merge(deepcopy(DEFAULT_CONFIG), data)


def save_config(config: dict[str, Any], path: str | Path = "config.yaml") -> None:
    Path(path).write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
