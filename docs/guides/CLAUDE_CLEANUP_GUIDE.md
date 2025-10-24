# Claude 폴더 정리 가이드

## 📊 현재 상태

### ✅ 정리 완료 (보관)
- **`.claude-clean/`** - 정리되고 최적화된 설정 (메인)
  - agents: 15개
  - commands: 1개
  - skills: 2개
  - config: 450개
  - workflows: 3개

- **`.claude-backup-20251023_104124/`** - 안전 백업 (원본 보존)

### 🗑️ 정리 대상 (삭제 가능)
- `.claude/` - 원본 폴더 (백업 있음)
- `.claude-plugin/` - 이제 .claude-clean에 통합됨
- `.claude-unified/` - 이제 .claude-clean에 통합됨  
- `.claude-v3/` - 이전 버전
- `.claude.backup.20251021_111051/` - 이전 백업

## 🚀 정리 방법

### 옵션 1: 자동 정리 (권장)
```bash
# 안전한 자동 정리 (백업 포함)
bash cleanup-old-claude.sh
```

이 스크립트는:
1. 삭제 전 모든 폴더를 `.tar.gz`로 백업
2. 삭제할 폴더 목록 표시
3. 사용자 확인 후 삭제
4. 안전 백업 보관

### 옵션 2: 수동 정리
```bash
# 1. 먼저 백업 (혹시 모르니)
tar -czf claude-old-backup.tar.gz .claude* 

# 2. 하나씩 삭제
rm -rf .claude-plugin
rm -rf .claude-unified
rm -rf .claude-v3
rm -rf .claude.backup.20251021_111051
rm -rf .claude  # 원본 (백업 있음)
```

### 옵션 3: 보관 후 정리
```bash
# 안전하게 다른 곳으로 이동
mkdir ~/claude-old-backups
mv .claude* ~/claude-old-backups/
# .claude-clean과 최신 백업은 다시 가져오기
mv ~/claude-old-backups/.claude-clean .
mv ~/claude-old-backups/.claude-backup-20251023_104124 .
```

## 📂 정리 후 구조

```
rag-enterprise/
├── .claude-clean/              # ✅ 메인 (활성화 대기)
│   ├── agents/
│   ├── commands/
│   ├── skills/
│   ├── config/
│   ├── workflows/
│   ├── claude.json
│   └── activate.sh
│
├── .claude-backup-20251023_104124/  # ✅ 안전 백업
│
└── claude-safety-backup-*.tar.gz    # ✅ 최종 안전 백업 (자동 정리 시)
```

## 🎯 활성화 (정리 후)

```bash
# 1. .claude-clean 내용 확인
ls -la .claude-clean/

# 2. 활성화 (홈 디렉토리로 복사)
bash .claude-clean/activate.sh

# 3. Claude 재시작
```

## ⚠️ 주의사항

1. **백업 확인**: 삭제 전 `.claude-backup-20251023_104124/` 폴더가 있는지 확인
2. **테스트**: 정리 후 Claude가 정상 작동하는지 확인
3. **보관 기간**: 안전 백업은 최소 1주일 보관 권장

## 🔄 롤백 방법

문제가 생기면:
```bash
# 백업에서 복원
cp -r .claude-backup-20251023_104124/* ~/.claude/

# 또는 안전 백업에서 복원
tar -xzf claude-safety-backup-*.tar.gz
```

## 💡 디스크 공간 절약

정리 전후 비교:
```bash
# 정리 전 전체 크기
du -sh .claude*

# 정리 후 예상 크기
du -sh .claude-clean .claude-backup-20251023_104124
```

대략 **60-80% 디스크 공간 절약** 예상!

## 📞 문제 발생 시

1. `.claude-backup-20251023_104124/` 에서 복원
2. `claude-safety-backup-*.tar.gz` 압축 해제
3. 또는 이전 상태로 git reset (버전 관리 중인 경우)

---
**생성일**: 2025-10-23  
**버전**: 2.1
