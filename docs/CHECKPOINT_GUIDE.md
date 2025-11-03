# 🔄 크롤러 체크포인트 및 재시작 가이드

현재 실행 중인 크롤러를 안전하게 보존하고 나중에 재시작하는 완전한 가이드입니다.

## 📊 현재 크롤러 상태 (2025-10-28 08:01)

### ✅ Freemold Detail Crawler
- **실행 중**: 2개 프로세스
- **PID**: 54807, 70098
- **진행률**: 1,796 / 21,592 제품 (8.3%)
- **수집 이미지**: 4,077개
- **Progress File**: `data/freemold/crawled_v2/crawl_progress.json`
- **Last Updated**: 2025-10-28 08:01:25

### ✅ Onehago Full Crawler
- **실행 중**: 1개 프로세스
- **PID**: 72139
- **진행률**: 31 / 217 카테고리 (14.3%)
- **Progress File**: `data/onehago/full_crawl_clean/progress.json`
- **Last Category**: 59

---

## 🛑 컴퓨터 끄기 전 안전 종료

### Option 1: 백그라운드 유지 (권장)
크롤러를 그대로 두고 컴퓨터만 끄면 자동으로 종료됩니다. 진행 상황은 JSON 파일에 저장되어 있으므로 **안전하게 재시작 가능**합니다.

```bash
# 진행 상황 확인 (선택사항)
cat data/freemold/crawled_v2/crawl_progress.json
cat data/onehago/full_crawl_clean/progress.json

# 그냥 컴퓨터를 끄면 됩니다 - 진행 상황이 자동으로 저장되어 있습니다
```

### Option 2: 명시적 종료
크롤러를 수동으로 종료하고 싶다면:

```bash
# 1. 현재 실행 중인 크롤러 PID 확인
ps aux | grep -E "crawl_freemold_complete_v2|crawl_onehago_full_clean" | grep -v grep

# 2. Freemold 크롤러 종료
kill 54807 70098

# 3. Onehago 크롤러 종료
kill 72139

# 4. 진행 상황 확인 (자동 저장되어 있음)
ls -lh data/freemold/crawled_v2/crawl_progress.json
ls -lh data/onehago/full_crawl_clean/progress.json
```

---

## 🚀 컴퓨터 켠 후 재시작

### 1. Freemold Detail Crawler 재시작

**자동 재시작 (권장)**:
```bash
nohup python3 scripts/crawl_freemold_complete_v2.py \
  data/freemold/universal/all_products_merged.json \
  2>&1 | tee /tmp/freemold_detail_restart.log &

echo "✅ Freemold Detail Crawler 재시작 완료!"
echo "로그: tail -f /tmp/freemold_detail_restart.log"
```

**병렬 크롤러 재시작 (더 빠름)**:
```bash
# 3개 프로세스 병렬 실행
nohup python3 scripts/crawl_freemold_complete_v2.py \
  data/freemold/universal/all_products_merged.json \
  2>&1 > /tmp/freemold_detail_1.log &

nohup python3 scripts/crawl_freemold_complete_v2.py \
  data/freemold/universal/A001_products_partial.json \
  2>&1 > /tmp/freemold_detail_2.log &

echo "✅ Freemold 병렬 크롤러 재시작 완료!"
```

### 2. Onehago Full Crawler 재시작

```bash
nohup python3 scripts/crawl_onehago_full_clean.py \
  2>&1 | tee /tmp/onehago_full_restart.log &

echo "✅ Onehago Full Crawler 재시작 완료!"
echo "로그: tail -f /tmp/onehago_full_restart.log"
```

---

## 📈 진행 상황 모니터링

### 실시간 로그 확인

```bash
# Freemold 로그
tail -f /tmp/freemold_detail_restart.log

# Onehago 로그
tail -f /tmp/onehago_full_restart.log
```

### 진행률 확인

```bash
# Freemold 진행률
python3 << 'EOF'
import json

# Progress 파일 읽기
with open('data/freemold/crawled_v2/crawl_progress.json', 'r') as f:
    progress = json.load(f)

# 전체 제품 수
total = 21592

# 완료된 제품 수
completed = len(progress['completed'])

# 진행률
percentage = (completed / total) * 100

print(f"📊 Freemold Detail Crawler")
print(f"   완료: {completed:,} / {total:,} 제품")
print(f"   진행률: {percentage:.1f}%")
print(f"   남은 제품: {total - completed:,}")
print(f"   마지막 업데이트: {progress['last_updated']}")
EOF

# Onehago 진행률
python3 << 'EOF'
import json

# Progress 파일 읽기
with open('data/onehago/full_crawl_clean/progress.json', 'r') as f:
    progress = json.load(f)

# 전체 카테고리 수
total = 217

# 완료된 카테고리 수
completed = len(progress['processed_categories'])

# 진행률
percentage = (completed / total) * 100

print(f"📊 Onehago Full Crawler")
print(f"   완료: {completed} / {total} 카테고리")
print(f"   진행률: {percentage:.1f}%")
print(f"   남은 카테고리: {total - completed}")
print(f"   다음 카테고리: {progress['last_category_index']}")
EOF
```

### 프로세스 상태 확인

```bash
# 실행 중인 크롤러 확인
ps aux | grep -E "crawl_freemold_complete_v2|crawl_onehago_full_clean" | grep -v grep

# 출력 예시:
# oypnus  54807  ... python3 scripts/crawl_freemold_complete_v2.py ...
# oypnus  72139  ... python3 scripts/crawl_onehago_full_clean.py ...
```

---

## 📁 체크포인트 파일 위치

### Freemold
| 파일 | 설명 | 위치 |
|------|------|------|
| **Progress** | 완료된 제품 ID 리스트 | `data/freemold/crawled_v2/crawl_progress.json` |
| **Products** | 수집된 제품 상세 정보 | `data/freemold/crawled_v2/*.json` |
| **Images** | 다운로드된 제품 이미지 | `data/freemold/crawled_v2/images/` |

**Progress 파일 구조**:
```json
{
  "completed": ["2949", "89037", "89035", ...],
  "last_updated": "2025-10-28T08:01:25.878082"
}
```

### Onehago
| 파일 | 설명 | 위치 |
|------|------|------|
| **Progress** | 완료된 카테고리 리스트 | `data/onehago/full_crawl_clean/progress.json` |
| **Products** | 수집된 제품 정보 | `data/onehago/full_crawl_clean/products/*.json` |
| **Images** | 다운로드된 제품 이미지 | `data/onehago/full_crawl_clean/images/` |

**Progress 파일 구조**:
```json
{
  "last_category_index": 27,
  "processed_categories": ["2", "193", "210", ...],
  "failed_categories": []
}
```

---

## 🔍 문제 해결

### Q: 재시작 후 크롤러가 처음부터 다시 시작하나요?
**A**: 아니요! 크롤러는 자동으로 `progress.json` 파일을 확인하여 마지막 진행 위치부터 재시작합니다.

### Q: 중복 수집이 발생하나요?
**A**: 아니요! 크롤러는 `progress.json`의 `completed` 배열을 확인하여 이미 수집된 제품은 건너뜁니다.

### Q: 크롤러가 멈춘 것 같아요
**A**: 로그를 확인하세요:
```bash
# Freemold 로그
tail -50 /tmp/freemold_detail_restart.log

# Onehago 로그
tail -50 /tmp/onehago_full_restart.log

# 프로세스 확인
ps aux | grep crawl | grep -v grep
```

### Q: 진행 속도가 느려요
**A**: 병렬 크롤러를 사용하면 더 빠릅니다:
```bash
# Freemold 3개 병렬 실행
for i in 1 2 3; do
  nohup python3 scripts/crawl_freemold_complete_v2.py \
    data/freemold/universal/all_products_merged.json \
    2>&1 > /tmp/freemold_detail_$i.log &
done
```

---

## 📝 빠른 명령어 치트시트

```bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 진행 상황 확인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Freemold 진행률
jq -r '.completed | length' data/freemold/crawled_v2/crawl_progress.json
echo "/ 21,592 제품"

# Onehago 진행률
jq -r '.processed_categories | length' data/onehago/full_crawl_clean/progress.json
echo "/ 217 카테고리"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 크롤러 재시작
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Freemold 재시작
nohup python3 scripts/crawl_freemold_complete_v2.py \
  data/freemold/universal/all_products_merged.json \
  2>&1 | tee /tmp/freemold_detail_restart.log &

# Onehago 재시작
nohup python3 scripts/crawl_onehago_full_clean.py \
  2>&1 | tee /tmp/onehago_full_restart.log &

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 로그 모니터링
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Freemold 로그
tail -f /tmp/freemold_detail_restart.log

# Onehago 로그
tail -f /tmp/onehago_full_restart.log

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 프로세스 확인/종료
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 실행 중인 크롤러 확인
ps aux | grep crawl | grep -v grep

# 모든 크롤러 종료
pkill -f "crawl_freemold_complete_v2"
pkill -f "crawl_onehago_full_clean"
```

---

## 💾 데이터 백업 (선택사항)

중요한 진행 상황을 백업하고 싶다면:

```bash
# 현재 날짜로 백업 디렉토리 생성
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Progress 파일 백업
cp data/freemold/crawled_v2/crawl_progress.json "$BACKUP_DIR/freemold_progress.json"
cp data/onehago/full_crawl_clean/progress.json "$BACKUP_DIR/onehago_progress.json"

# 수집된 데이터 백업 (선택)
cp -r data/freemold/crawled_v2/*.json "$BACKUP_DIR/freemold_data/"
cp -r data/onehago/full_crawl_clean/products/*.json "$BACKUP_DIR/onehago_data/"

echo "✅ 백업 완료: $BACKUP_DIR"
```

---

## 📞 다음 세션에서 확인할 사항

컴퓨터를 다시 켠 후:

1. **✅ 진행 상황 확인**: Progress 파일이 정상적으로 저장되었는지 확인
2. **✅ 크롤러 재시작**: 위의 재시작 명령어로 크롤러 실행
3. **✅ 로그 확인**: 크롤러가 마지막 위치부터 재개되는지 확인
4. **✅ 진행률 모니터링**: 정상적으로 데이터가 수집되는지 확인

**예상 완료 시간**:
- **Freemold**: 약 150시간 (91.7% 남음, 병렬 실행 시 ~50시간)
- **Onehago**: 약 9시간 (85.7% 남음)

---

**마지막 업데이트**: 2025-10-28 08:01:25
**작성자**: Claude
**문서 위치**: `/Users/oypnus/Project/rag-enterprise/CHECKPOINT_GUIDE.md`
