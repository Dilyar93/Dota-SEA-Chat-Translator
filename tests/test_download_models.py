import tempfile
import unittest
from pathlib import Path

from scripts.download_models import download_fasttext, download_nllb, download_ocr


class FakeConverter:
    def __init__(self, source, copy_files):
        self.source = Path(source)
        self.copy_files = copy_files

    def convert(self, output, quantization):
        assert quantization == "int8"
        output = Path(output)
        output.mkdir()
        (output / "model.bin").write_bytes(b"int8")
        for name in self.copy_files:
            (output / name).write_bytes((self.source / name).read_bytes())


class ModelDownloadTests(unittest.TestCase):
    def test_downloads_expected_local_layout_without_real_network(self):
        snapshots = []

        def retrieve(_url, filename):
            Path(filename).write_bytes(b"fasttext")
            return filename, None

        def snapshot(repo_id, local_dir):
            snapshots.append(repo_id)
            local_dir = Path(local_dir)
            local_dir.mkdir(parents=True)
            if repo_id.startswith("PaddlePaddle/"):
                (local_dir / "inference.json").write_text("{}", encoding="utf-8")
            else:
                (local_dir / "pytorch_model.bin").write_bytes(b"temporary")
                (local_dir / "tokenizer.json").write_text("{}", encoding="utf-8")

        with tempfile.TemporaryDirectory() as directory:
            models = Path(directory)
            download_fasttext(models, retrieve)
            download_ocr(models, snapshot)
            download_nllb(models, snapshot, FakeConverter)
            self.assertTrue((models / "lid.176.bin").is_file())
            self.assertTrue((models / "PP-OCRv5_mobile_det" / "inference.json").is_file())
            converted = models / "nllb-200-distilled-600M-ct2"
            self.assertTrue((converted / "model.bin").is_file())
            self.assertTrue((converted / "tokenizer.json").is_file())
            self.assertFalse(any(models.rglob("pytorch_model.bin")))
            self.assertEqual(len(snapshots), 4)


if __name__ == "__main__":
    unittest.main()
