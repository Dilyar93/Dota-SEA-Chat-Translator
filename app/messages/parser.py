"""Separate a plausible Dota speaker prefix without dropping uncertain text."""

from __future__ import annotations

import re
from dataclasses import dataclass


CHAT_LINE = re.compile(
    r"^(?:[\[［【](?:allies|all|队友|全体|所有人)[\]］】]\s*)?"
    r"(?P<speaker>[^:：\r\n]{1,64})[:：]\s*(?P<message>.+)$",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class ParsedMessage:
    speaker: str | None
    message: str


def parse_chat_line(text: str) -> ParsedMessage:
    text = text.strip()
    match = CHAT_LINE.match(text)
    if not match:
        return ParsedMessage(None, text)
    speaker = match.group("speaker").strip()
    message = match.group("message").strip()
    return ParsedMessage(speaker, message) if speaker and message else ParsedMessage(None, text)

