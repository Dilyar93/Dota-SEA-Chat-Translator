"""Lazy CTranslate2 adapter for the local NLLB model."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from app.translation.base import Translator


NLLB_LANG_MAP = {
    "id": "ind_Latn",
    "ms": "zsm_Latn",
    "tl": "tgl_Latn",
    "th": "tha_Thai",
    "vi": "vie_Latn",
    "en": "eng_Latn",
    "zh": "zho_Hans",
}


def _load_engine(path: Path, device: str, compute_type: str):
    if not path.is_dir():
        raise FileNotFoundError(f"CTranslate2 model not found: {path}")
    import ctranslate2

    return ctranslate2.Translator(str(path), device=device, compute_type=compute_type)


def _load_tokenizer(path: Path):
    if not path.is_dir():
        raise FileNotFoundError(f"NLLB tokenizer not found: {path}")
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(str(path), local_files_only=True)


class NLLBTranslator(Translator):
    def __init__(
        self,
        model_path: str | Path,
        tokenizer_path: str | Path,
        device: str = "cpu",
        compute_type: str = "int8",
        target_lang: str = "zho_Hans",
        engine_factory: Callable | None = None,
        tokenizer_factory: Callable | None = None,
    ):
        self.model_path = Path(model_path)
        self.tokenizer_path = Path(tokenizer_path)
        self.device = device
        self.compute_type = compute_type
        self.target_lang = target_lang
        self._engine_factory = engine_factory or _load_engine
        self._tokenizer_factory = tokenizer_factory or _load_tokenizer
        self._engine = None
        self._tokenizer = None

    def prepare(self) -> None:
        if self._engine is None:
            engine = self._engine_factory(
                self.model_path, self.device, self.compute_type
            )
            tokenizer = self._tokenizer_factory(self.tokenizer_path)
            self._engine, self._tokenizer = engine, tokenizer

    def translate(self, text: str, source_lang: str, target_lang: str = "zh") -> str:
        text = text.strip()
        if not text:
            return ""
        try:
            source_code = NLLB_LANG_MAP[source_lang]
            target_code = self.target_lang if target_lang == "zh" else NLLB_LANG_MAP[target_lang]
        except KeyError as error:
            raise ValueError(f"Unsupported NLLB language: {error.args[0]}") from error

        self.prepare()
        self._tokenizer.set_src_lang_special_tokens(source_code)
        source = self._tokenizer.convert_ids_to_tokens(self._tokenizer.encode(text))
        result = self._engine.translate_batch(
            [source], target_prefix=[[target_code]], beam_size=1
        )[0]
        target = result.hypotheses[0][1:]
        ids = self._tokenizer.convert_tokens_to_ids(target)
        return self._tokenizer.decode(ids, skip_special_tokens=True).strip()

