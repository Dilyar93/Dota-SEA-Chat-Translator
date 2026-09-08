"""Run OCR once against a saved ROI image."""

from __future__ import annotations

import argparse

import cv2

from app.config import load_config
from app.ocr.service import recognize_frame


def main() -> int:
    parser = argparse.ArgumentParser(description="Test OCR on one Dota chat ROI image")
    parser.add_argument("image")
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()
    image = cv2.imread(args.image)
    if image is None:
        parser.error(f"cannot read image: {args.image}")
    print("OCR:")
    for line in recognize_frame(image, load_config(args.config)["ocr"]):
        print(line.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

