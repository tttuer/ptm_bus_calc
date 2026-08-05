# 작업 인수인계: 버스 시간 계산기

마지막 갱신: 2026-08-05

## 현재 상태

- GitHub 저장소: `https://github.com/tttuer/ptm_bus_calc.git`
- 기본 브랜치: `main`
- 마지막 커밋: `a5ed66e` (`Add bus time calculator with k3s deployment`)
- 웹 주소 예정: `https://ptm.baeksung.kr`
- 구성: Vue 3 프론트엔드, FastAPI 백엔드, MongoDB, k3s, GitHub Actions, GHCR
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
5. `main`에 푸시하면 테스트, GHCR 이미지 생성, k3s 배포를 시도하는 GitHub Actions를 만들었다.

## 아직 해야 할 일

### 1. GitHub Secrets 등록

GitHub 저장소에서 **Settings → Secrets and variables → Actions**로 들어가 아래 4개를 추가한다.

| Secret | 넣을 값 |
| --- | --- |
| `KAKAO_MAP_KEY` | 카카오 Developers의 JavaScript 키 |
| `KUBECONFIG_B64` | k3s 접속용 kubeconfig 파일을 Base64로 바꾼 값 |
| `K8S_SECRETS_ENV` | 아래 MongoDB 환경변수 3줄 전체 |
| `GHCR_PULL_TOKEN` | `read:packages` 권한을 가진 GitHub Personal Access Token |

`K8S_SECRETS_ENV` 값 예시(실제 비밀번호로 바꿔서 한 줄씩 넣기):

```env
MONGO_INITDB_ROOT_USERNAME=bus_admin
MONGO_INITDB_ROOT_PASSWORD=긴_실제_비밀번호
MONGODB_URI=mongodb://bus_admin:긴_실제_비밀번호@mongo.ptm-bus.svc.cluster.local:27017/bus_time?authSource=admin
```

비밀번호에 `@`, `:`, `/`, `?` 등이 있다면 `MONGODB_URI` 안에서는 URL 인코딩해야 한다. 가장 쉬운 방법은 영문·숫자만 포함한 긴 비밀번호를 사용하는 것이다.

PowerShell에서 kubeconfig를 Base64로 바꾸는 명령:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\path\to\kubeconfig.yaml"))
```

### 2. k3s와 DNS 준비

1. k3s에 기본 Traefik Ingress가 실행 중인지 확인한다.
2. `ptm.baeksung.kr` DNS A 레코드를 Traefik의 외부 IP로 연결한다.
3. cert-manager를 k3s에 설치한다.
4. `k8s/cert-manager/clusterissuer.example.yaml`의 `REPLACE_WITH_YOUR_EMAIL`을 실제 이메일로 바꿔 적용한다.

```powershell
kubectl apply -f k8s/cert-manager/clusterissuer.example.yaml
```

GitHub-hosted Actions가 k3s API 서버에 연결할 수 있어야 한다. k3s가 집이나 회사 내부망에만 있다면 GitHub-hosted runner는 접속할 수 없다. 이 경우 VPN을 연결하거나, k3s 네트워크 안에 self-hosted GitHub runner를 설치해야 한다.

### 3. Actions 다시 실행

Secrets와 k3s 준비가 끝나면 GitHub의 **Actions → Build and deploy → Run workflow**를 실행한다.

성공하면 다음 순서로 진행된다.

```text
테스트 → GHCR 이미지 업로드 → k3s Secret 생성 → MongoDB/API/웹 배포 → HTTPS Ingress 연결
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

운영 오버레이 검증에는 `k8s/overlays/prod/secrets.env`가 필요하다. 이 파일은 Git에 올리면 안 된다. 예시 파일을 복사해서 개인적으로만 사용한다.

```powershell
Copy-Item k8s/overlays/prod/secrets.env.example k8s/overlays/prod/secrets.env
kubectl kustomize k8s/overlays/prod
```

## 주의할 점

- `k8s/overlays/prod/secrets.env`와 루트 `.env`는 커밋하지 않는다.
- GHCR 패키지를 공개로 바꾸지 않는다면 `GHCR_PULL_TOKEN`은 필수다.
- `storageClassName: local-path`은 일반 k3s 기본값이다. 클러스터에 다른 StorageClass만 있다면 `k8s/base/mongo.yaml`의 값을 바꾼다.
- cert-manager가 없으면 웹은 HTTP로 보일 수 있고 TLS 인증서는 발급되지 않는다.
