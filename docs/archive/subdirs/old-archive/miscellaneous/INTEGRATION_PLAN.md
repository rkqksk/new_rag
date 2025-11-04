# RAG Enterprise - Project Cleanup & Skill Integration Plan

## 🎯 목표
프로젝트를 자체 완결적으로 만들고, RAG 시스템에 필요한 스킬만 통합

## 📋 작업 단계

### Phase 1: 정리 (Cleanup)
- [ ] bottle-expert 스킬 제거
- [ ] 불필요한 MCP 프로파일 제거 (.max, .minimal, .zero)
- [ ] .mcp.json만 남기고 최적화
- [ ] 루트 문서들 정리 (auto_organize_docs.py 실행)

### Phase 2: 스킬 통합 (Skill Integration)
#### 기존 스킬 개선
- [ ] rag-document-processor 통합 개선
- [ ] rag-vector-search 최적화
- [ ] rag_pipeline 완성
- [ ] agent_orchestration 정리
- [ ] note_management Obsidian 연동 강화

#### 신규 스킬 생성
- [ ] rag-api-testing - FastAPI 테스트 자동화
- [ ] rag-deployment - Docker + 배포
- [ ] rag-monitoring - 로깅 + 모니터링

### Phase 3: 설정 통합 (Configuration)
- [ ] .claude/commands 정리
- [ ] .mcp.json 최적화
- [ ] CLAUDE.md 대폭 업데이트

### Phase 4: 문서화 (Documentation)
- [ ] CLAUDE.md에 모든 스킬 포함
- [ ] 각 스킬 사용법 명시
- [ ] MCP 설정 설명
- [ ] 프로젝트 전체 가이드

## 🚀 실행 순서

1. **지금 바로**: 정리 시작
2. **skill-creator 활용**: 새 스킬 생성
3. **통합 테스트**: 모든 스킬이 함께 작동하는지 확인
4. **문서 업데이트**: CLAUDE.md 완성

---

*최종 목표: 이 프로젝트 폴더만으로 RAG Enterprise 시스템 완전 작동*
