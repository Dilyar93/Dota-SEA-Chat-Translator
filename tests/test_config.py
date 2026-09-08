import tempfile
import unittest
from pathlib import Path

from app.config import load_config, save_config


class ConfigTests(unittest.TestCase):
    def test_load_merges_defaults_and_save_round_trips(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            path.write_text("capture:\n  fps: 4\n", encoding="utf-8")
            config = load_config(path)
            self.assertEqual(config["capture"]["fps"], 4)
            self.assertEqual(config["capture"]["debounce_ms"], 150)
            save_config(config, path)
            self.assertEqual(load_config(path), config)


if __name__ == "__main__":
    unittest.main()
