# 포트 가이드

## 🔌 고정 포트

| 서비스 | 포트 | URL |
|--------|------|-----|
| **백엔드 API** | 8000 | http://localhost:8000 |
| **프론트엔드** | 8001 | http://localhost:8001/chat-demo-final.html |

---

## 🚀 실행 방법

### 방법 1: 전체 시스템 한 번에 시작 (권장)
```bash
./start_all.sh
```

**실행 내용**:
- 백엔드 서버 시작 (포트 8000)
- 프론트엔드 서버 시작 (포트 8001)
- 백그라운드로 실행됨

**접속**:
- 프론트엔드: http://localhost:8001/chat-demo-final.html
- API 문서: http://localhost:8000/docs

---

### 방법 2: 개별 실행

#### 백엔드만 실행
```bash
python3 run_chat_server.py
```
- 포트: 8000

#### 프론트엔드만 실행
```bash
./start_frontend.sh
```
- 포트: 8001

---

## 🛑 종료 방법

### 전체 종료
```bash
./stop_all.sh
```

### 개별 종료
```bash
# 백엔드 종료
pkill -f run_chat_server

# 프론트엔드 종료
lsof -ti:8001 | xargs kill -9
```

---

## 📊 상태 확인

### 실행 중인 프로세스 확인
```bash
# 백엔드
lsof -i:8000

# 프론트엔드
lsof -i:8001
```

### 로그 확인
```bash
# 백엔드 로그
tail -f logs/backend.log

# 프론트엔드 로그
tail -f logs/frontend.log
```

---

## 💡 빠른 접속

브라우저 북마크에 저장하세요:

- **채팅 UI**: http://localhost:8001/chat-demo-final.html
- **API 문서**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 🐛 문제 해결

### 포트가 이미 사용 중인 경우
```bash
# 포트 사용 중인 프로세스 확인
lsof -i:8000
lsof -i:8001

# 강제 종료
./stop_all.sh
```

### 프론트엔드가 백엔드에 연결 안 될 때
1. 백엔드가 실행 중인지 확인: `lsof -i:8000`
2. CORS 설정 확인 (이미 설정됨)
3. 브라우저 콘솔에서 에러 확인

---

**마지막 업데이트**: 2025-01-26
