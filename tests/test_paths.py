import unittest
from pathlib import Path

from mae_captions.paths import (
    default_config_path,
    default_glossary_path,
    default_input_root,
    default_output_root,
    docs_root,
    var_build_root,
    var_dist_root,
    var_log_root,
    var_tmp_root,
)


class PathHelperTests(unittest.TestCase):
    def test_operational_defaults_match_current_cli_contract(self):
        root = Path("repo")
        self.assertEqual(default_input_root(root), root / "inputs")
        self.assertEqual(default_output_root(root), root / "outputs")
        self.assertEqual(default_config_path(root), root / "config.yaml")
        self.assertEqual(default_glossary_path(root), root / "glossary.csv")

    def test_var_roots_hold_generated_and_local_runtime_files(self):
        root = Path("repo")
        self.assertEqual(var_build_root(root), root / "var" / "build")
        self.assertEqual(var_dist_root(root), root / "var" / "dist")
        self.assertEqual(var_log_root(root), root / "var" / "logs")
        self.assertEqual(var_tmp_root(root), root / "var" / "tmp")

    def test_docs_root_is_explicit(self):
        root = Path("repo")
        self.assertEqual(docs_root(root), root / "docs")


if __name__ == "__main__":
    unittest.main()
