# 🚀 Claude RAG Enterprise - 빠른 시작 가이드

## 즉시 사용하기 (1분 설정)

```bash
# 1. 설정 적용
chmod +x apply-claude-config.sh
./apply-claude-config.sh

# 2. Claude Code 재시작

# 3. 완료! 이제 사용 가능
```

## 주요 명령어

### 문서 처리
```
"이 PDF를 RAG 시스템에 추가해줘"
"documents 폴더의 모든 문서를 처리해줘"
"이 엑셀 파일에서 데이터를 추출해줘"
```

### 벡터 검색
```
"50ml 용기 관련 문서 검색"
"플라스틱 재질 제품 찾아줘"
"최근 1개월 내 추가된 문서만 검색"
```

## 스킬이 자동으로 활성화되는 키워드

### rag-document-processor
- "문서 처리", "PDF 파싱", "엑셀 추출"
- "RAG에 추가", "문서 인덱싱"
- "청킹", "임베딩 생성"

### rag-vector-search  
- "벡터 검색", "유사 문서"
- "Qdrant 검색", "의미 검색"
- "관련 문서 찾기"

## 프로젝트 구조

```
✅ 필수 파일 (자동 생성됨)
.claude/
  ├── skills/               # 프로젝트 스킬
  ├── settings.local.json   # 권한 설정
.mcp.json                   # MCP 서버 설정

⭐ 핵심 스킬 (포함됨)
.claude/skills/
  ├── rag-document-processor/  # 문서 처리
  └── rag-vector-search/        # 벡터 검색
```

## 다른 프로젝트에 적용하기

### 옵션 1: 전체 복사 (권장)
```bash
# 대상 프로젝트로 이동
cd /path/to/other-project

# 설정 복사
cp -r /path/to/rag-enterprise/.claude .
cp /path/to/rag-enterprise/.mcp.json .

# 경로 수정 (필요시)
# .mcp.json 에서 Python 경로 업데이트
```

### 옵션 2: 스킬만 복사
```bash
# 특정 스킬만 복사
cp -r /path/to/rag-enterprise/.claude/skills/rag-document-processor \
      /path/to/other-project/.claude/skills/
```

### 옵션 3: 전역 설치
```bash
# 모든 프로젝트에서 사용
cp -r .claude/skills/rag-document-processor ~/.claude/skills/
```

## 문제 해결

### Q: 스킬이 인식되지 않아요
A: Claude Code를 재시작하세요

### Q: MCP 서버 오류가 발생해요  
A: `.mcp.json`의 Python 경로를 확인하세요

### Q: 권한 오류가 발생해요
A: `.claude/settings.local.json`에 필요한 권한 추가

## 지원

- 📚 [공식 문서](https://docs.claude.com/en/docs/agents-and-tools/agent-skills)
- 💬 문의: RAG Enterprise Team
- 🐛 이슈: GitHub Issues

---
**Version**: 3.0 | **Updated**: 2025-01-11
