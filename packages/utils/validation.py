"""
Validation utilities for RAG Enterprise v10.0.0

Common validation functions for data integrity.

Usage:
    from packages.utils.validation import validate_email, validate_url

    if validate_email("user@example.com"):
        print("Valid email!")
"""

import re
from typing import Optional
from urllib.parse import urlparse


def validate_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        bool: True if valid email format

    Example:
        >>> validate_email("user@example.com")
        True
        >>> validate_email("invalid-email")
        False
    """
    if not email or not isinstance(email, str):
        return False

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str, require_https: bool = False) -> bool:
    """
    Validate URL format.

    Args:
        url: URL to validate
        require_https: Require HTTPS protocol

    Returns:
        bool: True if valid URL

    Example:
        >>> validate_url("https://example.com")
        True
        >>> validate_url("not-a-url")
        False
    """
    if not url or not isinstance(url, str):
        return False

    try:
        result = urlparse(url)

        # Check scheme
        if not result.scheme:
            return False

        if require_https and result.scheme != 'https':
            return False

        # Check netloc (domain)
        if not result.netloc:
            return False

        return True

    except Exception:
        return False


def validate_phone(phone: str, country_code: Optional[str] = None) -> bool:
    """
    Validate phone number format.

    Args:
        phone: Phone number to validate
        country_code: Optional country code (e.g., 'US', 'KR')

    Returns:
        bool: True if valid phone format

    Example:
        >>> validate_phone("+1-234-567-8900")
        True
        >>> validate_phone("invalid")
        False
    """
    if not phone or not isinstance(phone, str):
        return False

    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)

    # Check if mostly numeric (allow + at start)
    if not re.match(r'^\+?\d{10,15}$', cleaned):
        return False

    return True


def validate_password_strength(
    password: str,
    min_length: int = 8,
    require_uppercase: bool = True,
    require_lowercase: bool = True,
    require_digit: bool = True,
    require_special: bool = True
) -> tuple[bool, list[str]]:
    """
    Validate password strength.

    Args:
        password: Password to validate
        min_length: Minimum length
        require_uppercase: Require uppercase letter
        require_lowercase: Require lowercase letter
        require_digit: Require digit
        require_special: Require special character

    Returns:
        tuple[bool, list[str]]: (is_valid, list_of_errors)

    Example:
        >>> validate_password_strength("SecurePass123!")
        (True, [])
        >>> validate_password_strength("weak")
        (False, ['Too short', 'Missing uppercase', ...])
    """
    errors = []

    if not password:
        return False, ["Password is required"]

    # Length
    if len(password) < min_length:
        errors.append(f"Minimum length is {min_length} characters")

    # Uppercase
    if require_uppercase and not re.search(r'[A-Z]', password):
        errors.append("Must contain uppercase letter")

    # Lowercase
    if require_lowercase and not re.search(r'[a-z]', password):
        errors.append("Must contain lowercase letter")

    # Digit
    if require_digit and not re.search(r'\d', password):
        errors.append("Must contain digit")

    # Special character
    if require_special and not re.search(r'[^a-zA-Z0-9]', password):
        errors.append("Must contain special character")

    return len(errors) == 0, errors


def validate_json_string(text: str) -> bool:
    """
    Validate if string is valid JSON.

    Args:
        text: String to validate

    Returns:
        bool: True if valid JSON

    Example:
        >>> validate_json_string('{"key": "value"}')
        True
        >>> validate_json_string('not json')
        False
    """
    if not text:
        return False

    import json
    try:
        json.loads(text)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def validate_port(port: int) -> bool:
    """
    Validate network port number.

    Args:
        port: Port number to validate

    Returns:
        bool: True if valid port (1-65535)

    Example:
        >>> validate_port(8080)
        True
        >>> validate_port(99999)
        False
    """
    try:
        port_int = int(port)
        return 1 <= port_int <= 65535
    except (ValueError, TypeError):
        return False


def validate_ip_address(ip: str, version: Optional[int] = None) -> bool:
    """
    Validate IP address.

    Args:
        ip: IP address to validate
        version: IP version (4 or 6), None for both

    Returns:
        bool: True if valid IP address

    Example:
        >>> validate_ip_address("192.168.1.1")
        True
        >>> validate_ip_address("not-an-ip")
        False
    """
    import ipaddress

    if not ip:
        return False

    try:
        ip_obj = ipaddress.ip_address(ip)

        if version == 4:
            return ip_obj.version == 4
        elif version == 6:
            return ip_obj.version == 6
        else:
            return True

    except ValueError:
        return False


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename for safe filesystem usage.

    Args:
        filename: Original filename
        max_length: Maximum filename length

    Returns:
        str: Sanitized filename

    Example:
        >>> sanitize_filename("my file!.txt")
        'my_file.txt'
    """
    if not filename:
        return "file"

    # Remove path separators
    filename = filename.replace('/', '_').replace('\\', '_')

    # Remove or replace dangerous characters
    filename = re.sub(r'[<>:"|?*]', '', filename)

    # Replace spaces
    filename = filename.replace(' ', '_')

    # Remove multiple underscores
    filename = re.sub(r'_+', '_', filename)

    # Truncate if too long
    if len(filename) > max_length:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        name = name[:max_length - len(ext) - 1]
        filename = f"{name}.{ext}" if ext else name

    return filename or "file"


__all__ = [
    "validate_email",
    "validate_url",
    "validate_phone",
    "validate_password_strength",
    "validate_json_string",
    "validate_port",
    "validate_ip_address",
    "sanitize_filename",
]
