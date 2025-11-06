# 자체 서버 배포 가이드 (Self-Hosted Deployment)

**비용**: 도메인 비용만 (~$10-15/년)
**난이도**: ⭐⭐ (중급)
**소요 시간**: 1-2시간

---

## 📋 목차

1. [사전 요구사항](#사전-요구사항)
2. [서버 준비](#서버-준비)
3. [Docker 설치](#docker-설치)
4. [프로젝트 배포](#프로젝트-배포)
5. [도메인 연결](#도메인-연결)
6. [SSL 인증서 설정](#ssl-인증서-설정)
7. [보안 설정](#보안-설정)
8. [모니터링 설정](#모니터링-설정)
9. [백업 설정](#백업-설정)
10. [문제 해결](#문제-해결)

---

## 사전 요구사항

### 하드웨어 요구사항

**최소 사양** (개발/테스트):
- CPU: 2 코어
- RAM: 4GB
- 디스크: 50GB
- 네트워크: 인터넷 연결

**권장 사양** (프로덕션):
- CPU: 4 코어 이상
- RAM: 8GB 이상
- 디스크: 100GB 이상 (SSD 권장)
- 네트워크: 고정 IP 또는 DDNS

**예상 사용량**:
- Qdrant (벡터 DB): ~2GB RAM, ~10GB 디스크
- PostgreSQL: ~512MB RAM, ~5GB 디스크
- Redis: ~256MB RAM
- API 서버: ~1GB RAM
- Ollama (LLM): ~4GB RAM (선택)

### 소프트웨어 요구사항

- **OS**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+ (Linux 권장)
- **도메인**: 구매한 도메인 (예: example.com)
- **포트**: 80, 443 오픈 필요

### 도메인 구매

**추천 도메인 등록 업체**:
- [Namecheap](https://www.namecheap.com/) - $10-12/년
- [가비아](https://www.gabia.com/) - ₩11,000/년 (한국)
- [Cloudflare](https://www.cloudflare.com/) - $10/년 + 무료 DNS

---

## 서버 준비

### 1. Ubuntu 서버 설치 (이미 있으면 생략)

```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 필수 패키지 설치
sudo apt install -y curl wget git vim ufw
```

### 2. 방화벽 설정

```bash
# UFW 방화벽 설정
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# 확인
sudo ufw status
```

### 3. 사용자 설정 (선택)

```bash
# 전용 사용자 생성 (보안 강화)
sudo adduser rag-app
sudo usermod -aG sudo rag-app
sudo usermod -aG docker rag-app

# 사용자 전환
su - rag-app
```

---

## Docker 설치

### Ubuntu/Debian

```bash
# 기존 Docker 제거 (있다면)
sudo apt remove docker docker-engine docker.io containerd runc

# Docker 공식 GPG 키 추가
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Docker 저장소 추가
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Docker 설치
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER

# 재로그인 필요 (또는 새 세션 시작)
newgrp docker

# 설치 확인
docker --version
docker compose version
```

### CentOS/RHEL

```bash
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

---

## 프로젝트 배포

### 1. 코드 Clone

```bash
# 홈 디렉토리로 이동
cd ~

# 프로젝트 clone
git clone https://github.com/YOUR_USERNAME/rag-enterprise.git
cd rag-enterprise

# 또는 특정 브랜치
git clone -b main https://github.com/YOUR_USERNAME/rag-enterprise.git
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# 환경 변수 수정
vim .env
```

**프로덕션 환경 변수** (`.env`):
```bash
# API 설정
API_HOST=0.0.0.0
API_PORT=8001
API_WORKERS=4
DEBUG_ENABLED=false

# 데이터베이스
QDRANT_HOST=qdrant
QDRANT_PORT=6333
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=rag_enterprise
POSTGRES_USER=rag_user
POSTGRES_PASSWORD=CHANGE_THIS_STRONG_PASSWORD_123!

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# 임베딩 모델
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIM=384

# 보안 (선택)
ALLOWED_ORIGINS=https://your-domain.com
CORS_ENABLED=true

# 로깅
LOG_LEVEL=INFO
```

**⚠️ 중요**: `POSTGRES_PASSWORD`를 강력한 비밀번호로 변경하세요!

### 3. Docker Compose 실행

```bash
# 프로덕션 모드로 실행
docker compose up -d

# 또는 최적화 스크립트 사용
./scripts/deploy-optimized.sh production

# 컨테이너 상태 확인
docker compose ps

# 로그 확인
docker compose logs -f api
```

**예상 출력**:
```
NAME                COMMAND                  SERVICE    STATUS
rag-api-1           "uvicorn app.main:ap…"   api        Up
rag-postgres-1      "docker-entrypoint.s…"   postgres   Up
rag-qdrant-1        "./qdrant"               qdrant     Up
rag-redis-1         "docker-entrypoint.s…"   redis      Up
```

### 4. 초기 데이터 로드 (선택)

```bash
# 제품 데이터 임베딩 생성
docker compose exec api python scripts/embed_all_products.py

# 또는 로컬에서
python scripts/embed_all_products.py
```

### 5. 헬스 체크

```bash
# API 헬스 체크
curl http://localhost:8001/health/ready

# 응답 예시:
# {"status":"healthy","qdrant":"connected","postgres":"connected"}
```

---

## 도메인 연결

### 1. DNS 설정

도메인 등록 업체 (Namecheap, 가비아 등)에서 DNS 레코드 추가:

**A 레코드 추가**:
```
Type: A
Name: @
Value: YOUR_SERVER_IP
TTL: 3600
```

**www 서브도메인 추가** (선택):
```
Type: A
Name: www
Value: YOUR_SERVER_IP
TTL: 3600
```

**서버 IP 확인**:
```bash
# 외부 IP 확인
curl ifconfig.me
```

**DNS 전파 확인** (5분~48시간 소요):
```bash
# Linux/Mac
dig your-domain.com

# 또는
nslookup your-domain.com
```

### 2. Nginx 설치 (리버스 프록시)

```bash
# Nginx 설치
sudo apt install -y nginx

# Nginx 시작
sudo systemctl start nginx
sudo systemctl enable nginx

# 상태 확인
sudo systemctl status nginx
```

### 3. Nginx 설정 (HTTP - 임시)

```bash
# 설정 파일 생성
sudo vim /etc/nginx/sites-available/rag-enterprise
```

**Nginx 설정** (`/etc/nginx/sites-available/rag-enterprise`):
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # 로그
    access_log /var/log/nginx/rag-enterprise-access.log;
    error_log /var/log/nginx/rag-enterprise-error.log;

    # API 프록시
    location / {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # 타임아웃 설정
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # SSE (Server-Sent Events) 지원
    location /api/v1/stream/ {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_set_header Cache-Control 'no-cache';
        proxy_set_header X-Accel-Buffering 'no';
        chunked_transfer_encoding on;
        proxy_buffering off;
    }

    # 정적 파일 (프론트엔드)
    location /static/ {
        alias /home/rag-app/rag-enterprise/frontend/;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }

    # 최대 업로드 크기
    client_max_body_size 100M;
}
```

**⚠️ `your-domain.com`을 실제 도메인으로 변경하세요!**

```bash
# 심볼릭 링크 생성
sudo ln -s /etc/nginx/sites-available/rag-enterprise /etc/nginx/sites-enabled/

# 기본 설정 제거 (선택)
sudo rm /etc/nginx/sites-enabled/default

# 설정 테스트
sudo nginx -t

# Nginx 재시작
sudo systemctl reload nginx
```

### 4. 도메인 접속 테스트

브라우저에서 접속:
```
http://your-domain.com/health/ready
```

정상 응답:
```json
{"status":"healthy","qdrant":"connected","postgres":"connected"}
```

---

## SSL 인증서 설정

### Let's Encrypt (무료 SSL)

**1. Certbot 설치**:
```bash
# Certbot 설치
sudo apt install -y certbot python3-certbot-nginx
```

**2. SSL 인증서 발급**:
```bash
# 자동 설정 (Nginx 설정 자동 수정)
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 또는 수동 설정
sudo certbot certonly --nginx -d your-domain.com -d www.your-domain.com
```

**프롬프트 응답**:
```
Email: your-email@example.com
Agree to ToS: Y
Share email: N (선택)
```

**3. 자동 갱신 설정**:
```bash
# 자동 갱신 테스트
sudo certbot renew --dry-run

# Cron job 확인 (자동 설치됨)
sudo systemctl status certbot.timer
```

**4. Nginx 설정 확인**:

Certbot이 자동으로 설정을 수정합니다:
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL 설정 (Certbot이 자동 추가)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # ... (기존 location 블록들)
}

# HTTP → HTTPS 리디렉션
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

**5. Nginx 재시작**:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

**6. HTTPS 접속 테스트**:
```
https://your-domain.com/health/ready
```

🎉 이제 HTTPS로 안전하게 접속 가능합니다!

---

## 보안 설정

### 1. 방화벽 강화

```bash
# 현재 설정 확인
sudo ufw status verbose

# 필요한 포트만 오픈
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 2. Fail2Ban (브루트포스 방지)

```bash
# Fail2Ban 설치
sudo apt install -y fail2ban

# 설정 파일 생성
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo vim /etc/fail2ban/jail.local
```

**Fail2Ban 설정**:
```ini
[sshd]
enabled = true
port = 22
maxretry = 3
bantime = 3600

[nginx-http-auth]
enabled = true
```

```bash
# Fail2Ban 시작
sudo systemctl start fail2ban
sudo systemctl enable fail2ban

# 상태 확인
sudo fail2ban-client status
```

### 3. Docker 보안

```bash
# Docker 데몬 보안 설정
sudo vim /etc/docker/daemon.json
```

**Docker 데몬 설정**:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "live-restore": true,
  "userland-proxy": false
}
```

```bash
# Docker 재시작
sudo systemctl restart docker
```

### 4. 비밀번호 변경

```bash
# PostgreSQL 비밀번호 변경
docker compose exec postgres psql -U rag_user -d rag_enterprise

# PostgreSQL 프롬프트에서:
ALTER USER rag_user WITH PASSWORD 'new_strong_password';
\q

# .env 파일도 업데이트
vim .env
# POSTGRES_PASSWORD=new_strong_password

# 재시작
docker compose restart
```

---

## 모니터링 설정

### 1. 로그 모니터링

```bash
# API 로그 실시간 확인
docker compose logs -f api

# 최근 100줄
docker compose logs --tail 100 api

# 모든 서비스 로그
docker compose logs -f
```

### 2. 리소스 모니터링

```bash
# Docker 컨테이너 리소스 사용량
docker stats

# 시스템 리소스
htop  # 또는 top
```

### 3. 디스크 사용량

```bash
# 전체 디스크 사용량
df -h

# Docker 디스크 사용량
docker system df

# 사용하지 않는 이미지/컨테이너 정리
docker system prune -a
```

### 4. 헬스 체크 스크립트

```bash
# 헬스 체크 스크립트 생성
vim ~/health-check.sh
```

**헬스 체크 스크립트** (`~/health-check.sh`):
```bash
#!/bin/bash

URL="https://your-domain.com/health/ready"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $URL)

if [ $RESPONSE -eq 200 ]; then
    echo "✅ System is healthy"
else
    echo "❌ System is down (HTTP $RESPONSE)"
    # 알림 보내기 (선택)
    # curl -X POST https://your-webhook-url ...
fi
```

```bash
# 실행 권한 부여
chmod +x ~/health-check.sh

# Cron job 등록 (5분마다 체크)
crontab -e

# 다음 라인 추가:
*/5 * * * * /home/rag-app/health-check.sh >> /home/rag-app/health-check.log 2>&1
```

---

## 백업 설정

### 1. 데이터베이스 백업

```bash
# 백업 스크립트 생성
vim ~/backup-db.sh
```

**백업 스크립트** (`~/backup-db.sh`):
```bash
#!/bin/bash

BACKUP_DIR="/home/rag-app/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# PostgreSQL 백업
docker compose exec -T postgres pg_dump -U rag_user rag_enterprise > \
  $BACKUP_DIR/postgres_$DATE.sql

# Qdrant 백업 (스냅샷)
curl -X POST "http://localhost:6333/collections/products_multimodal/snapshots"

# 7일 이상된 백업 삭제
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete

echo "✅ Backup completed: $DATE"
```

```bash
# 실행 권한
chmod +x ~/backup-db.sh

# 매일 새벽 2시 백업
crontab -e

# 다음 라인 추가:
0 2 * * * /home/rag-app/backup-db.sh >> /home/rag-app/backup.log 2>&1
```

### 2. 수동 백업

```bash
# PostgreSQL 백업
docker compose exec postgres pg_dump -U rag_user rag_enterprise > backup.sql

# 복원
docker compose exec -T postgres psql -U rag_user rag_enterprise < backup.sql

# Qdrant 백업
docker compose exec qdrant tar -czf /qdrant/backup.tar.gz /qdrant/storage

# Qdrant 백업 다운로드
docker cp rag-qdrant-1:/qdrant/backup.tar.gz ./qdrant-backup.tar.gz
```

---

## 업데이트 및 유지보수

### 1. 코드 업데이트

```bash
cd ~/rag-enterprise

# 변경사항 확인
git fetch
git status

# 최신 코드로 업데이트
git pull origin main

# 컨테이너 재시작
docker compose down
docker compose up -d

# 로그 확인
docker compose logs -f api
```

### 2. Docker 이미지 업데이트

```bash
# 이미지 업데이트
docker compose pull

# 재시작
docker compose up -d
```

### 3. 시스템 업데이트

```bash
# 시스템 패키지 업데이트
sudo apt update && sudo apt upgrade -y

# 재부팅 필요 여부 확인
ls /var/run/reboot-required

# 재부팅 (필요시)
sudo reboot
```

---

## 문제 해결

### 컨테이너가 시작되지 않을 때

```bash
# 로그 확인
docker compose logs api
docker compose logs postgres
docker compose logs qdrant

# 컨테이너 재시작
docker compose restart

# 완전 재시작
docker compose down
docker compose up -d
```

### 포트 충돌

```bash
# 포트 사용 중인 프로세스 확인
sudo lsof -i :8001
sudo lsof -i :5432

# 프로세스 종료
sudo kill -9 <PID>
```

### 디스크 공간 부족

```bash
# Docker 정리
docker system prune -a --volumes

# 로그 파일 정리
sudo journalctl --vacuum-time=7d

# 오래된 백업 삭제
find ~/backups -mtime +30 -delete
```

### SSL 인증서 문제

```bash
# 인증서 갱신
sudo certbot renew --force-renewal

# Nginx 재시작
sudo systemctl reload nginx

# 인증서 확인
sudo certbot certificates
```

### 성능 문제

```bash
# 리소스 확인
docker stats
htop

# Qdrant 인덱스 최적화
curl -X POST "http://localhost:6333/collections/products_multimodal/indexes"

# Redis 캐시 클리어
docker compose exec redis redis-cli FLUSHALL
```

---

## 성능 최적화

### 1. Nginx 캐싱

```nginx
# Nginx 설정에 추가
http {
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g inactive=60m;

    server {
        location /api/ {
            proxy_cache api_cache;
            proxy_cache_valid 200 10m;
            proxy_cache_key "$scheme$request_method$host$request_uri";
            add_header X-Cache-Status $upstream_cache_status;

            proxy_pass http://localhost:8001;
        }
    }
}
```

### 2. Docker 리소스 제한

`docker-compose.yml`에 추가:
```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### 3. PostgreSQL 튜닝

```sql
-- 연결 수 최적화
ALTER SYSTEM SET max_connections = 100;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';

-- 재시작
docker compose restart postgres
```

---

## 체크리스트

### 배포 완료 체크리스트

- [ ] Docker 설치 완료
- [ ] 프로젝트 clone 및 환경 변수 설정
- [ ] Docker Compose 실행 및 헬스 체크 통과
- [ ] 도메인 DNS 설정 완료
- [ ] Nginx 설치 및 리버스 프록시 설정
- [ ] SSL 인증서 발급 (Let's Encrypt)
- [ ] HTTPS 접속 확인
- [ ] 방화벽 설정 (UFW)
- [ ] Fail2Ban 설치
- [ ] 백업 스크립트 설정
- [ ] 모니터링 설정
- [ ] 헬스 체크 Cron job 등록

### 보안 체크리스트

- [ ] 강력한 비밀번호 설정
- [ ] SSH 키 인증 사용 (비밀번호 로그인 비활성화)
- [ ] 방화벽 활성화 (필요한 포트만 오픈)
- [ ] Fail2Ban 설치
- [ ] 정기 업데이트 설정
- [ ] 백업 자동화
- [ ] 로그 모니터링

---

## 비용 총정리

| 항목 | 비용 |
|------|------|
| 도메인 (.com) | $10-15/년 |
| SSL 인증서 | 무료 (Let's Encrypt) |
| 서버 | 무료 (자체 서버) |
| 소프트웨어 | 무료 (오픈소스) |
| **총 비용** | **$10-15/년** |

---

## 다음 단계

배포가 완료되었다면:

1. **데이터 로드**: 제품 데이터를 임베딩하여 Qdrant에 업로드
2. **프론트엔드 테스트**: `https://your-domain.com/chat.html` 접속
3. **API 테스트**: `/api/v1/docs` 에서 Swagger UI 확인
4. **모니터링 확인**: 헬스 체크 및 로그 모니터링
5. **백업 테스트**: 백업 스크립트 실행 및 복원 테스트

---

## 지원

문제가 발생하면:
1. 로그 확인: `docker compose logs -f`
2. 헬스 체크: `curl https://your-domain.com/health/ready`
3. GitHub Issues: 문제 보고
4. 문서 참조: `docs/DEPLOYMENT_GUIDE.md`

**배포 성공을 축하합니다! 🎉**
