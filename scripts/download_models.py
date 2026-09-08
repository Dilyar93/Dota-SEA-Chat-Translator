"""Download local OCR/language models and convert NLLB to CTranslate2 int8."""

from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path
from urllib.request import urlretrieve


FASTTEXT_URL = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"
OCR_REPOS = (
    "PaddlePaddle/PP-OCRv5_mobile_det",
    "PaddlePaddle/latin_PP-OCRv5_mobile_rec",
    "PaddlePaddle/th_PP-OCRv5_mobile_rec",
)
NLLB_REPO = "facebook/nllb-200-distilled-600M"
TOKENIZER_FILES = (
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "sentencepiece.bpe.model",
)


def download_fasttext(models_dir: Path, retrieve=urlretrieve) -> None:
    destination = models_dir / "lid.176.bin"
    if destination.is_file():
        return
    with tempfile.TemporaryDirectory(dir=models_dir) as temporary:
        downloaded, _headers = retrieve(FASTTEXT_URL, str(Path(temporary) / destination.name))
        shutil.move(downloaded, destination)


def download_ocr(models_dir: Path, snapshot) -> None:
    for repo in OCR_REPOS:
        destination = models_dir / repo.rsplit("/", 1)[1]
        if (destination / "inference.json").is_file():
            continue
        snapshot(repo_id=repo, local_dir=destination)


def download_nllb(models_dir: Path, snapshot, converter_factory) -> None:
    destination = models_dir / "nllb-200-distilled-600M-ct2"
    if (destination / "model.bin").is_file():
        return
    if destination.exists():
        raise FileExistsError(f"Incomplete model directory must be moved manually: {destination}")

    with tempfile.TemporaryDirectory(dir=models_dir) as temporary:
        temporary = Path(temporary)
        source = temporary / "source"
        output = temporary / "converted"
        snapshot(repo_id=NLLB_REPO, local_dir=source)
        copy_files = [name for name in TOKENIZER_FILES if (source / name).is_file()]
        converter_factory(str(source), copy_files=copy_files).convert(
            str(output), quantization="int8"
        )
        shutil.move(output, destination)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models-dir", default="models")
    parser.add_argument(
        "--accept-nllb-license",
        action="store_true",
        help="accept NLLB's CC-BY-NC-4.0 terms for personal non-commercial use",
    )
    args = parser.parse_args()
    if not args.accept_nllb_license:
        parser.error("read the NLLB license notice and pass --accept-nllb-license")

    from ctranslate2.converters import TransformersConverter
    from huggingface_hub import snapshot_download

    models_dir = Path(args.models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)
    download_fasttext(models_dir)
    download_ocr(models_dir, snapshot_download)
    download_nllb(models_dir, snapshot_download, TransformersConverter)
    print("Models installed. Normal application runtime is offline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

