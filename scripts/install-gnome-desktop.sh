#!/bin/bash
# Ubuntu GNOME Desktop 자동 설치 스크립트

echo "======================================"
echo "  Ubuntu GNOME Desktop 설치 시작"
echo "======================================"
echo ""

# 1. 패키지 목록 업데이트
echo "📦 패키지 목록 업데이트 중..."
sudo apt update

# 2. Ubuntu Desktop Minimal 설치
echo ""
echo "🖥️  Ubuntu Desktop Minimal 설치 중..."
echo "   (약 5-10분 소요)"
sudo apt install -y ubuntu-desktop-minimal gnome-session

# 3. GDM3 디스플레이 매니저 설정
echo ""
echo "🔧 디스플레이 매니저 설정 중..."
sudo DEBIAN_FRONTEND=noninteractive apt install -y gdm3

# 4. VNC xstartup 파일을 GNOME용으로 변경
echo ""
echo "📝 VNC 설정을 GNOME으로 변경 중..."
cat > ~/.vnc/xstartup << 'EOF'
#!/bin/bash
# VNC xstartup for Ubuntu GNOME Desktop

unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS

# GNOME 데스크톱 환경 시작
export XKL_XMODMAP_DISABLE=1
export XDG_CURRENT_DESKTOP=GNOME
export XDG_SESSION_TYPE=x11
export GNOME_SHELL_SESSION_MODE=ubuntu

# GNOME 세션 시작
gnome-session --session=ubuntu &
EOF

chmod +x ~/.vnc/xstartup

# 5. VNC 서버 재시작
echo ""
echo "🔄 VNC 서버 재시작 중..."
vncserver -kill :1 2>/dev/null
sleep 3
vncserver :1 -geometry 1920x1080 -depth 24

echo ""
echo "======================================"
echo "  ✅ 설치 완료!"
echo "======================================"
echo ""
echo "📱 안드로이드 VNC Viewer에서 다시 연결:"
echo "   주소: 100.66.183.122:5901"
echo ""
echo "🎉 이제 완전한 Ubuntu GNOME 데스크톱으로"
echo "   터미널과 브라우저가 정상 작동합니다!"
echo ""
