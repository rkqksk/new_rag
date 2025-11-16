#!/bin/bash
#
# Cloudflare Tunnel 자동 설정 스크립트
# 도메인 구매 후 실행하면 모든 설정 자동 완료
#
# Usage: ./scripts/cloudflare/setup-tunnel.sh your-domain.com tunnel-name
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

step() {
    echo -e "${BLUE}▶ $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check arguments
if [ $# -lt 1 ]; then
    error "Usage: $0 <domain> [tunnel-name]"
    echo ""
    echo "Example:"
    echo "  $0 rag-enterprise.com"
    echo "  $0 myrag.ai my-tunnel"
    echo ""
    exit 1
fi

DOMAIN=$1
TUNNEL_NAME=${2:-${DOMAIN%%.*}}  # Default: first part of domain
USER=$(whoami)

echo "🚀 Cloudflare Tunnel 자동 설정"
echo "========================================"
echo ""
echo "도메인: $DOMAIN"
echo "Tunnel 이름: $TUNNEL_NAME"
echo "사용자: $USER"
echo ""

# 1. Check if cloudflared is installed
step "1/7 Cloudflared 설치 확인..."
if ! command -v cloudflared &> /dev/null; then
    warning "Cloudflared가 설치되어 있지 않습니다. 설치 중..."
    
    cd /tmp
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    sudo dpkg -i cloudflared-linux-amd64.deb
    rm cloudflared-linux-amd64.deb
    
    success "Cloudflared 설치 완료"
else
    success "Cloudflared 이미 설치됨 ($(cloudflared --version | head -1))"
fi
echo ""

# 2. Login to Cloudflare
step "2/7 Cloudflare 로그인..."
if [ ! -f ~/.cloudflared/cert.pem ]; then
    warning "Cloudflare 로그인이 필요합니다"
    echo ""
    echo "브라우저가 열리면:"
    echo "  1. Cloudflare에 로그인"
    echo "  2. 도메인 선택: $DOMAIN"
    echo "  3. 'Authorize' 클릭"
    echo ""
    read -p "Enter 키를 눌러 계속..."
    
    cloudflared tunnel login
    
    if [ -f ~/.cloudflared/cert.pem ]; then
        success "Cloudflare 로그인 성공"
    else
        error "로그인 실패. 다시 시도해주세요."
        exit 1
    fi
else
    success "이미 로그인됨"
fi
echo ""

# 3. Create tunnel
step "3/7 Tunnel 생성..."
EXISTING_TUNNEL=$(cloudflared tunnel list 2>/dev/null | grep "$TUNNEL_NAME" | awk '{print $1}' || echo "")

if [ -n "$EXISTING_TUNNEL" ]; then
    warning "Tunnel이 이미 존재합니다: $TUNNEL_NAME ($EXISTING_TUNNEL)"
    TUNNEL_ID=$EXISTING_TUNNEL
else
    OUTPUT=$(cloudflared tunnel create $TUNNEL_NAME 2>&1)
    TUNNEL_ID=$(echo "$OUTPUT" | grep -oP 'Created tunnel .* with id \K[a-f0-9-]+' || echo "")
    
    if [ -z "$TUNNEL_ID" ]; then
        error "Tunnel 생성 실패"
        echo "$OUTPUT"
        exit 1
    fi
    
    success "Tunnel 생성 완료: $TUNNEL_ID"
fi
echo ""

# 4. Create config file
step "4/7 설정 파일 생성..."
mkdir -p ~/.cloudflared

CONFIG_FILE=~/.cloudflared/config.yml

cat > $CONFIG_FILE << EOF
# Cloudflare Tunnel Configuration
# Generated: $(date)
# Domain: $DOMAIN
# Tunnel: $TUNNEL_NAME ($TUNNEL_ID)

tunnel: $TUNNEL_ID
credentials-file: /home/$USER/.cloudflared/$TUNNEL_ID.json

ingress:
  # Main web app (Next.js)
  - hostname: $DOMAIN
    service: http://localhost:3000
    originRequest:
      noTLSVerify: true
      connectTimeout: 30s
      http2Origin: true

  # WWW subdomain
  - hostname: www.$DOMAIN
    service: http://localhost:3000
    originRequest:
      noTLSVerify: true
      connectTimeout: 30s
      http2Origin: true

  # API endpoint
  - hostname: api.$DOMAIN
    service: http://localhost:8001
    originRequest:
      noTLSVerify: true
      connectTimeout: 30s
      http2Origin: true

  # API documentation
  - hostname: docs.$DOMAIN
    service: http://localhost:8001
    path: /api/v1/docs
    originRequest:
      noTLSVerify: true
      connectTimeout: 30s

  # Monitoring
  - hostname: monitor.$DOMAIN
    service: http://localhost:3000
    originRequest:
      noTLSVerify: true
      connectTimeout: 30s

  # Admin panel
  - hostname: admin.$DOMAIN
    service: http://localhost:8001
    path: /admin
    originRequest:
      noTLSVerify: true
      connectTimeout: 30s

  # WebSocket
  - hostname: ws.$DOMAIN
    service: http://localhost:8001
    originRequest:
      noTLSVerify: true
      connectTimeout: 30s
      http2Origin: true

  # Default catch-all
  - service: http_status:404

loglevel: info
metrics: localhost:38301
EOF

success "설정 파일 생성: $CONFIG_FILE"
echo ""

# 5. Configure DNS routing
step "5/7 DNS 라우팅 설정..."

SUBDOMAINS=("$DOMAIN" "www.$DOMAIN" "api.$DOMAIN" "docs.$DOMAIN" "monitor.$DOMAIN" "admin.$DOMAIN" "ws.$DOMAIN")

for subdomain in "${SUBDOMAINS[@]}"; do
    # Check if route already exists
    EXISTING_ROUTE=$(cloudflared tunnel route dns $TUNNEL_NAME $subdomain 2>&1 || echo "")
    
    if echo "$EXISTING_ROUTE" | grep -q "already exists\|Created CNAME"; then
        success "DNS 라우팅: $subdomain"
    else
        warning "DNS 라우팅 실패: $subdomain"
        echo "$EXISTING_ROUTE"
    fi
done
echo ""

# 6. Create systemd service
step "6/7 Systemd 서비스 생성..."

SERVICE_FILE=/etc/systemd/system/cloudflared.service

sudo tee $SERVICE_FILE > /dev/null << EOF
[Unit]
Description=Cloudflare Tunnel
After=network.target

[Service]
Type=simple
User=$USER
ExecStart=/usr/bin/cloudflared tunnel run $TUNNEL_NAME
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

success "서비스 파일 생성: $SERVICE_FILE"

# Reload and enable service
sudo systemctl daemon-reload
sudo systemctl enable cloudflared
success "서비스 활성화 완료 (부팅 시 자동 시작)"
echo ""

# 7. Start service
step "7/7 서비스 시작..."
sudo systemctl restart cloudflared
sleep 3

if sudo systemctl is-active --quiet cloudflared; then
    success "Cloudflare Tunnel 실행 중 ✅"
else
    error "서비스 시작 실패"
    echo ""
    echo "로그 확인:"
    sudo journalctl -u cloudflared -n 20
    exit 1
fi
echo ""

# Summary
echo "========================================"
echo "✅ 설정 완료!"
echo "========================================"
echo ""
echo "접속 주소:"
echo "  • 메인:      https://$DOMAIN"
echo "  • API:       https://api.$DOMAIN"
echo "  • 문서:      https://docs.$DOMAIN"
echo "  • 모니터링:  https://monitor.$DOMAIN"
echo "  • 관리자:    https://admin.$DOMAIN"
echo ""
echo "서비스 관리:"
echo "  • 상태 확인: sudo systemctl status cloudflared"
echo "  • 재시작:    sudo systemctl restart cloudflared"
echo "  • 로그:      sudo journalctl -u cloudflared -f"
echo ""
echo "Tunnel 정보:"
echo "  • 이름: $TUNNEL_NAME"
echo "  • ID:   $TUNNEL_ID"
echo "  • 설정: $CONFIG_FILE"
echo ""

# Save tunnel info
INFO_FILE=~/.cloudflared/tunnel-info.txt
cat > $INFO_FILE << EOF
Cloudflare Tunnel Information
=============================
Created: $(date)

Domain: $DOMAIN
Tunnel Name: $TUNNEL_NAME
Tunnel ID: $TUNNEL_ID
Config File: $CONFIG_FILE
Service: cloudflared.service

Subdomains:
EOF

for subdomain in "${SUBDOMAINS[@]}"; do
    echo "  - https://$subdomain" >> $INFO_FILE
done

success "Tunnel 정보 저장: $INFO_FILE"
echo ""
echo "다음 단계:"
echo "  1. 로컬 서비스 시작 (pnpm dev)"
echo "  2. 브라우저에서 https://$DOMAIN 접속"
echo "  3. ./scripts/cloudflare/validate-tunnel.sh 실행하여 검증"
echo ""
