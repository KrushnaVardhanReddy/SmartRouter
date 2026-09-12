import asyncio
from typing import Any


class GuardrailsManager:
    """
    GuardrailsManager provides utilities to enforce safety constraints,
    such as PII redaction and jailbreak attempt detection.
    """

    def __init__(self) -> None:
        self._analyzer: Any | None = None
        self._anonymizer: Any | None = None

    def _get_engines(self) -> tuple[Any, Any]:
        """
        Lazily initialize and return the Presidio engines.
        """
        if self._analyzer is not None and self._anonymizer is not None:
            return self._analyzer, self._anonymizer

        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine
        except ImportError as e:
            raise ImportError(
                "Presidio libraries are required for PII redaction. "
                "Install them using `pip install presidio-analyzer presidio-anonymizer`."
            ) from e

        self._analyzer = AnalyzerEngine()
        self._anonymizer = AnonymizerEngine()

        return self._analyzer, self._anonymizer

    def _run_presidio(self, text: str) -> str:
        """
        Synchronous method to run the Presidio analysis and anonymization.
        """
        analyzer, anonymizer = self._get_engines()

        # Analyze the text for PII
        results = analyzer.analyze(text=text, language="en")

        # Anonymize the findings
        anonymized_result = anonymizer.anonymize(text=text, analyzer_results=results)

        return str(anonymized_result.text)

    async def redact_pii(self, text: str) -> str:
        """
        Redacts PII from the provided text using Microsoft Presidio.

        Raises:
            ImportError: if presidio_analyzer or presidio_anonymizer are not installed.
        """
        return await asyncio.to_thread(self._run_presidio, text)

    async def check_jailbreak(self, text: str) -> bool:
        """
        Checks if the provided text contains common jailbreak phrases.

        Returns:
            True if a jailbreak attempt is detected, False otherwise.
        """
        jailbreak_phrases = [
            "ignore all previous instructions",
            "system prompt",
            "bypass",
            "you are now a",
            "disregard previous",
            "do not follow",
            "pretend you are",
            "new instructions",
            "forget your previous",
            "ignore previous",
        ]

        text_lower = text.lower()
        for phrase in jailbreak_phrases:
            if phrase in text_lower:
                return True

        return False
