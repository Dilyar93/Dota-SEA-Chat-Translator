"""Protect Dota terms from model mistranslation."""

from __future__ import annotations

import re
from pathlib import Path

import yaml


class Glossary:
    def __init__(self, terms: dict[str, str]):
        if not terms:
            raise ValueError("Glossary cannot be empty")
        self.terms = terms
        alternatives = "|".join(
            re.escape(term) for term in sorted(terms, key=len, reverse=True)
        )
        self.pattern = re.compile(rf"(?<!\w)(?:{alternatives})(?!\w)", re.IGNORECASE)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Glossary":
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        terms = data.get("dota_terms")
        if not isinstance(terms, dict) or not terms:
            raise ValueError("Glossary requires a non-empty dota_terms mapping")
        return cls({str(key).casefold(): str(value) for key, value in terms.items()})

    def protect(self, text: str) -> tuple[str, dict[str, str]]:
        replacements: dict[str, str] = {}

        def replace(match: re.Match) -> str:
            placeholder = f"__DOTA_TERM_{len(replacements)}__"
            replacements[placeholder] = self.terms[match.group().casefold()]
            return placeholder

        return self.pattern.sub(replace, text), replacements

    @staticmethod
    def restore(text: str, replacements: dict[str, str]) -> str:
        for placeholder, value in replacements.items():
            text = text.replace(placeholder, value)
        return text
