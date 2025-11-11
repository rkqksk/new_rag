# Kubernetes 개념 및 로컬 사용 가이드

**작성일**: 2025-11-11
**대상**: RAG Enterprise 프로젝트 팀
**목적**: Kubernetes 기본 개념 이해 및 로컬 개발 환경 옵션

---

## 📚 Kubernetes란?

### 한 줄 정의
**Kubernetes(K8s) = Docker 컨테이너들을 자동으로 관리해주는 컨테이너 오케스트레이션 플랫폼**

마치 "자율주행 시스템"처럼, 서버를 자동으로 운영해주는 시스템입니다.

---

## 🎯 비유로 이해하기

### Docker vs Kubernetes

**Docker = 선박 컨테이너** 📦
```
애플리케이션을 담은 상자
- API 컨테이너
- PostgreSQL 컨테이너
- Redis 컨테이너
```

**Kubernetes = 항구 관리 시스템** 🏗️
```
수천 개의 컨테이너를 자동으로 관리
- 어디에 배치할지 자동 결정
- 고장나면 자동으로 교체
- 트래픽 많으면 자동으로 증설
- 적으면 자동으로 축소
```

---

## 🔧 Kubernetes가 하는 일

### 1. 자동 배포 (Deployment)
```yaml
# "API 서버 3개 띄워줘"
replicas: 3
```
→ Kubernetes가 자동으로 3개 생성

### 2. 자동 복구 (Self-Healing)
```
API 서버 1개 죽음
→ Kubernetes: "감지! 새로운 서버 자동 생성"
→ 몇 초 내 복구 완료
```

### 3. 자동 스케일링 (Auto-Scaling)
```
RAG Enterprise HPA 설정:
- CPU 70% 넘으면: 서버 자동 증설 (최대 20개)
- CPU 낮으면: 서버 자동 축소 (최소 3개)
→ 사람이 신경 쓸 필요 없음!
```

### 4. 로드 밸런싱 (Load Balancing)
```
사용자 요청 → Kubernetes → 여러 서버에 자동 분산
```

### 5. 무중단 배포 (Rolling Update)
```
새 버전 배포 시:
1. 하나씩 순차적으로 교체
2. 서비스 중단 없음
3. 문제 생기면 자동 롤백
```

---

## 🆚 비교: Docker Compose vs Kubernetes

### Docker (기본)
```bash
docker run api
# 컨테이너 1개만 실행
```

**특징**:
- 가장 기본
- 단일 컨테이너 관리
- 수동 관리 필요

---

### Docker Compose (개발용)
```bash
docker-compose up -d
# 여러 컨테이너 동시 실행 (우리 프로젝트: 17개)
# 하지만 1개 서버에서만 동작
```

**특징**:
- ✅ 여러 컨테이너 한 번에 관리
- ✅ 설정 간단 (YAML 파일 하나)
- ✅ 로컬 개발에 완벽
- ❌ 1개 서버로 제한
- ❌ 자동 복구 없음
- ❌ 자동 스케일링 없음

**우리 프로젝트 docker-compose.yml**:
```yaml
services:
  postgres:      # PostgreSQL DB
  redis:         # Cache
  qdrant:        # Vector DB
  api:           # FastAPI
  clickhouse:    # Analytics DB
  kafka:         # Event streaming
  # ... 총 17개 서비스
```

---

### Kubernetes (프로덕션용)
```bash
kubectl apply -f k8s/
# 여러 서버에 컨테이너 분산 배포
# 자동 복구, 자동 스케일링
# 수천~수만 개 컨테이너 관리
```

**특징**:
- ✅ 여러 서버에 분산 배포
- ✅ 자동 복구 (Self-Healing)
- ✅ 자동 스케일링 (HPA)
- ✅ 무중단 배포
- ✅ 로드 밸런싱
- ❌ 설정 복잡
- ❌ 학습 곡선 높음

**우리 프로젝트 k8s/ 디렉토리**:
```
k8s/
├── api-deployment.yaml          # API 배포 설정
├── postgres-statefulset.yaml    # PostgreSQL StatefulSet
├── qdrant-statefulset.yaml      # Qdrant StatefulSet
├── redis-deployment.yaml        # Redis Deployment
├── hpa.yaml                     # Auto-scaling 설정 ⭐
├── ingress.yaml                 # 외부 접근 라우팅
├── configmap.yaml               # 설정 관리
├── secrets.yaml                 # 비밀 정보
├── namespace.yaml               # 네임스페이스
└── deployment.yaml              # 일반 배포 설정
```

---

## 🚀 실제 사용 예시: 트래픽 급증 시나리오

### Docker Compose (수동 대응)
```
상황: 트래픽 10배 증가!

1. 개발자: "아! CPU 100%다..."
2. 수동으로 docker-compose.yml 수정
   replicas: 3 → replicas: 10
3. docker-compose down
4. docker-compose up -d
5. 서비스 재시작 (5-10초 중단)
6. 트래픽 감소 시 다시 수동 조정 필요
```

**문제점**:
- 수동 대응 (사람이 직접 해야 함)
- 서비스 중단 발생
- 반응 속도 느림 (분 단위)

---

### Kubernetes (자동 대응)
```
상황: 트래픽 10배 증가!

1. Kubernetes: "CPU 70% 넘었네? HPA 작동!"
2. 자동으로 Pod 증설 시작
   3개 → 5개 → 8개 → 10개
3. 무중단 스케일링 (1-2초 내)
4. 트래픽 감소하면 자동으로 축소
   10개 → 8개 → 5개 → 3개
5. 사람이 신경 쓸 필요 없음
```

**장점**:
- 완전 자동화
- 서비스 중단 없음
- 실시간 반응 (초 단위)
- 비용 최적화 (필요한 만큼만 사용)

---

## 📊 우리 프로젝트의 Kubernetes 설정

### HPA (Horizontal Pod Autoscaler)
```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: rag-enterprise-api-hpa

spec:
  scaleTargetRef:
    kind: Deployment
    name: rag-enterprise-api

  # 스케일링 범위
  minReplicas: 3      # 최소 3개 (항상 유지)
  maxReplicas: 20     # 최대 20개 (피크 시)

  # 스케일링 기준
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        averageUtilization: 70    # CPU 70% 기준

  - type: Resource
    resource:
      name: memory
      target:
        averageUtilization: 80    # 메모리 80% 기준

  # 스케일링 속도
  behavior:
    scaleUp:
      policies:
      - type: Percent
        value: 100              # 최대 100% 증가 (2배)
      - type: Pods
        value: 4                # 또는 최대 4개 추가
      periodSeconds: 60         # 1분당

    scaleDown:
      policies:
      - type: Percent
        value: 50               # 최대 50% 감소
      - type: Pods
        value: 2                # 또는 최대 2개 제거
      periodSeconds: 300        # 5분당
```

**동작 방식**:
1. **평소** (트래픽 낮음)
   - Pod 3개 유지
   - CPU ~30-40%

2. **피크 시간** (트래픽 증가)
   - CPU 70% 초과 감지
   - 1분 안에 Pod 증설 (최대 +4개 또는 2배)
   - 3개 → 6개 → 10개 (순차 증설)

3. **트래픽 감소**
   - CPU 70% 미만으로 하락
   - 5분 관찰 후 축소 시작
   - 10개 → 8개 → 5개 → 3개 (순차 축소)

**비용 절감 예시**:
- 피크 시간 (2시간): 20 pods
- 평소 시간 (22시간): 3 pods
- 평균: (20×2 + 3×22) / 24 = 4.4 pods
- 항상 20개 유지 vs HPA: **78% 비용 절감**

---

## 🔑 Kubernetes 주요 개념

### 1. Pod (파드)
```
Pod = 가장 작은 배포 단위 (컨테이너 1개 이상)
예: API 서버 컨테이너 1개 = Pod 1개
```

**특징**:
- 고유 IP 주소
- 컨테이너들이 같은 Pod 내에서 localhost로 통신
- Ephemeral (일시적) - 언제든 재생성 가능

---

### 2. Deployment (배포)
```yaml
kind: Deployment
spec:
  replicas: 3    # "Pod 3개 유지해줘"
```

**역할**:
- 원하는 Pod 개수 유지
- 하나 죽으면 자동으로 새로 생성
- 무중단 업데이트 (Rolling Update)
- 롤백 기능

---

### 3. Service (서비스)
```yaml
kind: Service
spec:
  selector:
    app: api
  ports:
  - port: 80
    targetPort: 8000
```

**역할**:
- 여러 Pod의 진입점 (단일 엔드포인트)
- 로드 밸런싱
- 서비스 디스커버리 (이름으로 접근)

**예시**:
```
사용자 → Service (api:80) → 자동 분산
           ↓
    Pod1  Pod2  Pod3
```

---

### 4. StatefulSet (상태 유지)
```yaml
kind: StatefulSet
metadata:
  name: postgres
spec:
  replicas: 1
```

**용도**: 데이터베이스 같은 상태 유지 서비스
- 순서대로 생성/삭제
- 고정된 네트워크 ID
- Persistent Volume (데이터 유지)

**우리 프로젝트**:
- PostgreSQL: StatefulSet
- Qdrant: StatefulSet
- API: Deployment (stateless)
- Redis: Deployment (stateless)

---

### 5. Ingress (진입점)
```yaml
kind: Ingress
spec:
  rules:
  - host: example.com
    http:
      paths:
      - path: /api
        backend:
          service:
            name: api
      - path: /admin
        backend:
          service:
            name: admin
```

**역할**:
- 외부에서 클러스터로 접근하는 관문
- HTTP/HTTPS 라우팅
- SSL/TLS 종료
- 도메인 기반 라우팅

---

## 💻 로컬에서 Kubernetes 사용하기

### 중요: 로컬에서도 Kubernetes 사용 가능!

Docker Compose처럼, **로컬 개발 환경에서도 Kubernetes를 사용할 수 있습니다.**

---

### 옵션 1: Minikube (가장 인기) ⭐

**특징**:
- 가상 머신에서 단일 노드 K8s 클러스터 실행
- 학습 및 로컬 테스트에 완벽
- 프로덕션 환경과 거의 동일한 경험

**설치 및 사용**:
```bash
# 1. Minikube 설치 (Linux)
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# 2. 클러스터 시작
minikube start

# 3. 우리 프로젝트 배포
kubectl apply -f k8s/

# 4. 확인
kubectl get pods
kubectl get hpa
kubectl get services

# 5. 대시보드 (웹 UI)
minikube dashboard

# 6. 정리
minikube stop
minikube delete
```

**리소스 설정**:
```bash
# CPU와 메모리 할당 (우리 프로젝트 권장)
minikube start --cpus=4 --memory=8192
```

---

### 옵션 2: Kind (Kubernetes IN Docker) 🐳

**특징**:
- Docker 컨테이너 안에서 K8s 실행
- 가장 가벼움
- CI/CD 파이프라인 테스트에 이상적

**설치 및 사용**:
```bash
# 1. Kind 설치
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# 2. 클러스터 생성
kind create cluster --name rag-enterprise

# 3. 배포
kubectl apply -f k8s/

# 4. 확인
kubectl get pods

# 5. 정리
kind delete cluster --name rag-enterprise
```

**멀티 노드 클러스터**:
```yaml
# kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
```

```bash
kind create cluster --config kind-config.yaml
```

---

### 옵션 3: Docker Desktop (가장 간편) 🖥️

**특징**:
- Docker Desktop에 내장
- 클릭 한 번으로 활성화
- Windows/Mac 전용

**사용법**:
```
1. Docker Desktop 설정 열기
2. Kubernetes 탭
3. "Enable Kubernetes" ✅
4. Apply & Restart
5. 완료!
```

**확인**:
```bash
kubectl config current-context
# docker-desktop

kubectl get nodes
# NAME             STATUS   ROLES    AGE   VERSION
# docker-desktop   Ready    master   1m    v1.24.0
```

**우리 프로젝트 배포**:
```bash
kubectl apply -f k8s/
kubectl get pods -w
```

---

## 🆚 로컬 옵션 비교

| 항목 | Minikube | Kind | Docker Desktop |
|------|----------|------|----------------|
| **설치** | 별도 설치 | 별도 설치 | 내장 |
| **플랫폼** | Linux/Mac/Windows | Linux/Mac/Windows | Mac/Windows만 |
| **무게** | 중간 (VM) | 가벼움 (Container) | 중간 |
| **속도** | 중간 | 빠름 | 중간 |
| **멀티 노드** | ❌ | ✅ | ❌ |
| **대시보드** | ✅ (내장) | ❌ | ✅ (별도) |
| **권장 용도** | 학습, 개발 | CI/CD, 테스트 | 간편한 개발 |

**우리 프로젝트 추천**:
- **학습/테스트**: Minikube (대시보드 포함)
- **CI/CD**: Kind (가볍고 빠름)
- **Mac/Windows**: Docker Desktop (가장 간편)

---

## 📋 로컬 Kubernetes 실습 (단계별)

### Step 1: Minikube 시작
```bash
# 클러스터 시작 (4 CPU, 8GB RAM)
minikube start --cpus=4 --memory=8192

# 상태 확인
kubectl get nodes
# NAME       STATUS   ROLES           AGE   VERSION
# minikube   Ready    control-plane   30s   v1.28.3
```

---

### Step 2: 우리 프로젝트 배포
```bash
# 네임스페이스 생성
kubectl apply -f k8s/namespace.yaml

# ConfigMap & Secrets
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# 데이터베이스 (StatefulSets)
kubectl apply -f k8s/postgres-statefulset.yaml
kubectl apply -f k8s/qdrant-statefulset.yaml
kubectl apply -f k8s/redis-deployment.yaml

# API
kubectl apply -f k8s/api-deployment.yaml

# HPA (Auto-scaling)
kubectl apply -f k8s/hpa.yaml

# Ingress
kubectl apply -f k8s/ingress.yaml

# 또는 한 번에
kubectl apply -f k8s/
```

---

### Step 3: 확인 및 모니터링
```bash
# 모든 리소스 확인
kubectl get all

# Pod 상태 실시간 확인
kubectl get pods -w

# HPA 상태 확인
kubectl get hpa
# NAME                     REFERENCE             TARGETS   MINPODS   MAXPODS   REPLICAS
# rag-enterprise-api-hpa   Deployment/api        45%/70%   3         20        3

# 로그 확인
kubectl logs -f deployment/rag-enterprise-api

# Pod 상세 정보
kubectl describe pod <pod-name>
```

---

### Step 4: 서비스 접근
```bash
# 서비스 목록
kubectl get services

# 로컬에서 서비스 접근 (포트 포워딩)
kubectl port-forward service/rag-enterprise-api 8001:80

# 브라우저에서 접근
# http://localhost:8001
```

---

### Step 5: Auto-scaling 테스트
```bash
# 부하 생성 (별도 터미널)
kubectl run -i --tty load-generator --rm --image=busybox --restart=Never -- /bin/sh
# 컨테이너 안에서:
while true; do wget -q -O- http://rag-enterprise-api/api/v1/health; done

# HPA 모니터링 (원래 터미널)
kubectl get hpa -w
# TARGETS 컬럼이 70% 넘으면 자동으로 REPLICAS 증가

# Pod 증가 확인
kubectl get pods -w
# 3개 → 5개 → 8개 → 10개 (순차 증가)
```

---

### Step 6: 대시보드 (선택)
```bash
# Minikube 대시보드 실행
minikube dashboard

# 브라우저에서 자동으로 열림
# - Pods 목록
# - HPA 그래프
# - 리소스 사용량
# - 로그 등
```

---

### Step 7: 정리
```bash
# 배포 삭제
kubectl delete -f k8s/

# 또는 네임스페이스 전체 삭제
kubectl delete namespace rag-enterprise

# 클러스터 중지
minikube stop

# 클러스터 삭제 (필요 시)
minikube delete
```

---

## 🤔 언제 Kubernetes를 사용해야 할까?

### ✅ Kubernetes 사용 권장 상황

**1. 트래픽이 불규칙한 경우**
```
예: RAG 검색 서비스
- 주간: 높은 트래픽 (많은 사용자)
- 야간: 낮은 트래픽 (사용자 적음)
→ HPA로 자동 스케일링 (비용 절감)
```

**2. 무중단 서비스가 필수인 경우**
```
예: 프로덕션 API 서비스
- 배포 중에도 서비스 계속
- Rolling Update로 무중단 업데이트
- 문제 시 자동 롤백
```

**3. 여러 서버에서 실행해야 하는 경우**
```
예: 글로벌 서비스
- 서울 리전: 3 pods
- 도쿄 리전: 3 pods
- 미국 리전: 3 pods
→ K8s로 통합 관리
```

**4. 자동 복구가 필요한 경우**
```
서버 장애 시:
- 수동 대응: 5-30분 소요
- K8s 자동 복구: 10-30초 소요
→ SLA 99.9% 이상 필요 시 필수
```

---

### ❌ Kubernetes 불필요한 상황

**1. 작은 프로젝트**
```
예: 개인 블로그, 작은 API
- 사용자 < 1000명
- 서버 1대로 충분
→ Docker Compose로 충분
```

**2. 트래픽이 예측 가능한 경우**
```
예: 사내 도구, 관리자 페이지
- 항상 비슷한 트래픽
- 피크 없음
→ 고정된 리소스로 충분
```

**3. 개발 환경**
```
로컬 개발:
- 설정 간단함이 중요
- Docker Compose가 더 빠름
→ 단, K8s 학습 목적이면 사용 가능
```

**4. 학습 시간이 부족한 경우**
```
K8s 학습 곡선:
- 기본 개념: 1-2주
- 실전 활용: 1-2개월
- 프로덕션 운영: 3-6개월
→ 시간 부족하면 관리형 서비스 (EKS, GKE) 고려
```

---

## 🎯 우리 프로젝트 권장 사항

### 현재 상태
```
✅ k8s/ 설정 파일: 완비
✅ docker-compose.yml: 완비
✅ HPA 설정: 3-20 replicas
❌ K8s 클러스터: 없음
```

### 단계별 로드맵

**Phase 1: 로컬 개발 (현재)**
```bash
# Docker Compose 사용
docker-compose up -d

장점:
- 설정 간단
- 빠른 시작/재시작
- 로컬 디버깅 용이
```

**Phase 2: K8s 학습 (선택)**
```bash
# Minikube로 실험
minikube start
kubectl apply -f k8s/
kubectl get hpa -w

목적:
- Kubernetes 개념 학습
- HPA 동작 확인
- 프로덕션 준비
```

**Phase 3: 스테이징 환경 (프로덕션 전)**
```bash
# 클라우드 K8s 클러스터
# AWS EKS / GCP GKE / Azure AKS

목적:
- 프로덕션과 동일한 환경
- 부하 테스트
- 모니터링 구축
```

**Phase 4: 프로덕션 배포**
```bash
# 프로덕션 클러스터
kubectl apply -f k8s/

기능:
- Auto-scaling (3-20 replicas)
- 무중단 배포
- 자동 복구
- 로드 밸런싱
```

---

## 📚 추가 학습 리소스

### 공식 문서
- Kubernetes 공식 문서: https://kubernetes.io/docs/
- Minikube 문서: https://minikube.sigs.k8s.io/docs/
- Kind 문서: https://kind.sigs.k8s.io/

### 튜토리얼
- Kubernetes 기초: https://kubernetes.io/docs/tutorials/kubernetes-basics/
- 인터랙티브 튜토리얼: https://www.katacoda.com/courses/kubernetes

### 우리 프로젝트 관련 문서
- k8s/README.md: 빠른 시작 가이드
- docs/PHASE1_MCP_INSTALLATION.md: MCP 설치 (kubernetes-mcp 포함)
- .claude/mcp.json: kubernetes-mcp 설정

---

## ✅ 요약

### Kubernetes = Docker 컨테이너 자동 관리 시스템

**핵심 기능**:
1. 자동 배포
2. 자동 복구 (Self-Healing)
3. 자동 스케일링 (HPA)
4. 로드 밸런싱
5. 무중단 배포

**로컬 사용**:
- ✅ 가능! Minikube / Kind / Docker Desktop
- ✅ 학습 및 테스트에 완벽
- ✅ 프로덕션과 거의 동일한 환경

**우리 프로젝트**:
- ✅ k8s/ 설정 완비 (12개 파일)
- ✅ HPA 자동 스케일링 (3-20 replicas)
- ✅ 프로덕션 배포 준비 완료
- ⏳ 로컬 K8s 테스트 가능 (Minikube 권장)

**다음 단계**:
1. Docker Compose로 계속 개발
2. Minikube로 K8s 학습 (선택)
3. 프로덕션 배포 시 K8s 활용

---

**작성일**: 2025-11-11
**버전**: 1.0
**대상**: RAG Enterprise v7.0.0+
**관련 Commit**: 07dc1b1 (kubernetes-mcp 추가)
