# VNC 원격 접속 설정 가이드

## 안드로이드폰 → 리눅스 VNC 접속

### 📋 개요

안드로이드폰을 사용해서 리눅스 데스크톱에 원격으로 접속하는 방법입니다.

**필요한 것**:
- 리눅스 서버 (Ubuntu 20.04+)
- 안드로이드폰
- 같은 네트워크 또는 인터넷 연결

---

## 🚀 빠른 시작

### 리눅스 서버 (한 번만 설정)

```bash
# 1. VNC 서버 설치
sudo apt update
sudo apt install -y tigervnc-standalone-server tigervnc-common

# 2. VNC 비밀번호 설정
vncpasswd
# 비밀번호 입력 (8자 이하 권장)
# View-only 비밀번호는 'n' 선택

# 3. VNC 서버 시작 (디스플레이 :1, 해상도 1920x1080)
vncserver :1 -geometry 1920x1080 -depth 24

# 4. 서버 IP 확인
hostname -I
# 예: 192.168.0.100
```

### 안드로이드폰

```
1. Play Store에서 "VNC Viewer" 설치
   → RealVNC Viewer (무료, 추천)

2. 앱 실행 → 새 연결 추가
   - Address: 192.168.0.100:5901
   - Name: 내 리눅스 PC

3. 연결 → VNC 비밀번호 입력 → 완료!
```

---

## 📖 상세 설정

### 1. 리눅스 VNC 서버 설치 및 설정

#### Option 1: TigerVNC (가벼움, 추천)

```bash
# 설치
sudo apt update
sudo apt install -y tigervnc-standalone-server tigervnc-common

# 데스크톱 환경 설치 (없는 경우)
sudo apt install -y ubuntu-desktop  # Ubuntu
# 또는
sudo apt install -y xfce4 xfce4-goodies  # XFCE (가벼움)

# VNC 비밀번호 설정
vncpasswd
# Password: ******** (입력)
# Verify: ******** (재입력)
# Would you like to enter a view-only password (y/n)? n
```

#### VNC 서버 시작 스크립트 생성

```bash
# ~/.vnc/xstartup 파일 생성
mkdir -p ~/.vnc
cat > ~/.vnc/xstartup << 'EOF'
#!/bin/bash
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
export XKL_XMODMAP_DISABLE=1

# XFCE 사용
startxfce4 &

# 또는 Ubuntu Desktop 사용
# gnome-session &

# 또는 KDE 사용
# startkde &
EOF

# 실행 권한 부여
chmod +x ~/.vnc/xstartup
```

#### VNC 서버 시작

```bash
# 디스플레이 :1 (포트 5901)로 시작
vncserver :1 -geometry 1920x1080 -depth 24

# 다른 해상도 옵션:
# vncserver :1 -geometry 1280x720 -depth 24   # 720p
# vncserver :1 -geometry 1366x768 -depth 24   # 태블릿 최적
# vncserver :1 -geometry 2560x1440 -depth 24  # 2K
```

#### 서버 상태 확인

```bash
# 실행 중인 VNC 서버 확인
vncserver -list

# 출력 예:
# TigerVNC server sessions:
# X DISPLAY #     RFB PORT #      PROCESS ID
# :1              5901            12345

# 서버 중지
vncserver -kill :1

# 서버 재시작
vncserver -kill :1
vncserver :1 -geometry 1920x1080 -depth 24
```

---

### 2. 방화벽 설정

```bash
# UFW 사용 시
sudo ufw allow 5901/tcp
sudo ufw reload

# firewalld 사용 시
sudo firewall-cmd --permanent --add-port=5901/tcp
sudo firewall-cmd --reload
```

---

### 3. 자동 시작 설정 (Optional)

#### systemd 서비스 생성

```bash
# 서비스 파일 생성
sudo nano /etc/systemd/system/vncserver@.service
```

```ini
[Unit]
Description=Remote desktop service (VNC)
After=syslog.target network.target

[Service]
Type=forking
User=YOUR_USERNAME
Group=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME

ExecStartPre=/bin/sh -c '/usr/bin/vncserver -kill :%i > /dev/null 2>&1 || :'
ExecStart=/usr/bin/vncserver :%i -geometry 1920x1080 -depth 24 -localhost no
ExecStop=/usr/bin/vncserver -kill :%i

[Install]
WantedBy=multi-user.target
```

**YOUR_USERNAME을 실제 사용자명으로 변경!**

```bash
# 서비스 활성화
sudo systemctl daemon-reload
sudo systemctl enable vncserver@1.service
sudo systemctl start vncserver@1.service

# 상태 확인
sudo systemctl status vncserver@1.service
```

---

### 4. 안드로이드 VNC 클라이언트 앱

#### 추천 앱

**1. RealVNC Viewer** (가장 추천)
- Play Store: https://play.google.com/store/apps/details?id=com.realvnc.viewer.android
- 특징: 무료, 안정적, 사용하기 쉬움

**2. VNC Viewer - Remote Desktop**
- Play Store에서 "vnc viewer" 검색
- 특징: 가벼움, 빠름

**3. bVNC: Secure VNC Viewer**
- 특징: SSH 터널링 지원

---

### 5. 안드로이드에서 연결하기

#### RealVNC Viewer 사용

```
1. 앱 설치 후 실행

2. "+" 버튼 클릭 → 새 연결 추가

3. 정보 입력:
   - Address: 192.168.0.100:5901
     (리눅스 서버 IP:포트)
   - Name: 내 리눅스 PC

4. 저장 후 연결 클릭

5. VNC 비밀번호 입력 (vncpasswd로 설정한 것)

6. 연결 완료!
```

#### 연결 주소 형식

```
로컬 네트워크:
192.168.0.100:5901

포트별 디스플레이 번호:
:1 = 포트 5901
:2 = 포트 5902
:3 = 포트 5903
```

---

## 🌐 인터넷을 통한 외부 접속

### Option 1: SSH 터널링 (가장 안전)

```bash
# 안드로이드에 Termux 설치
# Play Store → Termux

# Termux에서:
pkg install openssh
ssh -L 5901:localhost:5901 user@your-server-ip

# 그 다음 VNC Viewer에서:
# Address: localhost:5901
```

### Option 2: 포트 포워딩 (공유기 설정)

```
1. 공유기 관리자 페이지 접속 (보통 192.168.0.1)

2. 포트 포워딩 설정:
   - 외부 포트: 5901
   - 내부 IP: 192.168.0.100
   - 내부 포트: 5901
   - 프로토콜: TCP

3. 공인 IP 확인:
   https://www.whatismyip.com/

4. VNC Viewer에서:
   Address: YOUR_PUBLIC_IP:5901
```

**⚠️ 보안 주의**: 인터넷 노출 시 강력한 VNC 비밀번호 사용!

### Option 3: Tailscale (가장 쉬움, 추천)

```bash
# 리눅스에 Tailscale 설치
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# 안드로이드에 Tailscale 앱 설치
# Play Store → Tailscale

# 둘 다 같은 계정으로 로그인

# Tailscale IP 확인
tailscale ip -4
# 예: 100.101.102.103

# VNC Viewer에서:
# Address: 100.101.102.103:5901
```

---

## 🔧 문제 해결

### 1. "Connection refused" 오류

```bash
# VNC 서버가 실행 중인지 확인
vncserver -list

# 실행 중이 아니면 시작
vncserver :1 -geometry 1920x1080 -depth 24

# 방화벽 확인
sudo ufw status
sudo ufw allow 5901/tcp
```

### 2. 화면이 회색/검은색만 보임

```bash
# xstartup 파일 재설정
nano ~/.vnc/xstartup
```

```bash
#!/bin/bash
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
startxfce4 &
```

```bash
chmod +x ~/.vnc/xstartup

# VNC 재시작
vncserver -kill :1
vncserver :1 -geometry 1920x1080 -depth 24
```

### 3. 느린 연결 속도

```bash
# 낮은 해상도 사용
vncserver :1 -geometry 1280x720 -depth 24

# 또는 VNC Viewer 앱에서:
# 설정 → Picture Quality → Low
```

### 4. IP 주소 찾기

```bash
# 방법 1
hostname -I

# 방법 2
ip addr show

# 방법 3
ifconfig
```

---

## 📱 안드로이드 VNC 앱 설정 팁

### RealVNC Viewer 최적화

```
설정 → Picture Quality:
- High (빠른 네트워크)
- Medium (일반)
- Low (느린 네트워크, 모바일 데이터)

설정 → Input:
- Mouse Pointer: "Local" (더 부드러움)
- Keyboard: "Auto" 또는 "Virtual"

설정 → Expert:
- PreferredEncoding: "Tight" (압축률 높음)
```

---

## 🎯 사용 시나리오

### 1. 집 내부 (같은 WiFi)
```
리눅스 IP: 192.168.0.100
연결 주소: 192.168.0.100:5901
속도: 매우 빠름
보안: 안전 (내부망)
```

### 2. 외부 (인터넷)
```
방법: Tailscale (추천)
연결 주소: 100.x.x.x:5901
속도: 빠름
보안: 매우 안전 (암호화)
```

### 3. 모바일 데이터
```
방법: Tailscale + Low Quality
연결 주소: 100.x.x.x:5901
설정: Picture Quality → Low
데이터 사용량: ~10-30MB/시간
```

---

## 🔐 보안 강화

### 1. SSH 터널링 사용

```bash
# VNC 서버를 localhost만 허용
vncserver :1 -geometry 1920x1080 -depth 24 -localhost yes

# SSH 터널 생성 (Termux에서)
ssh -L 5901:localhost:5901 user@server-ip

# VNC Viewer에서
# Address: localhost:5901
```

### 2. 강력한 비밀번호

```bash
# 8자 이상, 복잡한 비밀번호
vncpasswd
```

### 3. 방화벽 제한

```bash
# 특정 IP만 허용
sudo ufw allow from 192.168.0.0/24 to any port 5901
```

---

## 📊 비교: VNC vs SSH vs RDP

| 기능 | VNC | SSH | RDP |
|------|-----|-----|-----|
| GUI | ✅ | ❌ | ✅ |
| 속도 | 중간 | 빠름 | 빠름 |
| 안드로이드 앱 | 많음 | Termux | 적음 |
| 리눅스 지원 | ✅ | ✅ | 제한적 |
| 추천 | ✅ GUI 필요 시 | CLI만 필요 시 | Windows 서버 |

---

## 🎓 추가 팁

### 해상도 변경

```bash
# 휴대폰 크기에 맞춤
vncserver :1 -geometry 1280x720 -depth 24

# 태블릿 크기
vncserver :1 -geometry 1920x1200 -depth 24
```

### 여러 세션 실행

```bash
# 디스플레이 :1 (포트 5901)
vncserver :1 -geometry 1920x1080 -depth 24

# 디스플레이 :2 (포트 5902)
vncserver :2 -geometry 1280x720 -depth 24

# 각각 다른 포트로 접속 가능
```

### 로그 확인

```bash
# VNC 로그
cat ~/.vnc/*.log

# 가장 최근 로그
tail -f ~/.vnc/*.log
```

---

## ✅ 체크리스트

### 리눅스 서버
- [ ] VNC 서버 설치 완료
- [ ] VNC 비밀번호 설정
- [ ] VNC 서버 실행 중
- [ ] 방화벽 포트 5901 오픈
- [ ] IP 주소 확인

### 안드로이드폰
- [ ] VNC Viewer 앱 설치
- [ ] 서버 주소 입력
- [ ] VNC 비밀번호 입력
- [ ] 연결 성공!

---

## 🆘 빠른 도움말

```bash
# VNC 서버 설치부터 시작까지 (복사 붙여넣기)
sudo apt update && sudo apt install -y tigervnc-standalone-server tigervnc-common xfce4
vncpasswd
echo '#!/bin/bash
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
startxfce4 &' > ~/.vnc/xstartup
chmod +x ~/.vnc/xstartup
vncserver :1 -geometry 1920x1080 -depth 24
sudo ufw allow 5901/tcp
hostname -I

# 이제 안드로이드에서 위에 나온 IP:5901로 접속!
```

---

**작성**: 2025-11-17
**테스트 환경**: Ubuntu 22.04 LTS + TigerVNC + Android 13
**추천 앱**: RealVNC Viewer
