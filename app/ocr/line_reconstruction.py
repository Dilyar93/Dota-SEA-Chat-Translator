"""Rebuild chat lines from positioned OCR tokens."""

from __future__ import annotations

from dataclasses import dataclass

from app.ocr.paddle_backend import OCRToken


@dataclass(frozen=True, slots=True)
class OCRLine:
    text: str
    confidence: float
    box: tuple[float, float, float, float]


def _center_y(token: OCRToken) -> float:
    return (token.box[1] + token.box[3]) / 2


def reconstruct_lines(tokens: tuple[OCRToken, ...]) -> list[OCRLine]:
    groups: list[list[OCRToken]] = []
    for token in sorted(tokens, key=lambda item: (_center_y(item), item.box[0])):
        if not groups:
            groups.append([token])
            continue
        group = groups[-1]
        group_y = sum(_center_y(item) for item in group) / len(group)
        height = max(token.box[3] - token.box[1], *(item.box[3] - item.box[1] for item in group))
        if abs(_center_y(token) - group_y) <= max(4.0, height * 0.6):
            group.append(token)
        else:
            groups.append([token])

    lines: list[OCRLine] = []
    for group in groups:
        ordered = sorted(group, key=lambda item: item.box[0])
        lines.append(
            OCRLine(
                " ".join(item.text for item in ordered),
                sum(item.confidence for item in ordered) / len(ordered),
                (
                    min(item.box[0] for item in ordered),
                    min(item.box[1] for item in ordered),
                    max(item.box[2] for item in ordered),
                    max(item.box[3] for item in ordered),
                ),
            )
        )
    return lines

