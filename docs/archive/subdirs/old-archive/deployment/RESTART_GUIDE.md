# Onehago 크롤링 재시작 가이드

## 🔄 크롤링 재시작 방법

### 1. Chrome 원격 디버깅 시작

컴퓨터를 재시작한 후에는 Chrome을 먼저 원격 디버깅 모드로 실행해야 합니다:

```bash
# Chrome 실행 (원격 디버깅 모드)
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome_debug_profile &
```

Chrome 창이 열리면 그대로 두세요.

### 2. 크롤링 재시작

프로젝트 디렉토리에서:

```bash
cd /Users/oypnus/Project/rag-enterprise

# 정제된 크롤러 재시작 (권장)
python3 scripts/crawl_onehago_full_clean.py 2>&1 | tee /tmp/onehago_clean_crawl.log &
```

### 3. 진행 상황 확인

```bash
# 실행 중인지 확인
ps aux | grep crawl_onehago_full_clean | grep -v grep

# 로그 확인
tail -f /tmp/onehago_clean_crawl.log

# 진행 상황 파일 확인
cat data/onehago/full_crawl_clean/progress.json

# 이미지 다운로드 현황
ls data/onehago/full_crawl_clean/images/ | wc -l

# 카테고리 파일 개수
ls data/onehago/full_crawl_clean/category_*.json | wc -l
```

### 4. 모니터링 스크립트 사용

```bash
/tmp/monitor_crawl.sh
```

## 🎯 현재 크롤링 설정

### 정제된 크롤러 (crawl_onehago_full_clean.py)

**특징**:
- ✅ 불필요한 폼 데이터 제거
- ✅ 핵심 필드만 깨끗하게 추출
- ✅ 유효성 검사 강화

**추출되는 필드**:
- 코드, 용량, 사이즈, Neck, MOQ, 재질, 원산지
- 제조사, PHONE, FAX, 담당, E MAIL

**제외되는 필드** (폼 관련):
- 가견적 요청일, 이메일 *, 신청수량 *
- 드롭다운 메뉴 HTML

### 출력 위치
- **카테고리별**: `data/onehago/full_crawl_clean/category_*.json`
- **이미지**: `data/onehago/full_crawl_clean/images/`
- **최종 통합**: `data/onehago/full_crawl_clean/all_products_clean.json` (완료 후)
- **진행 상황**: `data/onehago/full_crawl_clean/progress.json`

## ⚙️ 크롤링 파라미터

- **지연 시간**: 2-5초 (랜덤)
- **총 카테고리**: 217개
- **예상 제품 수**: ~43,000개
- **예상 소요 시간**: 약 3.3일

## 🛑 중단 방법

```bash
# 실행 중인 크롤러 PID 확인
ps aux | grep crawl_onehago_full_clean | grep -v grep

# 중단 (PID를 확인한 후)
kill <PID>
```

## 📊 데이터 구조 예시

```json
{
  "product_id": "57497",
  "company_no": "180",
  "category_id": "2",
  "category_name": "PACKAGING",
  "product_name": "20파이 뾰족캡",
  "moq": "5,000",
  "image_url": "/productImages/2025-02/1739726538_1.jpg",
  "detail_url": "https://onehago.com/mall/?cate_mode=view&pid=57497&no=180",
  "detailed_name": "20파이 뾰족캡",
  "full_image_url": "/productImages/2025-02/1739726538_1.jpg",
  "image_path": "data/onehago/full_crawl_clean/images/57497.jpg",
  "specifications": {
    "코드": "GY-20-뾰족캡B",
    "사이즈": "Ø23.8 × 51.5",
    "Neck": "Ø20",
    "MOQ": "5,000",
    "재질": "PP",
    "원산지": "한국",
    "제조사": "금양실업",
    "PHONE": "032-671-7630",
    "FAX": "032-671-7631",
    "담당": "- 일반 문의 : 김양원 실장 010-9341-1805",
    "E MAIL": "toritoya@naver.com"
  },
  "manufacturer": "금양실업",
  "phone": "032-671-7630",
  "fax": "032-671-7631",
  "email": "toritoya@naver.com",
  "contact": "- 일반 문의 : 김양원 실장 010-9341-1805",
  "crawled_at": "2025-10-27T02:39:33.410999"
}
```

## ✅ 자동 재시작 기능

크롤러는 `progress.json`을 통해 진행 상황을 저장합니다.

**중단 후 재시작하면**:
- ✅ 마지막으로 완료된 카테고리부터 이어서 진행
- ✅ 이미 크롤링한 데이터는 건너뜀
- ✅ 처음부터 다시 시작하지 않음

**처음부터 다시 시작하려면**:
```bash
rm data/onehago/full_crawl_clean/progress.json
```

## 🆘 문제 해결

### Chrome 연결 실패
```
❌ CDP connection failed: ...
```

**해결**: Chrome을 원격 디버깅 모드로 다시 시작
```bash
killall "Google Chrome"
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome_debug-profile &
```

### 크롤러가 멈춤
```bash
# 프로세스 확인
ps aux | grep crawl_onehago_full_clean

# 없으면 재시작
python3 scripts/crawl_onehago_full_clean.py 2>&1 | tee /tmp/onehago_clean_crawl.log &
```

### 데이터 검증
```bash
# 제품 수 확인
python3 -c "import json; data=json.load(open('data/onehago/full_crawl_clean/category_2_PACKAGING.json')); print(len(data))"

# Specification 확인
python3 -c "import json; data=json.load(open('data/onehago/full_crawl_clean/category_2_PACKAGING.json')); print([p for p in data if 'specifications' in p][:1])"
```

---

**마지막 업데이트**: 2025-10-27
**상태**: 준비 완료, 재시작 대기 중
