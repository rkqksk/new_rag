"""
Language Detector - Simple Language Identification

Provides lightweight language detection using character-based heuristics.
For production use, consider integrating fasttext or langdetect.

Features:
- Character-based language detection
- Support for English, Korean, Chinese, Japanese
- Fast heuristic-based approach
- No external model dependencies

Usage:
    detector = LanguageDetector()
    language = await detector.detect("안녕하세요")
    print(language)  # "ko"
"""

import logging
import re
from typing import Dict

logger = logging.getLogger(__name__)


class LanguageDetector:
    """Lightweight language detector using character-based heuristics.

    Detects language based on Unicode character ranges.
    Supports English, Korean, Chinese, and Japanese.

    Note: For production systems handling many languages,
    consider using fasttext or langdetect libraries.
    """

    # Unicode ranges for character-based detection
    KOREAN_RANGE = (0xAC00, 0xD7AF)  # Hangul syllables
    CHINESE_RANGE = (0x4E00, 0x9FFF)  # CJK unified ideographs
    JAPANESE_HIRAGANA = (0x3040, 0x309F)
    JAPANESE_KATAKANA = (0x30A0, 0x30FF)

    def __init__(self) -> None:
        """Initialize language detector."""
        logger.info("Language detector initialized")

    def _count_korean_chars(self, text: str) -> int:
        """Count Korean Hangul characters.

        Args:
            text: Input text

        Returns:
            Number of Korean characters
        """
        count = 0
        for char in text:
            code = ord(char)
            if self.KOREAN_RANGE[0] <= code <= self.KOREAN_RANGE[1]:
                count += 1
        return count

    def _count_chinese_chars(self, text: str) -> int:
        """Count Chinese characters.

        Args:
            text: Input text

        Returns:
            Number of Chinese characters
        """
        count = 0
        for char in text:
            code = ord(char)
            if self.CHINESE_RANGE[0] <= code <= self.CHINESE_RANGE[1]:
                count += 1
        return count

    def _count_japanese_chars(self, text: str) -> int:
        """Count Japanese Hiragana and Katakana characters.

        Args:
            text: Input text

        Returns:
            Number of Japanese characters
        """
        count = 0
        for char in text:
            code = ord(char)
            if (
                self.JAPANESE_HIRAGANA[0] <= code <= self.JAPANESE_HIRAGANA[1]
                or self.JAPANESE_KATAKANA[0] <= code <= self.JAPANESE_KATAKANA[1]
            ):
                count += 1
        return count

    def _count_ascii_chars(self, text: str) -> int:
        """Count ASCII alphabetic characters.

        Args:
            text: Input text

        Returns:
            Number of ASCII characters
        """
        return sum(1 for char in text if char.isascii() and char.isalpha())

    async def detect(self, text: str) -> str:
        """Detect language from text.

        Args:
            text: Input text

        Returns:
            ISO 639-1 language code (en, ko, zh, ja)

        Raises:
            ValueError: If text is empty
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        text = text.strip()

        try:
            # Count characters by script
            char_counts: Dict[str, int] = {
                "ko": self._count_korean_chars(text),
                "zh": self._count_chinese_chars(text),
                "ja": self._count_japanese_chars(text),
                "en": self._count_ascii_chars(text),
            }

            # Determine dominant language
            total_chars = sum(char_counts.values())

            if total_chars == 0:
                logger.warning("No recognizable characters, defaulting to English")
                return "en"

            # Calculate percentages
            percentages = {
                lang: count / total_chars for lang, count in char_counts.items()
            }

            # Select language with highest percentage
            detected_lang = max(percentages.items(), key=lambda x: x[1])[0]

            logger.info(
                f"Detected language: {detected_lang} "
                f"(confidence: {percentages[detected_lang]:.2%})"
            )

            return detected_lang

        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            # Default to English on error
            return "en"
