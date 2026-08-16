from abc import ABC, abstractmethod


class BaseProvider(ABC):
    @abstractmethod
    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        preceding_context: str = "",
    ) -> str: ...

    @abstractmethod
    def review(self, text: str, glossary_terms: str = "", source_context: str = "") -> str: ...

    @abstractmethod
    def prepare_translation_source(
        self,
        text: str,
        glossary_terms: str = "",
        source_context: str = "",
    ) -> str: ...

    @property
    @abstractmethod
    def name(self) -> str: ...
