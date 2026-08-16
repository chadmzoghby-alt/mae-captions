import tempfile
import unittest
from pathlib import Path

from mae_captions.paths import default_config_path, default_input_root, default_output_root


class CliDefaultPathTests(unittest.TestCase):
    def test_default_paths_keep_current_public_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(default_input_root(root), root / "inputs")
            self.assertEqual(default_output_root(root), root / "outputs")
            self.assertEqual(default_config_path(root), root / "config.yaml")


if __name__ == "__main__":
    unittest.main()
