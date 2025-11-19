#!/bin/bash
# x11vnc 자동 시작 서비스 설정

echo "x11vnc 자동 시작 서비스 설정 중..."

# systemd 서비스 파일 생성
sudo tee /etc/systemd/system/x11vnc.service > /dev/null << 'EOF'
[Unit]
Description=x11vnc - VNC Server for X11 Display
After=display-manager.service network.target

[Service]
Type=simple
User=rkqksk
Environment="DISPLAY=:0"
Environment="XAUTHORITY=/home/rkqksk/.Xauthority"
ExecStart=/usr/bin/x11vnc -display :0 -auth guess -rfbauth /home/rkqksk/.vnc/x11vnc_passwd -forever -shared -rfbport 5900 -noxdamage -bg -o /var/log/x11vnc.log
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 서비스 활성화
sudo systemctl daemon-reload
sudo systemctl enable x11vnc
sudo systemctl start x11vnc

# 상태 확인
echo ""
echo "✅ x11vnc 서비스 설정 완료!"
echo ""
sudo systemctl status x11vnc --no-pager

echo ""
echo "📱 안드로이드에서 연결:"
echo "   주소: 100.66.183.122:5900"
echo ""
echo "🔧 명령어:"
echo "   시작: sudo systemctl start x11vnc"
echo "   중지: sudo systemctl stop x11vnc"
echo "   상태: sudo systemctl status x11vnc"
