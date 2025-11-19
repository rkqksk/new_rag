#!/bin/bash
# Ubuntu GNOME VNC 서버 재시작 스크립트
#
# 사용법: ./GNOME_VNC_RESTART.sh

echo "=== Ubuntu GNOME VNC 서버 재시작 ==="
echo ""

# 기존 VNC 서버 종료
echo "1. 기존 VNC 서버 종료..."
vncserver -kill :1 2>&1

# 잠시 대기
echo "2. 잠시 대기 중..."
sleep 3

# VNC 서버 재시작 (GNOME)
echo "3. VNC 서버 재시작 (GNOME 데스크톱)..."
vncserver :1 -geometry 1920x1080 -depth 24

echo ""
echo "=== 완료 ==="
echo ""
echo "✅ VNC 서버가 GNOME 데스크톱으로 시작되었습니다."
echo ""
echo "📱 안드로이드 VNC Viewer에서 연결:"
echo "   주소: 100.66.183.122:5901"
echo ""
echo "🔍 VNC 로그 확인:"
echo "   tail -f ~/.vnc/*.log"
