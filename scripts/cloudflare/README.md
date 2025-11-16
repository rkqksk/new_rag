# Cloudflare 자동화 스크립트

**결제만 하면 바로 사용 가능** - 모든 설정 자동화 완료 ✅

---

## 📁 파일 구조

```
scripts/cloudflare/
├── README.md                    # 이 파일
├── one-click-deploy.sh          # 원클릭 배포 스크립트
├── setup-tunnel.sh              # Tunnel 설정 자동화
└── validate-tunnel.sh           # 검증 스크립트

infrastructure/cloudflare/
└── config.yml.template          # Tunnel 설정 템플릿

docs/guides/
├── CLOUDFLARE_DOMAIN_SETUP.md   # 상세 설정 가이드
└── CLOUDFLARE_TIER_COMPARISON.md # Tier 비교

CLOUDFLARE_QUICK_START.md        # 빠른 시작 가이드 (루트)
```

---

## 🚀 빠른 시작 (3단계)

### 1. Cloudflare에서 도메인 구매

```
https://dash.cloudflare.com
→ Domain Registration
→ 도메인 검색 및 구매 ($9.77-120/year)
```

추천:
- `.com` - $9.77/year (가장 저렴) ⭐⭐⭐⭐⭐
- `.dev` - $12/year (개발자 친화적) ⭐⭐⭐⭐⭐
- `.ai` - $120/year (AI 브랜딩)

### 2. 원클릭 배포 실행

```bash
# 프로젝트 디렉토리
cd /home/user/new_rag

# 배포 (도메인을 본인 것으로 변경)
./scripts/cloudflare/one-click-deploy.sh your-domain.com
```

### 3. 로컬 서비스 시작

```bash
# 다른 터미널에서
pnpm dev
```

**완료!** https://your-domain.com 접속

---

## 📜 스크립트 상세

### 1. one-click-deploy.sh

**설명**: 모든 설정을 자동으로 수행하는 올인원 스크립트

**사용법**:
```bash
./scripts/cloudflare/one-click-deploy.sh your-domain.com
```

**수행 작업**:
1. Cloudflared 설치 확인
2. Tunnel 설정 (setup-tunnel.sh 호출)
3. 로컬 서비스 확인
4. 검증 (validate-tunnel.sh 호출)
5. 배포 정보 저장

**소요 시간**: ~5분

### 2. setup-tunnel.sh

**설명**: Cloudflare Tunnel 설정 자동화

**사용법**:
```bash
./scripts/cloudflare/setup-tunnel.sh your-domain.com [tunnel-name]
```

**예시**:
```bash
./scripts/cloudflare/setup-tunnel.sh rag-enterprise.com
./scripts/cloudflare/setup-tunnel.sh myrag.ai my-tunnel
```

**수행 작업**:
1. Cloudflared 설치
2. Cloudflare 로그인
3. Tunnel 생성
4. config.yml 생성
5. DNS 라우팅 설정 (7개 서브도메인)
6. Systemd 서비스 생성
7. 서비스 시작

**생성 파일**:
- `~/.cloudflared/config.yml` - Tunnel 설정
- `/etc/systemd/system/cloudflared.service` - Systemd 서비스
- `~/.cloudflared/tunnel-info.txt` - Tunnel 정보

### 3. validate-tunnel.sh

**설명**: 모든 엔드포인트 검증

**사용법**:
```bash
./scripts/cloudflare/validate-tunnel.sh
```

**검증 항목**:
1. ✅ Systemd 서비스 상태
2. ✅ 로컬 서비스 실행 (port 3000, 8001)
3. ✅ DNS 해상도 (7개 서브도메인)
4. ✅ HTTPS 엔드포인트 접근
5. ✅ SSL 인증서
6. ✅ Tunnel 메트릭

**출력**:
- 통과: 모든 체크 성공 → 배포 완료
- 실패: 문제 항목 표시 → 해결 방법 제시

---

## 🌐 생성되는 서브도메인

| 서브도메인 | 서비스 | 포트 | 설명 |
|-----------|--------|------|------|
| your-domain.com | Next.js | 3000 | 메인 웹사이트 |
| www.your-domain.com | Next.js | 3000 | WWW 리다이렉트 |
| api.your-domain.com | FastAPI | 8001 | API 엔드포인트 |
| docs.your-domain.com | FastAPI | 8001 | API 문서 (Swagger) |
| monitor.your-domain.com | Grafana | 3000 | 모니터링 |
| admin.your-domain.com | FastAPI | 8001 | 관리자 패널 |
| ws.your-domain.com | Socket.IO | 8001 | WebSocket |

---

## 🔧 서비스 관리

### 상태 확인
```bash
sudo systemctl status cloudflared
```

### 시작/중지/재시작
```bash
sudo systemctl start cloudflared
sudo systemctl stop cloudflared
sudo systemctl restart cloudflared
```

### 로그 확인
```bash
# 실시간 로그
sudo journalctl -u cloudflared -f

# 최근 50줄
sudo journalctl -u cloudflared -n 50
```

### Tunnel 정보
```bash
# Tunnel 목록
cloudflared tunnel list

# 설정 파일 확인
cat ~/.cloudflared/config.yml

# Tunnel 정보
cat ~/.cloudflared/tunnel-info.txt
```

---

## 🚨 문제 해결

### "cloudflared: command not found"

```bash
# 수동 설치
cd /tmp
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

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

### "DNS route failed"

Cloudflare Dashboard에서 도메인이 추가되었는지 확인:
```
https://dash.cloudflare.com
→ Websites → 본인 도메인 확인
```

### 서비스 시작 실패

```bash
# 로그 확인
sudo journalctl -u cloudflared -n 50

# 설정 파일 확인
cat ~/.cloudflared/config.yml

# 수동 실행 테스트
cloudflared tunnel run your-tunnel-name
```

---

## 📊 Tier 선택

### Tier1 - 무료 (시작 추천)

**비용**: $0.81-10/month (도메인만)

**기능**:
- ✅ Cloudflare Tunnel
- ✅ 자동 HTTPS
- ✅ CDN
- ✅ 기본 DDoS 보호

### Tier2 - 유료 (업그레이드)

**비용**: $30-50/month

**추가 기능**:
- ✅ Workers (엣지 캐싱)
- ✅ R2 Storage (파일 저장)
- ✅ Pro Plan (고급 보안)

**자세한 내용**: `docs/guides/CLOUDFLARE_TIER_COMPARISON.md`

---

## 💡 추가 리소스

### 문서
- `CLOUDFLARE_QUICK_START.md` - 빠른 시작 가이드
- `docs/guides/CLOUDFLARE_DOMAIN_SETUP.md` - 상세 설정 가이드
- `docs/guides/CLOUDFLARE_TIER_COMPARISON.md` - Tier 비교
- `docs/planning/CLOUDFLARE_HOSTING_PLAN.md` - 호스팅 플랜

### 템플릿
- `infrastructure/cloudflare/config.yml.template` - Tunnel 설정 템플릿

### Cloudflare 공식 문서
- https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/
- https://developers.cloudflare.com/registrar/

---

## 🎉 성공 체크리스트

- [ ] Cloudflare 계정 생성
- [ ] 도메인 구매
- [ ] one-click-deploy.sh 실행
- [ ] 로컬 서비스 시작 (pnpm dev)
- [ ] validate-tunnel.sh 통과
- [ ] 브라우저에서 접속 확인
- [ ] HTTPS 확인 (🔒 자물쇠)
- [ ] Cloudflare Dashboard 최적화

---

**Created**: 2025-11-17
**Version**: 1.0
**Status**: Production Ready ✅
**Cost**: $0.81-10/month (Tier1, 도메인만)
