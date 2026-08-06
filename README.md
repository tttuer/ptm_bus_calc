# 버스 운행 시간표 편성기

여러 대의 버스와 기사의 하루 운행 시간을 입력하고, 가능한 시간표인지 확인하는 웹 앱입니다.

출발지와 도착지만 관리합니다. 중간 정류장 정보와 지도 기능은 사용하지 않습니다.

현재 구현 상태와 다음 작업은 [DEPLOYMENT_HANDOFF.md](DEPLOYMENT_HANDOFF.md)에 기록되어 있습니다.

## 할 수 있는 일

- 출발지·도착지, 운행 거리, 출발·도착시간 입력
- `거리 ÷ 운행시간`으로 필요한 평균속도 계산
- 버스와 기사 등록 및 운행편별 배정
- 배차 간격만큼 다음 출발편을 빠르게 추가
- 기사 휴게시간 등록
- 충전소 이동시간·거리, 충전시간, 출발지 이동시간·거리 등록
- 버스·기사 일정 겹침, 근무시간 밖 운행, 평균속도 초과 경고
- 자정을 넘는 운행시간 계산

## 실행 방법

1. MongoDB를 실행합니다.

   ```powershell
   docker compose up -d mongo
   ```

2. 백엔드를 실행합니다.

   ```powershell
   cd backend
   uv run --extra dev uvicorn app.main:app --reload
   ```

3. 새 터미널에서 프론트엔드를 실행합니다.

   ```powershell
   cd frontend
   pnpm install
   pnpm dev
   ```

웹 주소는 `http://localhost:5173`이고, API 문서는 `http://localhost:8000/docs`입니다.

## 확인 방법

```powershell
uv run --project backend --extra dev pytest backend/tests -q

cd frontend
pnpm build
```

## 데이터가 저장되는 곳

새 시간표는 MongoDB의 `schedules` 컬렉션에 저장됩니다. 이전 버전의 `routes` 데이터는 건드리지 않으므로 기존 데이터가 덮어써지지 않습니다.

## 주요 계산 규칙

```text
운행시간 = 도착시간 - 출발시간
필요 평균속도 = 운행거리(km) ÷ 운행시간(시간)
```

예를 들어 30km를 45분 안에 가려면 필요한 평균속도는 40km/h입니다.
