# Contributing to RAG Enterprise

Thank you for your interest in contributing to RAG Enterprise! This document provides guidelines and instructions for contributing.

---

## 📋 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Branch Strategy](#branch-strategy)
5. [Commit Message Guidelines](#commit-message-guidelines)
6. [Pull Request Process](#pull-request-process)
7. [Code Review](#code-review)
8. [Testing](#testing)
9. [Documentation](#documentation)

---

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the project
- Show empathy towards other contributors

---

## Getting Started

### Prerequisites

- Python 3.11.14
- Docker Desktop or Colima
- Git
- Basic understanding of RAG (Retrieval-Augmented Generation)

### Environment Setup

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/rag-enterprise.git
cd rag-enterprise

# 2. Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/rag-enterprise.git

# 3. Automated setup
./scripts/setup_dev_environment.sh

# 4. Verify
./scripts/verify_environment.sh

# 5. Prepare sample data
./scripts/prepare_data.sh --sample
```

**Detailed Guide**: `docs/LOCAL_SETUP.md`

---

## Development Workflow

### 1. Create a Feature Branch

```bash
# Update main
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Changes

- Write clean, readable code
- Follow existing code style
- Add comments for complex logic
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run tests
pytest tests/ -v

# Verify environment
./scripts/verify_environment.sh

# Test specific functionality
python -m pytest tests/test_your_feature.py -v
```

### 4. Commit Changes

See [Commit Message Guidelines](#commit-message-guidelines)

```bash
git add .
git commit -m "feat: Add new RAG feature for X"
```

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

---

## Branch Strategy

### Branch Types

| Type | Naming | Purpose | Example |
|------|--------|---------|---------|
| **main** | `main` | Production-ready code | `main` |
| **feature** | `feature/description` | New features | `feature/vector-search` |
| **fix** | `fix/description` | Bug fixes | `fix/qdrant-connection` |
| **docs** | `docs/description` | Documentation only | `docs/update-readme` |
| **refactor** | `refactor/description` | Code refactoring | `refactor/rag-pipeline` |
| **test** | `test/description` | Test additions | `test/embedding-service` |
| **chore** | `chore/description` | Maintenance tasks | `chore/update-dependencies` |

### Branch Lifecycle

```
main
 │
 ├─ feature/new-feature
 │   ├─ (develop)
 │   ├─ (commit)
 │   └─ (PR → main)
 │
 └─ fix/bug-fix
     ├─ (develop)
     └─ (PR → main)
```

---

## Commit Message Guidelines

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style (formatting, missing semicolons, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks (dependencies, configs, etc.)
- **perf**: Performance improvements

### Scope (Optional)

- `rag`: RAG pipeline
- `api`: FastAPI routes
- `core`: Core modules
- `ui`: Frontend
- `infra`: Infrastructure (Docker, etc.)
- `docs`: Documentation

### Examples

**Good**:
```
feat(rag): Add metadata filtering to vector search

Implemented metadata filtering for Qdrant queries to support
category-based product search. This enables users to filter
results by product type, material, and volume.

Closes #123
```

**Good** (Simple):
```
fix(api): Resolve Qdrant connection timeout issue
```

**Bad**:
```
fixed stuff
```

**Bad**:
```
update
```

### Rules

1. **Subject**:
   - Use imperative mood ("Add feature" not "Added feature")
   - Don't capitalize first letter
   - No period at the end
   - Max 50 characters

2. **Body** (Optional):
   - Explain what and why, not how
   - Wrap at 72 characters
   - Separate from subject with blank line

3. **Footer** (Optional):
   - Reference issues: `Closes #123`, `Fixes #456`
   - Breaking changes: `BREAKING CHANGE: ...`

---

## Pull Request Process

### Before Creating PR

- [ ] Code follows project style
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] Environment verification passes

### Creating PR

1. **Title**: Clear and descriptive
   ```
   feat: Add vector search with metadata filtering
   ```

2. **Description**: Use the template
   - What changed
   - Why it changed
   - How to test
   - Screenshots (if UI changes)
   - Related issues

3. **Labels**: Add appropriate labels
   - `feature`, `bug`, `documentation`, etc.

4. **Reviewers**: Request review from maintainers

### PR Template

```markdown
## Description

Brief description of changes.

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring
- [ ] Performance improvement

## Testing

How to test these changes:

\```bash
# Commands to test
\```

## Checklist

- [ ] Code follows project style
- [ ] Self-review completed
- [ ] Comments added
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] Environment verification passes

## Related Issues

Closes #123
```

---

## Code Review

### For Authors

- Respond to feedback promptly
- Be open to suggestions
- Explain your reasoning clearly
- Make requested changes or discuss alternatives

### For Reviewers

- Be constructive and kind
- Explain the "why" behind suggestions
- Approve when satisfied
- Use GitHub's suggestion feature

### Review Checklist

- [ ] Code is clear and maintainable
- [ ] No unnecessary complexity
- [ ] Proper error handling
- [ ] Security considerations addressed
- [ ] Performance impact considered
- [ ] Tests are comprehensive
- [ ] Documentation is updated

---

## Testing

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific module
pytest tests/test_rag_pipeline.py -v

# With coverage
pytest tests/ -v --cov=src --cov-report=html

# Watch mode (for development)
pytest-watch tests/
```

### Writing Tests

```python
# tests/test_example.py
import pytest
from src.core.rag_pipeline import RAGPipeline

def test_rag_pipeline_initialization():
    """Test RAG pipeline initializes correctly."""
    pipeline = RAGPipeline(collection_name="test")
    assert pipeline is not None
    assert pipeline.collection_name == "test"

def test_document_ingestion():
    """Test document ingestion with sample data."""
    pipeline = RAGPipeline(collection_name="test")
    documents = [
        {"text": "Sample product", "metadata": {"id": 1}}
    ]

    result = pipeline.ingest_documents(documents)
    assert result.status == "success"
```

### Test Guidelines

- One assertion per test (generally)
- Clear test names that describe what is tested
- Use fixtures for common setup
- Test edge cases and error conditions
- Aim for >80% code coverage

---

## Documentation

### What to Document

- **Code**: Docstrings for all public functions/classes
- **APIs**: Endpoint descriptions and examples
- **Features**: User-facing documentation
- **Setup**: Installation and configuration guides

### Docstring Format

```python
def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
    """
    Retrieve relevant documents using vector search.

    Args:
        query: The search query text
        top_k: Number of results to return (default: 5)

    Returns:
        List of dictionaries containing:
            - text: Document text
            - score: Relevance score
            - metadata: Document metadata

    Raises:
        QdrantException: If vector search fails

    Example:
        >>> pipeline = RAGPipeline()
        >>> results = pipeline.retrieve("100ml bottle")
        >>> len(results)
        5
    """
    pass
```

### Updating Documentation

When making changes, update:

1. **Code Comments**: Inline explanations
2. **Docstrings**: Function/class documentation
3. **README.md**: If affecting quick start
4. **docs/*.md**: Detailed guides
5. **CHANGELOG.md**: Notable changes

---

## Style Guide

### Python

Follow PEP 8:

```bash
# Format with black
black src/ tests/

# Lint with flake8
flake8 src/ tests/

# Type checking with mypy
mypy src/
```

### Key Points

- Use 4 spaces for indentation
- Max line length: 88 characters (black default)
- Use type hints where possible
- Import order: stdlib, third-party, local

### Example

```python
from typing import List, Dict, Optional
import os

from fastapi import FastAPI
from qdrant_client import QdrantClient

from src.core.rag_pipeline import RAGPipeline


class DocumentProcessor:
    """Process documents for RAG ingestion."""

    def __init__(self, collection_name: str) -> None:
        """Initialize processor with collection name."""
        self.collection_name = collection_name

    def process(self, documents: List[Dict]) -> List[Dict]:
        """
        Process raw documents into embeddings.

        Args:
            documents: List of raw document dictionaries

        Returns:
            List of processed documents with embeddings
        """
        processed = []
        for doc in documents:
            # Processing logic here
            processed.append(doc)
        return processed
```

---

## Questions?

- **Documentation**: Check `docs/` directory
- **Issues**: Open a GitHub issue
- **Discussions**: Use GitHub Discussions
- **Email**: [maintainer-email]

---

## Recognition

Contributors will be recognized in:
- `CONTRIBUTORS.md` file
- GitHub contributors page
- Release notes for significant contributions

---

## License

By contributing to RAG Enterprise, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing!** 🎉

---

**Last Updated**: 2025-11-06
**Version**: 1.0.0
