"""
Preprocessors for different data sources

Each preprocessor handles site-specific data transformation
"""

from .base import BasePreprocessor, ProcessedData
from .onehago import OnehagoPreprocessor

__all__ = [
    'BasePreprocessor',
    'ProcessedData',
    'OnehagoPreprocessor',
    'get_preprocessor'
]


def get_preprocessor(data_type: str) -> BasePreprocessor:
    """
    Get preprocessor for specific data type

    Args:
        data_type: Type of data (onehago, chungjinkorea, etc.)

    Returns:
        Preprocessor instance

    Raises:
        ValueError: If data_type not supported
    """
    preprocessors = {
        'onehago': OnehagoPreprocessor,
        # Add more as needed
    }

    if data_type not in preprocessors:
        raise ValueError(f"Unknown data_type: {data_type}. Supported: {list(preprocessors.keys())}")

    return preprocessors[data_type]()
