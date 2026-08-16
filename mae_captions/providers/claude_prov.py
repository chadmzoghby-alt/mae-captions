import time

import anthropic

from .base import BaseProvider

_SYSTEM = """\
You are a professional caption translator. Translate the provided text from {source} to {target}.

The text contains numbered anchor markers like <<1>>, <<2>>, etc. that mark subtitle line boundaries. \
Keep every marker in your translation, repositioning each to the nearest natural grammatical break \
point in {target}. Do not add, remove, or renumber markers. Output only the translated text with \
markers — no preamble, no explanation.\
"""

_SYSTEM_AUTO = """\
You are a professional caption translator. Detect the source language automatically and translate \
the provided text to {target}.

The text contains numbered anchor markers like <<1>>, <<2>>, etc. that mark subtitle line boundaries. \
Keep every marker in your translation, repositioning each to the nearest natural grammatical break \
point in {target}. Do not add, remove, or renumber markers. Output only the translated text with \
markers — no preamble, no explanation.\
"""

_REVIEW_BASE = (
    "You are a professional script editor specialising in subtitle text."
    "__CONTEXT_LINE__"
    " Review the provided English text as a conservative lexical cleanup only. Correct obvious"
    " spelling errors, transcription errors, grammar mistakes, punctuation issues, and casing"
    " problems only when the correction is necessary."
    " Do not paraphrase. Do not replace words with synonyms. Do not expand contractions."
    " Preserve the original wording, word order, meaning, register, and speaker style unless"
    " a word is clearly erroneous."
    "__GLOSSARY_BLOCK__"
    "\n\nThe text may contain numbered anchor markers like <<1>>, <<2>>, etc. that mark subtitle"
    " line boundaries. Preserve every marker exactly as-is and at the same boundary in the"
    " corrected text. Do not add, remove, renumber, or reposition markers. Output only the"
    " corrected text — no preamble, no explanation."
)

_TRANSLATION_SOURCE_BASE = (
    "Prepare this English subtitle text as a clear source for translation."
    "__CONTEXT_LINE__"
    " You may correct grammar, punctuation, obvious transcription errors,"
    " sentence flow, and ambiguous phrasing when doing so improves translation reliability."
    " Preserve meaning, factual claims, register, and speaker intent."
    " Do not add new information. Do not remove meaningful details."
    "__GLOSSARY_BLOCK__"
    "\n\nThe text may contain numbered anchor markers like <<1>>, <<2>>, etc. that mark subtitle"
    " line boundaries. Keep every marker exactly once and do not add, remove, or renumber markers."
    " You may reposition markers only to the nearest natural sentence or phrase boundary."
    " Output only the prepared English text with markers — no preamble, no explanation."
)


class ClaudeProvider(BaseProvider):
    def __init__(self, model: str, api_key: str | None = None):
        self._model = model
        self._client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()

    @property
    def name(self) -> str:
        return "claude"

    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        preceding_context: str = "",
    ) -> str:
        if source_lang.lower() == "auto":
            system = _SYSTEM_AUTO.format(target=target_lang)
        else:
            system = _SYSTEM.format(source=source_lang, target=target_lang)

        user_content = text
        if preceding_context:
            user_content = (
                f"[Preceding context — do not translate]: {preceding_context}\n\n"
                f"[Translate this]: {text}"
            )

        for attempt in range(4):
            try:
                response = self._client.messages.create(
                    model=self._model,
                    max_tokens=4096,
                    system=system,
                    messages=[{"role": "user", "content": user_content}],
                )
                return response.content[0].text.strip()
            except anthropic.RateLimitError:
                if attempt == 3:
                    raise
                time.sleep(2**attempt)

    def review(self, text: str, glossary_terms: str = "", source_context: str = "") -> str:
        context_line = f" The source material is: {source_context}." if source_context else ""
        glossary_block = (
            f"\n\nThe following terms have canonical spellings — always use the right-hand form:\n{glossary_terms}"
            if glossary_terms
            else ""
        )
        system = _REVIEW_BASE.replace("__CONTEXT_LINE__", context_line).replace(
            "__GLOSSARY_BLOCK__", glossary_block
        )
        for attempt in range(4):
            try:
                response = self._client.messages.create(
                    model=self._model,
                    max_tokens=4096,
                    system=system,
                    messages=[{"role": "user", "content": text}],
                )
                return response.content[0].text.strip()
            except anthropic.RateLimitError:
                if attempt == 3:
                    raise
                time.sleep(2**attempt)

    def prepare_translation_source(
        self,
        text: str,
        glossary_terms: str = "",
        source_context: str = "",
    ) -> str:
        context_line = f" The source material is: {source_context}." if source_context else ""
        glossary_block = (
            f"\n\nThe following terms have canonical spellings — always use the right-hand form:\n{glossary_terms}"
            if glossary_terms
            else ""
        )
        system = _TRANSLATION_SOURCE_BASE.replace("__CONTEXT_LINE__", context_line).replace(
            "__GLOSSARY_BLOCK__", glossary_block
        )
        for attempt in range(4):
            try:
                response = self._client.messages.create(
                    model=self._model,
                    max_tokens=4096,
                    system=system,
                    messages=[{"role": "user", "content": text}],
                )
                return response.content[0].text.strip()
            except anthropic.RateLimitError:
                if attempt == 3:
                    raise
                time.sleep(2**attempt)
