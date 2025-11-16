# Cloudflare 빠른 시작 - Tier1 (무료)

**결제만 하면 바로 사용** - 모든 설정 자동화 완료 ✅

**소요 시간**: 10분
**비용**: $9.77-120/year (도메인만, tier 선택에 따라 다름)
**난이도**: ⭐ 매우 쉬움

---

## 🎯 Tier 선택 (시작: Tier1 무료)

### Tier1 - 무료 (추천: 시작용) ⭐

**비용**: 도메인만 ($9.77-120/year)
- ✅ Cloudflare Tunnel (무료)
- ✅ 자동 HTTPS (무료)
- ✅ CDN (무료)
- ✅ 기본 DDoS 보호 (무료)

**월 환산**: $0.81-10/month (도메인 종류에 따라)

### Tier2 - 유료 (나중에 업그레이드)

**비용**: $30-50/month
- Cloudflare Pro Plan ($20/month)
- Workers (엣지 캐싱, $5/month)
- R2 Storage (파일 저장, $5-15/month)

**권장**: Tier1으로 시작 → 트래픽 증가 시 Tier2로 업그레이드

---

## 🚀 원클릭 배포 (Tier1)

### 1단계: Cloudflare에서 도메인 구매 (5분)

**추천 도메인**:
- `.com` - $9.77/year (가장 저렴, 신뢰도 높음) ⭐⭐⭐⭐⭐
- `.dev` - $12/year (개발자 친화적) ⭐⭐⭐⭐⭐
- `.ai` - $120/year (AI 브랜딩, 비쌈) ⭐⭐⭐⭐

**구매 과정**:
```
1. https://dash.cloudflare.com/sign-up
   → 계정 생성 (이메일 + 비밀번호)

2. Domain Registration → Register Domain
   → 도메인 검색 (예: rag-enterprise.com)

3. 도메인 선택 → Continue

4. 결제 정보 입력
   → Name, Email, Address, Phone
   → Credit Card 또는 PayPal

5. Complete Purchase 클릭

✅ 완료! (도메인 구매 완료)
```

### 2단계: 원클릭 배포 실행 (5분)

Ubuntu 서버에서 실행:

```bash
# 프로젝트 디렉토리로 이동
cd /home/user/new_rag

# 원클릭 배포 (도메인을 본인 것으로 변경)
./scripts/cloudflare/one-click-deploy.sh rag-enterprise.com

# 또는 대화형 모드
./scripts/cloudflare/one-click-deploy.sh
→ 도메인 입력: rag-enterprise.com
```

**스크립트가 자동으로 수행**:
1. ✅ Cloudflared 설치
2. ✅ Cloudflare 로그인 (브라우저에서 인증)
3. ✅ Tunnel 생성
4. ✅ DNS 라우팅 설정 (7개 서브도메인)
5. ✅ Systemd 서비스 등록
6. ✅ 서비스 시작 및 검증

### 3단계: 로컬 서비스 시작

다른 터미널에서:

```bash
# 모든 서비스 시작
pnpm dev

# 또는 개별 시작
pnpm web  # Next.js (port 3000)
pnpm api  # FastAPI (port 8001)
```

### 4단계: 접속 확인 (1분)

브라우저에서:
```
https://rag-enterprise.com          (메인 웹사이트)
https://api.rag-enterprise.com/health  (API)
https://docs.rag-enterprise.com     (API 문서)
```

**완료!** 🎉

---

## 📊 Tier1에서 사용 가능한 기능

### 무료로 제공되는 것

✅ **자동 HTTPS** - Cloudflare SSL 인증서
✅ **전 세계 CDN** - 300+ 위치
✅ **무제한 대역폭** - 트래픽 제한 없음
✅ **DDoS 보호** - 기본 보안
✅ **방화벽 설정 불필요** - 로컬 서버 직접 노출 안 함
✅ **자동 시작** - systemd 서비스

### 주요 엔드포인트

| 엔드포인트 | URL | 설명 |
|-----------|-----|------|
| 메인 웹사이트 | https://your-domain.com | Next.js 앱 |
| WWW | https://www.your-domain.com | 메인으로 리다이렉트 |
| API | https://api.your-domain.com | FastAPI 백엔드 |
| API 문서 | https://docs.your-domain.com | Swagger UI |
| 모니터링 | https://monitor.your-domain.com | Grafana |
| 관리자 | https://admin.your-domain.com | 관리 패널 |
| WebSocket | https://ws.your-domain.com | 실시간 기능 |

---

## 🔧 서비스 관리

### 상태 확인
```bash
sudo systemctl status cloudflared
```

### 재시작
```bash
sudo systemctl restart cloudflared
```

### 로그 확인
```bash
sudo journalctl -u cloudflared -f
```

### 검증
```bash
./scripts/cloudflare/validate-tunnel.sh
```

---

## 💡 Tier2로 업그레이드 시기

다음 상황에서 Tier2 고려:

1. **트래픽 증가** - 월 100만 요청 이상
2. **엣지 캐싱 필요** - 응답 속도 최적화
3. **파일 저장소 필요** - 이미지, 비디오 등
4. **고급 보안 필요** - WAF, Rate Limiting

### Tier2 업그레이드 방법

```bash
# Cloudflare Dashboard
→ Plan Selection → Upgrade to Pro ($20/month)

# Workers 활성화
→ Workers → Enable ($5/month)

# R2 Storage 활성화
→ R2 → Create Bucket ($0.015/GB/month)
```

**자세한 내용**: `docs/planning/CLOUDFLARE_HOSTING_PLAN.md`

---

## 📁 생성된 파일

### 자동화 스크립트 (3개)
- `scripts/cloudflare/setup-tunnel.sh` - Tunnel 설정 자동화
- `scripts/cloudflare/validate-tunnel.sh` - 검증 스크립트
- `scripts/cloudflare/one-click-deploy.sh` - 원클릭 배포

### 설정 파일 (2개)
- `infrastructure/cloudflare/config.yml.template` - Tunnel 설정 템플릿
- `~/.cloudflared/config.yml` - 실제 설정 파일 (자동 생성)

### Systemd 서비스
- `/etc/systemd/system/cloudflared.service` - 자동 시작 서비스

---

## 🚨 문제 해결

### "tunnel login failed"
```bash
# 인증서 삭제 후 재시도
rm ~/.cloudflared/cert.pem
cloudflared tunnel login
```

### "502 Bad Gateway"
```bash
# 로컬 서버 확인
curl http://localhost:3000
curl http://localhost:8001/health

# 서버 시작
pnpm dev

# Tunnel 재시작
sudo systemctl restart cloudflared
```

### DNS 전파 대기
도메인 구매 후 DNS가 전파되는 데 최대 48시간 소요될 수 있습니다.
보통 5-10분 내 완료됩니다.

---

## 💰 비용 요약 (Tier1)

### 초기 비용
| 항목 | 비용 |
|------|------|
| 도메인 (.com) | $9.77/year |
| 도메인 (.dev) | $12/year |
| 도메인 (.ai) | $120/year |
| Cloudflare Tunnel | $0 ✅ |
| SSL/HTTPS | $0 ✅ |
| CDN | $0 ✅ |
| DDoS 보호 | $0 ✅ |

### 월 비용
- `.com`: $0.81/month
- `.dev`: $1/month
- `.ai`: $10/month

**추천**: `.com` ($9.77/year = $0.81/month) ⭐

---

## 🎉 완료!

축하합니다! 이제 로컬 Ubuntu 서버가 공개 웹사이트로 호스팅되었습니다.

**접속 주소**:
- https://your-domain.com (본인 도메인)

**특징**:
- ✅ $0.81-10/month (도메인만)
- ✅ 자동 HTTPS
- ✅ 전 세계 CDN
- ✅ 무제한 대역폭
- ✅ Tier2로 쉽게 업그레이드 가능

**다음 단계**:
1. Cloudflare Dashboard 최적화 (SSL, 캐싱 등)
2. 트래픽 모니터링
3. 필요시 Tier2로 업그레이드

---

**Created**: 2025-11-17
**Version**: 1.0
**Tier**: 1 (무료) → 2 (유료, 선택)
**Status**: Ready for Payment ✅
