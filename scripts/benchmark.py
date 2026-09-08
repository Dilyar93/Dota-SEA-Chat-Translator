"""Measure the real local MVP pipeline against the current Dota chat ROI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from time import perf_counter
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.capture.change_detector import ChangeDetector
from app.capture.dota_window import foreground_dota_window
from app.capture.roi import RatioROI
from app.capture.screen_capture import ScreenCapture
from app.config import load_config
from app.language.detector import LanguageDetector
from app.messages.parser import parse_chat_line
from app.ocr.paddle_backend import PaddleOCRBackend
from app.ocr.service import recognize_frame
from app.translation.nllb import NLLB_LANG_MAP
from app.translation.service import create_translation_service


def timed(action: Callable, clock: Callable[[], float] = perf_counter):
    started = clock()
    result = action()
    return result, (clock() - started) * 1000


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    window = foreground_dota_window()
    if window is None:
        parser.error("Dota 2 must be the foreground window during the benchmark")

    roi = RatioROI.from_mapping(config["roi"]).to_screen_rect(window.client)
    capture = ScreenCapture(config["capture"]["black_frame_limit"])
    total_started = perf_counter()
    try:
        frame, capture_ms = timed(lambda: capture.grab(roi))
    finally:
        capture.close()
    if frame.black:
        parser.error("captured ROI is black; use Borderless Window mode")

    detector = ChangeDetector(
        config["capture"]["change_threshold"], config["capture"]["debounce_ms"]
    )
    _change, change_ms = timed(lambda: detector.update(frame.image))
    ocr = PaddleOCRBackend(
        config["ocr"]["latin_model"],
        config["ocr"]["thai_model"],
        config["ocr"]["confidence_threshold"],
        config["ocr"]["detection_model_path"],
        config["ocr"]["latin_model_path"],
        config["ocr"]["thai_model_path"],
    )
    lines, ocr_ms = timed(lambda: recognize_frame(frame.image, config["ocr"], ocr))
    if not lines:
        parser.error("no chat text was recognized; keep a foreign chat line visible")
    message = parse_chat_line(lines[-1].text).message

    language_detector = LanguageDetector(
        config["language"]["model_path"], config["language"]["confidence_threshold"]
    )
    language, language_ms = timed(lambda: language_detector.detect(message))
    if language.code not in NLLB_LANG_MAP or language.code == "zh":
        parser.error(f"recognized language {language.code!r} cannot benchmark translation")
    translator = create_translation_service(config["translation"])
    _translated, translation_ms = timed(
        lambda: translator.translate(message, language.code)
    )
    total_ms = (perf_counter() - total_started) * 1000

    for name, elapsed in (
        ("Capture", capture_ms),
        ("ChangeDetect", change_ms),
        ("OCR", ocr_ms),
        ("LangDetect", language_ms),
        ("Translation", translation_ms),
        ("Total", total_ms),
    ):
        print(f"{name + ':':<14}{elapsed:8.1f} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
