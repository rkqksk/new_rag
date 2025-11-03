# RAG Enterprise 🚀

## 🎯 Project Overview

**RAG Enterprise** is an open-source, production-grade Retrieval-Augmented Generation (RAG) system designed to provide intelligent, context-aware document processing and query resolution.

### 🌟 Key Features
- 📄 Multi-format Document Ingestion
- 🔍 Semantic Search
- 🤖 Flexible Model Integration
- 🛡️ Robust Error Handling
- 📊 Performance Optimization

## 🛠 Tech Stack

- **Backend**: FastAPI
- **Vector Database**: Qdrant
- **Embedding**: Sentence Transformers
- **Models**: Ollama, OpenAI, Anthropic
- **Testing**: Pytest

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Poetry or pip

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/rag-enterprise.git
cd rag-enterprise

# Install dependencies
poetry install
# or
pip install -r requirements.txt

# Run the application
poetry run python -m src.api.app
# or
python -m src.api.app
```

## 🧪 Running Tests

```bash
poetry run pytest
# or
pytest
```

## 📚 Documentation

- [Architecture](/docs/ARCHITECTURE_FINAL.md)
- [Deployment Strategy](/docs/DEPLOYMENT_STRATEGY.md)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.

## 🏆 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [Qdrant](https://qdrant.tech/)
- [Sentence Transformers](https://www.sbert.net/)

---

**Version**: 1.0.0
**Last Updated**: 2025-11-03