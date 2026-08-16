from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LanguageDef:
    code: str
    prompt_name: str  # passed verbatim to the LLM
    max_line_chars: int


LANGUAGES: dict[str, LanguageDef] = {
    "en_US": LanguageDef("en_US", "English", 42),
    "zh_CN": LanguageDef("zh_CN", "Simplified Chinese", 16),
    "hi_IN": LanguageDef("hi_IN", "Hindi", 42),
    "es_LA": LanguageDef("es_LA", "Spanish", 42),
    "ar_AR": LanguageDef("ar_AR", "Arabic", 42),
    "fr_FR": LanguageDef("fr_FR", "French", 42),
    "de_DE": LanguageDef("de_DE", "German", 42),
    "ja_JP": LanguageDef("ja_JP", "Japanese", 13),
    "ko_KR": LanguageDef("ko_KR", "Korean", 16),
    "pt_BR": LanguageDef("pt_BR", "Brazilian Portuguese", 42),
    "sv_SE": LanguageDef("sv_SE", "Swedish", 42),
    "nb_NO": LanguageDef("nb_NO", "Norwegian", 42),
    "nl_NL": LanguageDef("nl_NL", "Dutch", 42),
    "af_ZA": LanguageDef("af_ZA", "Afrikaans", 42),
}

PRESETS: dict[str, list[str]] = {
    "top5": ["en_US", "zh_CN", "hi_IN", "es_LA", "ar_AR"],
}


def resolve_targets(values: list[str]) -> list[LanguageDef]:
    """Accept codes, plain language names, and preset names.

    Returns a deduplicated ordered list of LanguageDef. Raises ValueError for unknowns.
    """
    result: list[LanguageDef] = []
    seen: set[str] = set()
    name_lookup: dict[str, LanguageDef] = {
        lang.prompt_name.lower(): lang for lang in LANGUAGES.values()
    }

    for value in values:
        if value in PRESETS:
            for code in PRESETS[value]:
                if code not in seen:
                    result.append(LANGUAGES[code])
                    seen.add(code)
        elif value in LANGUAGES:
            if value not in seen:
                result.append(LANGUAGES[value])
                seen.add(value)
        elif value.lower() in name_lookup:
            lang = name_lookup[value.lower()]
            if lang.code not in seen:
                result.append(lang)
                seen.add(lang.code)
        else:
            raise ValueError(
                f"Unknown language or preset: {value!r}. "
                f"Use a code (e.g. zh_CN), a name (e.g. French), or a preset (e.g. top5)."
            )

    return result
