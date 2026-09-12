import re
from typing import ClassVar


class PatternRouter:
    """
    Checks prompts against configurable regex/keywords to route to local nano models.
    """

    DEFAULT_KEYWORDS: ClassVar[list[str]] = [
        "git",
        "bash",
        "ls",
        "cd",
        "pwd",
        "grep",
        "cat",
        "echo",
        "mkdir",
        "rm",
        "mv",
        "cp",
    ]

    DEFAULT_PATTERNS: ClassVar[list[str]] = [
        r"^how to use .* in bash$",
        r"^[a-zA-Z0-9_-]+\.(sh|bash|zsh)$",
    ]

    def __init__(
        self,
        keywords: list[str] | None = None,
        regex_patterns: list[str] | None = None,
    ) -> None:
        """
        Initialize PatternRouter with optional lists of keywords and regex patterns.
        If None, default lists are used.
        """
        self.keywords: list[str] = (
            keywords if keywords is not None else self.DEFAULT_KEYWORDS
        )
        self.regex_patterns: list[str] = (
            regex_patterns if regex_patterns is not None else self.DEFAULT_PATTERNS
        )

        # Pre-compile the regex patterns for efficiency
        self._compiled_patterns: list[re.Pattern[str]] = [
            re.compile(p, re.IGNORECASE) for p in self.regex_patterns
        ]

        # Pre-compile a single regex for all keywords using word boundaries
        if self.keywords:
            escaped_keywords = [re.escape(kw) for kw in self.keywords]
            keyword_regex_str = r"\b(" + "|".join(escaped_keywords) + r")\b"
            self._compiled_keywords_pattern: re.Pattern[str] | None = re.compile(
                keyword_regex_str, re.IGNORECASE
            )
        else:
            self._compiled_keywords_pattern = None

    def is_nano_task(self, text: str) -> bool:
        """
        Returns True if the text matches any keyword or regex pattern,
        indicating it should be routed to a local nano model.
        """
        if not text:
            return False

        # Check regex patterns first
        for pattern in self._compiled_patterns:
            if pattern.search(text):
                return True

        # Check keywords
        return bool(
            self._compiled_keywords_pattern
            and self._compiled_keywords_pattern.search(text)
        )
