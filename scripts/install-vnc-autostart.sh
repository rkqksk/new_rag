#!/bin/bash
# x11vnc 부팅 시 자동 시작 설정

echo "🔧 x11vnc 자동 시작 서비스 설정 중..."

# systemd 서비스 파일 생성
sudo tee /etc/systemd/system/x11vnc.service > /dev/null << 'EOF'
[Unit]
Description=x11vnc - VNC Server for X11 Display
After=display-manager.service network-online.target
Wants=network-online.target

[Service]
Type=simple
User=rkqksk
Environment="DISPLAY=:0"
Environment="XAUTHORITY=/home/rkqksk/.Xauthority"

# x11vnc 시작 (로컬 화면 미러링)
ExecStart=/usr/bin/x11vnc \
  -display :0 \
  -auth guess \
  -rfbauth /home/rkqksk/.vnc/x11vnc_passwd \
  -forever \
  -shared \
  -rfbport 5900 \
  -noxdamage \
  -repeat \
  -nap \
  -wait 50 \
  -deferupdate 1 \
  -o /var/log/x11vnc.log

# 30분 후 자동 종료
RuntimeMaxSec=1800

Restart=no

[Install]
WantedBy=multi-user.target
EOF

# 서비스 권한 설정
sudo chmod 644 /etc/systemd/system/x11vnc.service

# systemd 재로드
sudo systemctl daemon-reload

# 서비스 활성화 (부팅 시 자동 시작)
sudo systemctl enable x11vnc.service

# 서비스 시작
sudo systemctl start x11vnc.service

echo ""
echo "✅ x11vnc 자동 시작 설정 완료!"
echo ""

# 상태 확인
sudo systemctl status x11vnc.service --no-pager -l

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 사용 방법:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  시작:   sudo systemctl start x11vnc"
echo "  중지:   sudo systemctl stop x11vnc"
echo "  재시작: sudo systemctl restart x11vnc"
echo "  상태:   sudo systemctl status x11vnc"
echo ""
echo "  자동 시작 활성화:   sudo systemctl enable x11vnc"
echo "  자동 시작 비활성화: sudo systemctl disable x11vnc"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 x11vnc 자동 시작 + 30분 타이머 설정 완료!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⏱️  타이머: 재부팅 시 VNC 시작 → 30분 후 자동 종료"
echo "📱 VNC 주소: $(tailscale ip -4 2>/dev/null || echo "YOUR_IP"):5900"
echo ""
echo "💡 30분 이후에도 계속 사용하려면:"
echo "   ssh로 접속 → vnc_on 실행"
