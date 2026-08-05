# 작업 인수인계: 버스 시간 계산기

마지막 갱신: 2026-08-05

## 현재 상태

- GitHub 저장소: `https://github.com/tttuer/ptm_bus_calc.git`
- 기본 브랜치: `main`
- 마지막 커밋: 새 컴퓨터에서 `git log -1 --oneline`으로 확인
- 웹 주소 예정: `https://ptm.baeksung.kr`
- 구성: Vue 3 프론트엔드, FastAPI 백엔드, MongoDB, k3s, GitHub Actions, Docker Hub, SSH
- GitHub Actions 파일: `.github/workflows/deploy.yml`

## 이미 끝난 일

1. 노선·정류장·거리·평균 속도를 저장하고 시간을 계산하는 웹 앱을 만들었다.
2. 카카오 지도 표시와 장소 검색 기능을 추가했다.
3. Docker 이미지 파일을 만들었다.
   - `backend/Dockerfile`
   - `frontend/Dockerfile`
4. k3s 리소스를 만들었다.
   - MongoDB StatefulSet과 5Gi 저장공간
   - FastAPI Deployment와 Service
   - Vue/Nginx Deployment와 Service
   - `ptm.baeksung.kr` Ingress
5. `main`에 푸시하면 테스트, Docker Hub 이미지 생성, SSH를 통한 k3s 배포를 시도하는 GitHub Actions를 만들었다.

## 아직 해야 할 일

### 1. GitHub Secrets 등록

GitHub 저장소에서 **Settings → Secrets and variables → Actions**로 들어가 아래 4개를 추가한다.

| Secret | 넣을 값 |
| --- | --- |
| `KAKAO_MAP_KEY` | 카카오 Developers의 JavaScript 키 |
| `ENV_VARS` | 아래 MongoDB 및 카카오 REST API 환경변수 4줄 전체 |
| `DOCKER_USERNAME` | Docker Hub 사용자 이름 |
| `DOCKER_PASSWORD` | Docker Hub Access Token 또는 비밀번호 |
| `SSH_HOST` | k3s 서버 주소 또는 IP |
| `SSH_PORT` | SSH 포트(보통 `22`) |
| `SSH_USER` | k3s 서버 SSH 사용자 이름 |
| `SSH_PRIVATE_KEY` | SSH 개인 키 전체 내용 |

`ENV_VARS` 값 예시(실제 비밀번호로 바꿔서 한 줄씩 넣기):

```env
MONGO_INITDB_ROOT_USERNAME=bus_admin
MONGO_INITDB_ROOT_PASSWORD=긴_실제_비밀번호
MONGODB_URI=mongodb://bus_admin:긴_실제_비밀번호@mongo.ptm-bus.svc.cluster.local:27017/bus_time?authSource=admin
KAKAO_REST_API_KEY=카카오_REST_API_키
```

비밀번호에 `@`, `:`, `/`, `?` 등이 있다면 `MONGODB_URI` 안에서는 URL 인코딩해야 한다. 가장 쉬운 방법은 영문·숫자만 포함한 긴 비밀번호를 사용하는 것이다.

### 2. k3s와 DNS 준비

1. k3s에 기본 Traefik Ingress가 실행 중인지 확인한다.
2. `ptm.baeksung.kr` DNS A 레코드를 Traefik의 외부 IP로 연결한다.
3. cert-manager를 k3s에 설치한다. 이메일이 설정된 `k8s/cert-manager/clusterissuer.yaml`은 GitHub Actions가 자동 적용한다.

GitHub Actions는 SSH로 서버에 접속하고, 서버 안의 `kubectl`로 배포한다. 따라서 k3s 서버에는 다음이 필요하다.

- GitHub Actions에서 SSH 접속 가능
- `SSH_USER`가 `kubectl` 실행 권한 보유
- `kubectl`이 올바른 k3s 클러스터를 바라봄
- Docker Hub의 `ptm_bus_calc-api`, `ptm_bus_calc-web` 이미지를 내려받을 수 있음

Docker Hub 저장소는 공개(public)로 만드는 것이 가장 간단하다. 비공개(private)로 유지한다면 별도의 Docker Hub image pull secret을 Kubernetes에 추가해야 한다.

### 3. Actions 다시 실행

Secrets와 k3s 준비가 끝나면 GitHub의 **Actions → Build and deploy → Run workflow**를 실행한다.

성공하면 다음 순서로 진행된다.

```text
테스트 → Docker Hub 이미지 업로드 → SSH 접속 → k3s Secret 생성 → MongoDB/API/웹 배포 → HTTPS Ingress 연결
```

## 새 컴퓨터에서 작업하는 방법

```powershell
git clone https://github.com/tttuer/ptm_bus_calc.git
cd ptm_bus_calc
```

로컬 실행은 아래 순서다.

```powershell
docker compose up -d mongo
cd backend
uv run --extra dev uvicorn app.main:app --reload
```

새 터미널에서:

```powershell
cd ptm_bus_calc/frontend
pnpm install
pnpm dev
```

프로젝트 루트 `.env`에는 로컬 카카오 지도용 키를 둔다. 이 파일은 Git에 올라가지 않는다.

```env
VITE_KAKAO_MAP_KEY=카카오_JavaScript_키
```

## 확인 명령

```powershell
cd backend
uv run --extra dev pytest

cd ../frontend
pnpm build

cd ..
kubectl kustomize k8s/base
```

운영 오버레이 자체는 Secret 파일 없이도 검증할 수 있다. 배포 시에는 GitHub Actions가 `ENV_VARS`로 `k8s/bus-app-secrets.yaml`을 잠시 만들고 서버에 전달한다.

```powershell
kubectl kustomize k8s/overlays/prod
```

## 주의할 점

- `k8s/bus-app-secrets.yaml`과 루트 `.env`는 커밋하지 않는다.
- GitHub Actions의 `Production` Environment에 Secret을 등록한다.
- Docker Hub 이미지를 비공개로 만들면 Kubernetes image pull secret을 추가로 구성해야 한다.
- `storageClassName: local-path`은 일반 k3s 기본값이다. 클러스터에 다른 StorageClass만 있다면 `k8s/base/mongo.yaml`의 값을 바꾼다.
- cert-manager가 없으면 웹은 HTTP로 보일 수 있고 TLS 인증서는 발급되지 않는다.
