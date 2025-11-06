---
name: Bug Report
about: Create a report to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description

<!-- A clear and concise description of what the bug is -->

## Steps to Reproduce

<!-- Steps to reproduce the behavior -->

1. Go to '...'
2. Run command '...'
3. See error

## Expected Behavior

<!-- A clear and concise description of what you expected to happen -->

## Actual Behavior

<!-- What actually happened -->

## Environment

**System Information**:
- OS: [e.g., macOS 14.0, Ubuntu 22.04]
- Python Version: [e.g., 3.11.14]
- RAG Enterprise Version/Commit: [e.g., v1.0.0 or commit hash]

**Environment Verification**:
```bash
# Paste output of:
./scripts/verify_environment.sh
```

**Dependencies**:
```bash
# Paste output of:
pip list | grep -E "(qdrant|fastapi|transformers|torch)"
```

## Error Messages

<!-- Paste any error messages or stack traces -->

```
# Error output here
```

## Logs

<!-- Paste relevant logs if applicable -->

```
# Logs here
```

## Configuration

**`.env` file** (remove sensitive information):
```bash
QDRANT_HOST=localhost
USE_VECTOR_RAG=true
# etc.
```

**Data**:
- Qdrant Collection: [e.g., onehago_v2]
- Vector Count: [e.g., 22,870 or run `./scripts/verify_data.sh`]

## Screenshots

<!-- If applicable, add screenshots to help explain your problem -->

## Additional Context

<!-- Add any other context about the problem here -->

### Workaround

<!-- If you found a temporary workaround, please share it -->

### Related Issues

<!-- Link to related issues if any -->

---

**For Maintainers**:
- [ ] Reproduced the issue
- [ ] Identified root cause
- [ ] Created fix branch
- [ ] Added regression test
