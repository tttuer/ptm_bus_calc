# 버스 시간 계산기

정류장 사이 거리와 평균 속도로 구간별·전체 예상 시간을 계산하는 웹 앱입니다.

다른 컴퓨터에서 배포 작업을 이어갈 때는 [DEPLOYMENT_HANDOFF.md](DEPLOYMENT_HANDOFF.md)를 먼저 읽으세요.

## 실행 방법

1. `.env.example`을 `.env`로 복사합니다. 지도 사용 시 `VITE_KAKAO_MAP_KEY`에 JavaScript 키를 입력합니다.
2. MongoDB를 시작합니다: `docker compose up -d mongo`
3. 백엔드에서 `uv sync --extra dev` 후 `uv run uvicorn app.main:app --reload`을 실행합니다.
4. 프론트엔드에서 `pnpm install` 후 `pnpm dev`를 실행합니다.

프론트엔드: http://localhost:5173

API 문서: http://localhost:8000/docs

## k3s 배포

GitHub Actions는 `main` 브랜치에 푸시되면 이미지를 GitHub Container Registry(GHCR)에 올린 뒤 k3s에 배포합니다.

1. `ptm.baeksung.kr`의 DNS A 레코드를 k3s Ingress의 외부 IP로 연결합니다.
2. k3s에 Traefik과 cert-manager를 설치합니다. [k8s/cert-manager/clusterissuer.example.yaml](k8s/cert-manager/clusterissuer.example.yaml)의 이메일을 바꾼 뒤 적용합니다.
3. GitHub 저장소의 **Settings → Secrets and variables → Actions**에 다음 값을 추가합니다.

| Secret | 값 |
| --- | --- |
| `KAKAO_MAP_KEY` | 카카오 JavaScript 키 |
| `KUBECONFIG_B64` | 배포 권한이 있는 kubeconfig 파일을 Base64로 변환한 값 |
| `K8S_SECRETS_ENV` | `k8s/overlays/prod/secrets.env.example`를 실제 비밀번호로 채운 내용 |
| `GHCR_PULL_TOKEN` | `read:packages` 권한을 가진 GitHub Personal Access Token |

`K8S_SECRETS_ENV`의 MongoDB 비밀번호에 `@`, `:`, `/` 같은 문자가 있으면 URI 안에서는 URL 인코딩해야 합니다. GHCR 패키지가 비공개라면 k3s에서 읽을 수 있도록 GHCR 이미지 pull secret도 별도로 설정해야 합니다.

## 계산 규칙

`시간(초) = 거리(m) / (속도(km/h) × 1000 / 3600)`

첫 정류장의 거리는 0m이고, 이후 정류장의 거리는 바로 이전 정류장에서 오는 거리입니다. 지도 선은 위치를 확인하기 위한 참고용이며 시간 계산에는 입력한 거리를 사용합니다.
