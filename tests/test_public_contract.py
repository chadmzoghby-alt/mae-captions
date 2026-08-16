import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from mae_captions import __version__
from mae_captions.cli import main
from mae_captions.config import load_config


class PublicContractTests(unittest.TestCase):
    def test_help_uses_public_product_and_excludes_secret_argument(self):
        stdout = io.StringIO()
        with self.assertRaises(SystemExit) as raised:
            with contextlib.redirect_stdout(stdout):
                main(["--help"])

        self.assertEqual(raised.exception.code, 0)
        help_text = stdout.getvalue()
        self.assertIn("Mae Captions", help_text)
        self.assertIn("mae-captions", help_text)
        self.assertNotIn("--api" + "-key", help_text)

    def test_config_does_not_load_a_persisted_credential(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.yaml"
            path.write_text("api_" + "key: example-placeholder\n", encoding="utf-8")

            config = load_config(path)

        self.assertFalse(hasattr(config, "api_" + "key"))

    def test_version_is_public_prerelease(self):
        self.assertEqual(__version__, "0.1.0")

    def test_source_available_license_documents_are_present_and_consistent(self):
        root = Path(__file__).resolve().parents[1]
        required_documents = {
            "LICENSE",
            "FREELANCER_EXCEPTION.md",
            "LICENSING.md",
            "TRADEMARKS.md",
        }

        for relative in required_documents:
            self.assertTrue((root / relative).is_file(), relative)

        metadata = (root / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('license = "LicenseRef-Mae-Captions-Source-Available"', metadata)
        self.assertIn('license-files = ["LICENSE", "FREELANCER_EXCEPTION.md"]', metadata)

        guide = (root / "LICENSING.md").read_text(encoding="utf-8")
        self.assertIn("Independent Freelancer Exception", guide)
        self.assertIn("Separate commercial license required", guide)


if __name__ == "__main__":
    unittest.main()
