# @rag/config

Configuration package for RAG Enterprise v10.0.0

## Purpose

Centralized configuration and settings management.

## Usage

```python
from packages.config.settings import get_settings

settings = get_settings()
print(settings.DATABASE_URL)
```

## Features

- Environment-based configuration
- Type-safe settings (Pydantic)
- Validation
- Secret management integration (Vault)

## Structure

```
packages/config/
├── __init__.py
├── settings.py     # Main settings
├── database.py     # Database config
├── redis.py        # Redis config
└── security.py     # Security config
```

## Version

10.0.0 - Unified Maximum
