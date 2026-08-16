from __future__ import annotations

from pathlib import Path


def default_input_root(root: Path) -> Path:
    return root / "inputs"


def default_output_root(root: Path) -> Path:
    return root / "outputs"


def default_config_path(root: Path) -> Path:
    return root / "config.yaml"


def default_glossary_path(root: Path) -> Path:
    return root / "glossary.csv"


def docs_root(root: Path) -> Path:
    return root / "docs"


def var_root(root: Path) -> Path:
    return root / "var"


def var_build_root(root: Path) -> Path:
    return var_root(root) / "build"


def var_dist_root(root: Path) -> Path:
    return var_root(root) / "dist"


def var_log_root(root: Path) -> Path:
    return var_root(root) / "logs"


def var_tmp_root(root: Path) -> Path:
    return var_root(root) / "tmp"


def var_local_root(root: Path) -> Path:
    return var_root(root) / "local"
