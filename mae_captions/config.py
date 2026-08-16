from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class ChunkingConfig:
    max_chunk_chars: int = field(default=900, metadata={"help": "Maximum characters per chunk"})
    gap_threshold_ms: int = field(
        default=1200, metadata={"help": "Time gap (ms) that forces a new chunk"}
    )


@dataclass
class TargetLanguage:
    code: str
    language: str
    max_line_chars: int = 0  # 0 = use LanguageDef default from languages.py


@dataclass
class OutputConfig:
    max_line_chars: int = 42
    min_entry_chars: int = 0
    bom: bool = False
    # Mirrors paths.default_output_root for the serialized config contract.
    output_root: str = "outputs"
    skip_existing: bool = False


@dataclass
class Config:
    provider: str = "claude"
    model: str = "claude-sonnet-4-6"
    base_url: str = ""
    source_lang: str = "auto"
    target_lang: str = ""  # legacy single-value; used only when targets is empty
    targets: list[TargetLanguage] = field(default_factory=list)
    preset: str = ""  # preset name; used only when targets is empty
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    source_context: str = ""
    glossary: str = ""  # path to CSV; resolved relative to CWD


def load_config(path: Path | None = None) -> Config:
    cfg = Config()
    if not (path and path.exists()):
        return cfg

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    cfg.provider = data.get("provider", cfg.provider)
    cfg.model = data.get("model", cfg.model)
    cfg.base_url = data.get("base_url", cfg.base_url)
    cfg.source_lang = data.get("source_lang", cfg.source_lang)
    cfg.target_lang = data.get("target_lang", cfg.target_lang)
    cfg.preset = data.get("preset", cfg.preset)
    cfg.source_context = data.get("source_context", cfg.source_context)
    cfg.glossary = data.get("glossary", cfg.glossary)

    if "targets" in data:
        raw = data["targets"]
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, dict):
                    cfg.targets.append(
                        TargetLanguage(
                            code=item.get("code", ""),
                            language=item.get("language", ""),
                            max_line_chars=item.get("max_line_chars", 0),
                        )
                    )

    if "chunking" in data:
        c = data["chunking"]
        cfg.chunking.max_chunk_chars = c.get("max_chunk_chars", cfg.chunking.max_chunk_chars)
        cfg.chunking.gap_threshold_ms = c.get("gap_threshold_ms", cfg.chunking.gap_threshold_ms)

    if "output" in data:
        o = data["output"]
        cfg.output.max_line_chars = o.get("max_line_chars", cfg.output.max_line_chars)
        cfg.output.min_entry_chars = o.get("min_entry_chars", cfg.output.min_entry_chars)
        cfg.output.bom = o.get("bom", cfg.output.bom)
        cfg.output.output_root = o.get("output_root", cfg.output.output_root)
        cfg.output.skip_existing = o.get("skip_existing", cfg.output.skip_existing)

    return cfg
