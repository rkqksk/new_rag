#!/bin/bash
#
# Cloudflare Tunnel 검증 스크립트
# 모든 엔드포인트가 제대로 작동하는지 확인
#

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Get domain from tunnel config
if [ ! -f ~/.cloudflared/tunnel-info.txt ]; then
    error "Tunnel 정보를 찾을 수 없습니다"
    echo "먼저 ./scripts/cloudflare/setup-tunnel.sh를 실행하세요"
    exit 1
fi

DOMAIN=$(grep "^Domain:" ~/.cloudflared/tunnel-info.txt | awk '{print $2}')

if [ -z "$DOMAIN" ]; then
    error "도메인 정보를 찾을 수 없습니다"
    exit 1
fi

echo "🔍 Cloudflare Tunnel 검증"
echo "========================================"
echo "도메인: $DOMAIN"
echo ""

PASSED=0
FAILED=0

# 1. Check service status
echo "1️⃣  Systemd 서비스 상태"
echo "----------------------------------------"
if sudo systemctl is-active --quiet cloudflared; then
    success "cloudflared 서비스 실행 중"
    PASSED=$((PASSED + 1))
else
    error "cloudflared 서비스 중지됨"
    FAILED=$((FAILED + 1))
    info "sudo systemctl start cloudflared"
fi
echo ""

# 2. Check local services
echo "2️⃣  로컬 서비스 확인"
echo "----------------------------------------"

# Check Next.js (port 3000)
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    success "Next.js 앱 실행 중 (port 3000)"
    PASSED=$((PASSED + 1))
else
    warning "Next.js 앱이 실행되지 않음 (port 3000)"
    info "pnpm dev 또는 pnpm web"
    FAILED=$((FAILED + 1))
fi

# Check API (port 8001)
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    success "API 서버 실행 중 (port 8001)"
    PASSED=$((PASSED + 1))
else
    warning "API 서버가 실행되지 않음 (port 8001)"
    info "pnpm api 또는 uvicorn main:app"
    FAILED=$((FAILED + 1))
fi
echo ""

# 3. Check DNS resolution
echo "3️⃣  DNS 해상도 확인"
echo "----------------------------------------"

SUBDOMAINS=("$DOMAIN" "www.$DOMAIN" "api.$DOMAIN" "docs.$DOMAIN")

for subdomain in "${SUBDOMAINS[@]}"; do
    if nslookup $subdomain > /dev/null 2>&1; then
        # Check if it resolves to Cloudflare tunnel
        CNAME=$(nslookup $subdomain 2>/dev/null | grep "canonical name" | awk '{print $NF}' || echo "")
        if [[ $CNAME == *"cfargotunnel.com"* ]]; then
            success "DNS: $subdomain → Cloudflare Tunnel"
            PASSED=$((PASSED + 1))
        else
            warning "DNS: $subdomain (not pointing to Cloudflare Tunnel)"
            FAILED=$((FAILED + 1))
        fi
    else
        error "DNS: $subdomain (resolution failed)"
        FAILED=$((FAILED + 1))
    fi
done
echo ""

# 4. Check HTTPS endpoints
echo "4️⃣  HTTPS 엔드포인트 테스트"
echo "----------------------------------------"

# Main site
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 https://$DOMAIN 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "304" ]; then
    success "메인 사이트: https://$DOMAIN (HTTP $HTTP_CODE)"
    PASSED=$((PASSED + 1))
else
    error "메인 사이트: https://$DOMAIN (HTTP $HTTP_CODE)"
    FAILED=$((FAILED + 1))
fi

# API health
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 https://api.$DOMAIN/health 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    success "API 헬스체크: https://api.$DOMAIN/health (HTTP $HTTP_CODE)"
    PASSED=$((PASSED + 1))
else
    error "API 헬스체크: https://api.$DOMAIN/health (HTTP $HTTP_CODE)"
    FAILED=$((FAILED + 1))
fi

# API docs
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 https://docs.$DOMAIN 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "307" ]; then
    success "API 문서: https://docs.$DOMAIN (HTTP $HTTP_CODE)"
    PASSED=$((PASSED + 1))
else
    warning "API 문서: https://docs.$DOMAIN (HTTP $HTTP_CODE)"
    FAILED=$((FAILED + 1))
fi
echo ""

# 5. Check SSL certificate
echo "5️⃣  SSL 인증서 확인"
echo "----------------------------------------"

SSL_INFO=$(echo | openssl s_client -connect $DOMAIN:443 -servername $DOMAIN 2>/dev/null | openssl x509 -noout -issuer 2>/dev/null || echo "")

if [[ $SSL_INFO == *"Cloudflare"* ]] || [[ $SSL_INFO == *"cloudflare"* ]]; then
    success "SSL 인증서: Cloudflare 발급 ✓"
    PASSED=$((PASSED + 1))
elif [ -n "$SSL_INFO" ]; then
    warning "SSL 인증서: 발급됨 (not Cloudflare)"
    info "$SSL_INFO"
    PASSED=$((PASSED + 1))
else
    error "SSL 인증서: 확인 실패"
    FAILED=$((FAILED + 1))
fi
echo ""

# 6. Check tunnel metrics
echo "6️⃣  Tunnel 메트릭 확인"
echo "----------------------------------------"

if curl -s http://localhost:38301/metrics > /dev/null 2>&1; then
    success "Tunnel 메트릭 사용 가능 (http://localhost:38301/metrics)"
    PASSED=$((PASSED + 1))
else
    warning "Tunnel 메트릭 사용 불가"
    FAILED=$((FAILED + 1))
fi
echo ""

# Summary
echo "========================================"
echo "검증 요약"
echo "========================================"
echo ""

TOTAL=$((PASSED + FAILED))
PASS_RATE=$((PASSED * 100 / TOTAL))

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ 모든 검증 통과! ($PASSED/$TOTAL)${NC}"
    echo ""
    echo "접속 가능한 주소:"
    echo "  • 메인:     https://$DOMAIN"
    echo "  • API:      https://api.$DOMAIN"
    echo "  • 문서:     https://docs.$DOMAIN"
    echo "  • 모니터:   https://monitor.$DOMAIN"
    echo ""
    exit 0
else
    echo -e "${YELLOW}⚠️  일부 검증 실패 ($PASSED/$TOTAL passed, $FAILED failed)${NC}"
    echo ""
    echo "문제 해결:"
    echo "  1. 로컬 서비스 시작: pnpm dev"
    echo "  2. Tunnel 재시작: sudo systemctl restart cloudflared"
    echo "  3. 로그 확인: sudo journalctl -u cloudflared -n 50"
    echo ""
    exit 1
fi
