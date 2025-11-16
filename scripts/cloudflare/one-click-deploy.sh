#!/bin/bash
#
# Cloudflare 원클릭 배포 스크립트
# 도메인만 입력하면 모든 설정 자동 완료
#

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "╔════════════════════════════════════════════╗"
echo "║  Cloudflare 원클릭 배포 스크립트          ║"
echo "║  RAG Enterprise v11.0.0                   ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# Check if domain is provided
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}도메인을 입력하세요${NC}"
    echo ""
    echo "예시:"
    echo "  ./scripts/cloudflare/one-click-deploy.sh rag-enterprise.com"
    echo "  ./scripts/cloudflare/one-click-deploy.sh myrag.ai"
    echo "  ./scripts/cloudflare/one-click-deploy.sh rag-search.dev"
    echo ""
    read -p "도메인 입력: " DOMAIN
    
    if [ -z "$DOMAIN" ]; then
        echo -e "${RED}도메인을 입력해야 합니다${NC}"
        exit 1
    fi
else
    DOMAIN=$1
fi

echo ""
echo -e "${BLUE}도메인: $DOMAIN${NC}"
echo ""
echo "다음 작업이 자동으로 수행됩니다:"
echo "  1. Cloudflared 설치 (필요시)"
echo "  2. Cloudflare 로그인"
echo "  3. Tunnel 생성"
echo "  4. DNS 라우팅 설정"
echo "  5. Systemd 서비스 등록"
echo "  6. 서비스 시작"
echo "  7. 검증"
echo ""
read -p "계속하시겠습니까? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "취소되었습니다."
    exit 0
fi

echo ""

# Step 1: Setup tunnel
echo -e "${BLUE}══════════════════════════════════════════${NC}"
echo -e "${BLUE}1. Cloudflare Tunnel 설정${NC}"
echo -e "${BLUE}══════════════════════════════════════════${NC}"
echo ""

if [ -f scripts/cloudflare/setup-tunnel.sh ]; then
    bash scripts/cloudflare/setup-tunnel.sh "$DOMAIN"
else
    echo -e "${RED}❌ setup-tunnel.sh를 찾을 수 없습니다${NC}"
    exit 1
fi

echo ""

# Step 2: Start local services
echo -e "${BLUE}══════════════════════════════════════════${NC}"
echo -e "${BLUE}2. 로컬 서비스 시작${NC}"
echo -e "${BLUE}══════════════════════════════════════════${NC}"
echo ""

# Check if services are running
WEB_RUNNING=false
API_RUNNING=false

if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Next.js 앱이 이미 실행 중${NC}"
    WEB_RUNNING=true
fi

if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API 서버가 이미 실행 중${NC}"
    API_RUNNING=true
fi

if [ "$WEB_RUNNING" = false ] || [ "$API_RUNNING" = false ]; then
    echo ""
    echo -e "${YELLOW}로컬 서비스를 시작해주세요:${NC}"
    echo ""
    echo "  터미널 1: pnpm web   # Next.js (port 3000)"
    echo "  터미널 2: pnpm api   # FastAPI (port 8001)"
    echo ""
    echo "또는:"
    echo "  pnpm dev  # 모든 서비스 시작"
    echo ""
    read -p "서비스를 시작한 후 Enter를 누르세요..."
fi

echo ""

# Step 3: Wait for tunnel to be ready
echo -e "${BLUE}══════════════════════════════════════════${NC}"
echo -e "${BLUE}3. Tunnel 연결 대기${NC}"
echo -e "${BLUE}══════════════════════════════════════════${NC}"
echo ""

echo "Cloudflare Tunnel이 연결될 때까지 대기 중..."
sleep 5

for i in {1..12}; do
    if sudo systemctl is-active --quiet cloudflared; then
        echo -e "${GREEN}✅ Tunnel 연결됨${NC}"
        break
    fi
    echo "대기 중... ($i/12)"
    sleep 5
done

echo ""

# Step 4: Validate
echo -e "${BLUE}══════════════════════════════════════════${NC}"
echo -e "${BLUE}4. 배포 검증${NC}"
echo -e "${BLUE}══════════════════════════════════════════${NC}"
echo ""

if [ -f scripts/cloudflare/validate-tunnel.sh ]; then
    bash scripts/cloudflare/validate-tunnel.sh
    VALIDATION_RESULT=$?
else
    echo -e "${YELLOW}⚠️  검증 스크립트를 찾을 수 없습니다${NC}"
    VALIDATION_RESULT=1
fi

echo ""

# Summary
if [ $VALIDATION_RESULT -eq 0 ]; then
    echo "╔════════════════════════════════════════════╗"
    echo "║          🎉 배포 완료! 🎉                 ║"
    echo "╚════════════════════════════════════════════╝"
    echo ""
    echo "접속 주소:"
    echo ""
    echo "  🌐 메인 웹사이트:  https://$DOMAIN"
    echo "  🔌 API:           https://api.$DOMAIN"
    echo "  📚 API 문서:       https://docs.$DOMAIN"
    echo "  📊 모니터링:       https://monitor.$DOMAIN"
    echo "  ⚙️  관리자:         https://admin.$DOMAIN"
    echo ""
    echo "특징:"
    echo "  ✅ 자동 HTTPS (Cloudflare SSL)"
    echo "  ✅ 전 세계 CDN (300+ 위치)"
    echo "  ✅ DDoS 보호"
    echo "  ✅ 무제한 대역폭"
    echo "  ✅ 자동 시작 (systemd)"
    echo ""
    echo "서비스 관리:"
    echo "  • 상태: sudo systemctl status cloudflared"
    echo "  • 재시작: sudo systemctl restart cloudflared"
    echo "  • 로그: sudo journalctl -u cloudflared -f"
    echo ""
else
    echo "╔════════════════════════════════════════════╗"
    echo "║       ⚠️  배포 일부 완료 ⚠️                ║"
    echo "╚════════════════════════════════════════════╝"
    echo ""
    echo "일부 검증에 실패했지만 기본 설정은 완료되었습니다."
    echo ""
    echo "문제 해결:"
    echo "  1. 로컬 서비스 확인: curl http://localhost:3000"
    echo "  2. Tunnel 상태: sudo systemctl status cloudflared"
    echo "  3. 재검증: ./scripts/cloudflare/validate-tunnel.sh"
    echo ""
fi

# Save deployment info
DEPLOY_INFO="$HOME/.cloudflared/deployment-$(date +%Y%m%d-%H%M%S).txt"
cat > "$DEPLOY_INFO" << EOF
Cloudflare Deployment Summary
=============================
Date: $(date)
Domain: $DOMAIN

Deployment Status: $([ $VALIDATION_RESULT -eq 0 ] && echo "SUCCESS" || echo "PARTIAL")

URLs:
  Main: https://$DOMAIN
  API: https://api.$DOMAIN
  Docs: https://docs.$DOMAIN
  Monitor: https://monitor.$DOMAIN
  Admin: https://admin.$DOMAIN

Service: cloudflared (systemd)
Config: ~/.cloudflared/config.yml

Next Steps:
  1. Test all endpoints in browser
  2. Configure Cloudflare Dashboard settings
  3. Set up monitoring and alerts
  4. Review security settings

For support: docs/guides/CLOUDFLARE_DOMAIN_SETUP.md
EOF

echo "배포 정보 저장: $DEPLOY_INFO"
echo ""
