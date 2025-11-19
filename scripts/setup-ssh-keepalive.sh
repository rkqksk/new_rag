#!/bin/bash
# SSH Keep-Alive 설정 (연결 끊김 방지)

echo "🔧 SSH Keep-Alive 설정 중..."
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 서버 측 설정 (sshd_config)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "📦 1. 서버 측 SSH 설정..."

# 백업
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup.$(date +%Y%m%d_%H%M%S)

# 기존 설정 제거 (주석 처리된 것 포함)
sudo sed -i '/^#\?ClientAliveInterval/d' /etc/ssh/sshd_config
sudo sed -i '/^#\?ClientAliveCountMax/d' /etc/ssh/sshd_config
sudo sed -i '/^#\?TCPKeepAlive/d' /etc/ssh/sshd_config

# 새로운 설정 추가
cat << 'EOF' | sudo tee -a /etc/ssh/sshd_config > /dev/null

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SSH Keep-Alive Settings (Added by setup-ssh-keepalive.sh)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Send keep-alive message every 60 seconds
ClientAliveInterval 60

# Never disconnect (0 = unlimited)
ClientAliveCountMax 0

# Enable TCP keep-alive
TCPKeepAlive yes
EOF

echo "   ✅ 서버 설정 완료"

# SSH 서비스 재시작
echo "   🔄 SSH 서비스 재시작..."
sudo systemctl restart sshd

echo "   ✅ SSH 서버 재시작 완료"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 클라이언트 측 설정 (~/.ssh/config)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "📱 2. 클라이언트 측 SSH 설정..."

# SSH config 디렉토리 생성
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# 백업 (파일이 존재하는 경우만)
if [[ -f ~/.ssh/config ]]; then
  cp ~/.ssh/config ~/.ssh/config.backup.$(date +%Y%m%d_%H%M%S)
fi

# 기존 Keep-Alive 설정 제거
sed -i '/ServerAliveInterval/d' ~/.ssh/config 2>/dev/null
sed -i '/ServerAliveCountMax/d' ~/.ssh/config 2>/dev/null
sed -i '/TCPKeepAlive/d' ~/.ssh/config 2>/dev/null

# 새로운 설정 추가
cat << 'EOF' >> ~/.ssh/config

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SSH Keep-Alive Settings (Added by setup-ssh-keepalive.sh)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Host *
    # Send keep-alive message every 60 seconds
    ServerAliveInterval 60

    # Never disconnect (0 = unlimited)
    ServerAliveCountMax 0

    # Enable TCP keep-alive
    TCPKeepAlive yes
EOF

chmod 600 ~/.ssh/config

echo "   ✅ 클라이언트 설정 완료"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 설정 확인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ SSH Keep-Alive 설정 완료!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 설정 내용:"
echo ""
echo "  서버 측 (sshd_config):"
echo "    - ClientAliveInterval: 60초마다 keep-alive 전송"
echo "    - ClientAliveCountMax: 0 (무제한, 절대 끊지 않음)"
echo "    - TCPKeepAlive: 활성화"
echo ""
echo "  클라이언트 측 (~/.ssh/config):"
echo "    - ServerAliveInterval: 60초마다 keep-alive 전송"
echo "    - ServerAliveCountMax: 0 (무제한, 절대 끊지 않음)"
echo "    - TCPKeepAlive: 활성화"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 클라이언트가 끊지 않는 한 SSH 연결이 영구 유지됩니다!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 백업 파일:"
echo "   서버: /etc/ssh/sshd_config.backup.*"
echo "   클라이언트: ~/.ssh/config.backup.*"
echo ""
echo "🔄 설정 확인:"
echo "   sudo grep -E 'ClientAlive|TCPKeepAlive' /etc/ssh/sshd_config | grep -v '^#'"
echo "   grep -E 'ServerAlive|TCPKeepAlive' ~/.ssh/config | grep -v '^#'"
