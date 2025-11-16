"""
Text processing utilities for RAG Enterprise v10.0.0

Common text manipulation functions used across the platform.

Usage:
    from packages.utils.text import clean_text, tokenize

    text = clean_text("  Hello World!  ")
    tokens = tokenize("Natural language processing")
"""

import re
from typing import List, Optional


def clean_text(text: str) -> str:
    """
    Clean and normalize text.

    - Removes extra whitespace
    - Normalizes line breaks
    - Strips leading/trailing whitespace

    Args:
        text: Input text to clean

    Returns:
        str: Cleaned text

    Example:
        >>> clean_text("  Hello   World!  \\n\\n  ")
        'Hello World!'
    """
    if not text:
        return ""

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)

    # Strip
    text = text.strip()

    return text


def tokenize(text: str, lowercase: bool = True) -> List[str]:
    """
    Simple word tokenization.

    Args:
        text: Input text to tokenize
        lowercase: Convert to lowercase

    Returns:
        List[str]: List of tokens

    Example:
        >>> tokenize("Hello World!")
        ['hello', 'world']
    """
    if not text:
        return []

    # Lowercase
    if lowercase:
        text = text.lower()

    # Split on non-alphanumeric
    tokens = re.findall(r'\b\w+\b', text)

    return tokens


def truncate(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Input text
        max_length: Maximum length (including suffix)
        suffix: Suffix to add if truncated

    Returns:
        str: Truncated text

    Example:
        >>> truncate("This is a very long sentence", max_length=10)
        'This is...'
    """
    if not text or len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def normalize_whitespace(text: str) -> str:
    """
    Normalize all whitespace to single spaces.

    Args:
        text: Input text

    Returns:
        str: Text with normalized whitespace

    Example:
        >>> normalize_whitespace("Hello\\n\\n  World\\t!")
        'Hello World !'
    """
    return re.sub(r'\s+', ' ', text)


def remove_special_characters(
    text: str,
    keep_spaces: bool = True,
    keep_numbers: bool = True
) -> str:
    """
    Remove special characters from text.

    Args:
        text: Input text
        keep_spaces: Keep space characters
        keep_numbers: Keep numeric characters

    Returns:
        str: Text with special characters removed

    Example:
        >>> remove_special_characters("Hello, World! 123")
        'Hello World 123'
    """
    if not text:
        return ""

    # Build pattern
    pattern = r'[^a-zA-Z'
    if keep_numbers:
        pattern += r'0-9'
    if keep_spaces:
        pattern += r'\s'
    pattern += r']'

    return re.sub(pattern, '', text)


def extract_emails(text: str) -> List[str]:
    """
    Extract email addresses from text.

    Args:
        text: Input text

    Returns:
        List[str]: List of email addresses found

    Example:
        >>> extract_emails("Contact: john@example.com or jane@test.org")
        ['john@example.com', 'jane@test.org']
    """
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_pattern, text)


def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text.

    Args:
        text: Input text

    Returns:
        List[str]: List of URLs found

    Example:
        >>> extract_urls("Visit https://example.com or http://test.org")
        ['https://example.com', 'http://test.org']
    """
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(url_pattern, text)


def slugify(text: str, separator: str = "-") -> str:
    """
    Convert text to URL-friendly slug.

    Args:
        text: Input text
        separator: Separator character

    Returns:
        str: Slugified text

    Example:
        >>> slugify("Hello World! 123")
        'hello-world-123'
    """
    # Lowercase
    text = text.lower()

    # Remove special characters
    text = re.sub(r'[^a-z0-9\s-]', '', text)

    # Replace spaces and multiple separators
    text = re.sub(r'[\s-]+', separator, text)

    # Strip separators from edges
    text = text.strip(separator)

    return text


def highlight_matches(
    text: str,
    query: str,
    tag_start: str = "<mark>",
    tag_end: str = "</mark>"
) -> str:
    """
    Highlight query matches in text.

    Args:
        text: Input text
        query: Search query
        tag_start: Opening tag
        tag_end: Closing tag

    Returns:
        str: Text with highlighted matches

    Example:
        >>> highlight_matches("Hello World", "world")
        'Hello <mark>World</mark>'
    """
    if not query:
        return text

    # Case-insensitive replacement
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    return pattern.sub(f"{tag_start}\\g<0>{tag_end}", text)


__all__ = [
    "clean_text",
    "tokenize",
    "truncate",
    "normalize_whitespace",
    "remove_special_characters",
    "extract_emails",
    "extract_urls",
    "slugify",
    "highlight_matches",
]
