# 인코딩 검수 및 수정 가이드

## 📋 개요

Onehago 크롤링 완료 후 인코딩이 깨진 데이터를 일괄 스캔하고 수정하는 스크립트입니다.

## 🎯 실행 시점

**크롤링이 100% 완료된 후** (예상: 2025년 11월 3일)

```bash
# 크롤링 완료 확인
python3 -c "
import json
with open('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/all_products_complete.json', 'r') as f:
    data = json.load(f)
    print(f'총 제품: {len(data):,}개')
    print(f'목표: 105,186개')
"
```

## 🚀 사용 방법

### 1. 인코딩 검수 및 수정 실행

```bash
cd /Users/oypnus/Project/rag-enterprise
python3 scripts/scan_and_fix_encoding.py
```

### 2. 실행 과정

```
1단계: 인코딩 문제 스캔 (전체 제품)
   ↓
2단계: 깨진 제품 재크롤링 (병렬 처리, 10개 워커)
   ↓
3단계: 수정된 데이터 저장
   ↓
4단계: 최종 검증
```

### 3. 출력 파일

- **입력**: `data/onehago/crawled/all_products_complete.json`
- **출력**: `data/onehago/crawled/all_products_fixed.json`
- **로그**: `/tmp/encoding_fix.log`

## 📊 검출 기준

다음 패턴을 가진 텍스트를 "깨진 데이터"로 판단:

1. **물음표 연속**: `���` 같은 패턴
2. **비정상 바이트**: 3개 이상 연속된 비ASCII 문자
3. **깨진 한글**: `酉곗궗`, `��⑸��` 같은 특정 패턴
4. **한글 없는 이상 문자**: 한글이 전혀 없고 이상한 문자만 5개 이상

## 🔧 재크롤링 방식

1. **EUC-KR 명시**: `response.encoding = 'euc-kr'`
2. **BeautifulSoup 사용**: HTML 파싱으로 정확한 텍스트 추출
3. **병렬 처리**: 10개 워커로 속도 최적화
4. **지연 시간**: 0.5~1.5초 랜덤 지연 (서버 부하 방지)

## 📈 예상 결과

### 현재 (513개 테스트 데이터)
```
발견된 문제: ~50개 (약 10%)
수정 완료: ~45개 (약 90%)
남은 문제: ~5개 (복원 불가)
```

### 전체 (105,186개 예상)
```
발견된 문제: ~10,500개 (약 10%)
수정 완료: ~9,500개 (약 90%)
실행 시간: 약 2-3시간
```

## ⚠️ 주의사항

1. **크롤링 완료 후 실행**: 진행 중일 때 실행하면 중복 처리 발생
2. **백업 권장**: 원본 파일 백업 후 실행
   ```bash
   cp all_products_complete.json all_products_complete_backup.json
   ```
3. **네트워크 안정**: 재크롤링 중 네트워크 끊김 주의
4. **로그 확인**: `/tmp/encoding_fix.log`에서 진행 상황 모니터링

## 🔄 재실행

만족스럽지 않은 경우 다시 실행 가능:

```bash
# 입력 파일을 fixed 버전으로 변경
cp all_products_fixed.json all_products_complete.json
python3 scripts/scan_and_fix_encoding.py
```

## 📝 검증

수정 후 샘플 확인:

```bash
python3 << 'EOF'
import json

with open('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/all_products_fixed.json', 'r') as f:
    products = json.load(f)

# 이전에 깨졌던 제품 (40934) 확인
for p in products:
    if p.get('product_id') == '40934':
        print("✅ 제품 ID: 40934")
        specs = p.get('specifications', {})
        for key in list(specs.keys())[:5]:
            print(f"   - {key}: {specs[key]}")
        break
EOF
```

## 🎯 성공 기준

- ✅ 한글이 정상적으로 읽힘
- ✅ `���`, `酉곗궗` 같은 패턴 없음
- ✅ specifications 필드가 모두 한글로 표시

## 📞 문제 발생 시

1. 로그 확인: `tail -f /tmp/encoding_fix.log`
2. 네트워크 확인: 재크롤링 중 타임아웃 발생 여부
3. 수동 확인: 특정 product_id로 직접 웹페이지 접속해서 데이터 확인
