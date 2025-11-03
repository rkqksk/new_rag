# RAG Enterprise 🚀

## 📋 프로젝트 개요

**RAG Enterprise**는 오픈소스 검색 증강 생성(Retrieval-Augmented Generation) 시스템으로, 지능형 문서 처리 및 쿼리 해결을 위한 혁신적인 솔루션입니다.

### 🌟 주요 기능

- 🔍 다중 포맷 문서 수집
- 💡 시맨틱 검색
- 🤖 유연한 모델 통합
- 🛡️ 강력한 오류 처리
- 📊 성능 최적화

## 🛠 기술 스택

- **백엔드**: FastAPI
- **벡터 데이터베이스**: Qdrant
- **임베딩**: Sentence Transformers
- **모델**: Ollama, OpenAI, Anthropic
- **테스트**: Pytest

## 🚀 빠른 시작

### 필수 조건
- Python 3.11+
- Poetry 또는 pip

### 설치

```bash
# 저장소 클론
git clone https://github.com/your-org/rag-enterprise.git
cd rag-enterprise

# 의존성 설치
poetry install
# 또는
pip install -r requirements.txt

# 애플리케이션 실행
poetry run python -m src.api.app
# 또는
python -m src.api.app
```

## 🧪 테스트 실행

```bash
poetry run pytest
# 또는
pytest
```

## 📚 문서

- [아키텍처](/docs/ARCHITECTURE_FINAL.md)
- [배포 전략](/docs/DEPLOYMENT_STRATEGY.md)

## 🤝 기여 방법

1. 저장소 포크
2. 기능 브랜치 생성 (`git checkout -b feature/AmazingFeature`)
3. 변경사항 커밋 (`git commit -m '놀라운 기능 추가'`)
4. 브랜치 푸시 (`git push origin feature/AmazingFeature`)
5. 풀 리퀘스트 열기

## 📝 라이선스

MIT 라이선스에 따라 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 🏆 감사의 말

- [FastAPI](https://fastapi.tiangolo.com/)
- [Qdrant](https://qdrant.tech/)
- [Sentence Transformers](https://www.sbert.net/)

---

**버전**: 1.0.0
**최종 업데이트**: 2025-11-03