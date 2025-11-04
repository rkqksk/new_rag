# RAG Enterprise Documentation

Production-grade RAG system with SKILL-based architecture, multi-model support, and vector search capabilities.

---

## Quick Links

- **[QUICK_START.md](QUICK_START.md)** - Get started in 5 minutes
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture overview
- **[DEPLOYMENT_STRATEGY.md](DEPLOYMENT_STRATEGY.md)** - Production deployment guide
- **[TECHNOLOGY_STACK.md](TECHNOLOGY_STACK.md)** - Tech stack details
- **[CHANGELOG.md](CHANGELOG.md)** - Version history

---

## Core Documentation

### Getting Started
- **[QUICK_START.md](QUICK_START.md)** - Installation and basic usage
- **[../CLAUDE.md](../CLAUDE.md)** - Claude Code integration guide

### Architecture & Design
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design
- **[TECHNOLOGY_STACK.md](TECHNOLOGY_STACK.md)** - Technologies used

### Deployment & Operations
- **[DEPLOYMENT_STRATEGY.md](DEPLOYMENT_STRATEGY.md)** - Deployment strategies
- **[CHANGELOG.md](CHANGELOG.md)** - Release notes and changes

---

## Development History

For detailed development history, design decisions, and session logs:

**[../claudedocs/](../claudedocs/)** - Comprehensive development documentation including:
- Development session logs
- Feature implementation reports
- Bug investigations and resolutions
- Architecture evolution history
- Progress reports and milestones

---

## Archive

Historical documentation has been moved to **[archive/](archive/)** directory:

- **archive/architecture/** - Legacy architecture documents
- **archive/crawling/** - Web crawling documentation
- **archive/rag/** - Detailed RAG implementation docs
- **archive/guides/** - Setup and configuration guides
- **archive/progress/** - Historical progress reports
- **archive/deployment/** - Detailed deployment documentation
- **archive/observability/** - Observability and monitoring
- **archive/ci-cd/** - CI/CD pipeline documentation
- **archive/analysis/** - Data analysis reports
- **archive/miscellaneous/** - Other documentation
- **archive/subdirs/** - Old archived directories

---

## Documentation Philosophy

### docs/ (This Directory)
- **Purpose**: Current, essential project documentation
- **Audience**: Users, contributors, operators
- **Content**: Getting started, architecture, deployment
- **Maintenance**: Keep up-to-date, remove obsolete

### claudedocs/ (Development History)
- **Purpose**: Development process tracking
- **Audience**: Developers, maintainers, Claude
- **Content**: Session logs, decisions, implementation details
- **Maintenance**: Append-only, preserve history

### archive/ (Legacy Docs)
- **Purpose**: Historical reference
- **Audience**: Researchers, archaeologists
- **Content**: Superseded documentation
- **Maintenance**: Read-only, organized by category

---

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Vector DB**: Qdrant + PostgreSQL/pgvector
- **Cache**: Redis
- **LLM**: Ollama (llama3.1:8b), OpenAI, Anthropic
- **Embeddings**: Sentence Transformers
- **Infrastructure**: Docker Compose
- **Testing**: pytest (80%+ coverage target)

---

## Quick Start

```bash
# Clone repository
git clone https://github.com/your-org/rag-enterprise.git
cd rag-enterprise

# Install dependencies
pip install -r requirements.txt

# Run application
python -m src.api.app

# Run tests
pytest tests/ -v
```

For detailed instructions, see [QUICK_START.md](QUICK_START.md).

---

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes and test (`pytest tests/ -v`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open Pull Request

---

## License

MIT License - See [LICENSE](../LICENSE) for details.

---

**Version**: 1.0.0
**Last Updated**: 2025-11-03
**Project**: [github.com/your-org/rag-enterprise](https://github.com/your-org/rag-enterprise)
