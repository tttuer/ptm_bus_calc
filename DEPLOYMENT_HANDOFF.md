# 작업 인수인계: 시내버스 배차 시간표

마지막 갱신: 2026-08-06

## 현재 목표

입력한 인가 차량 대수 안에서, 첫차·막차·양방향 운행시간·최소 휴식시간·배차 간격을 이용해 차량별 하루 운행표를 만듭니다. 기사 자동 배정은 다음 단계이며, 충전시간은 현재 종점 휴식시간에 포함합니다.

## 현재 동작

1. 희망 배차 간격을 입력하면 그 간격으로 기점 출발 슬롯을 만듭니다.
2. 각 차량은 기점→종점 운행, 종점 휴식, 종점→기점 운행, 기점 휴식 순서로 돌아갑니다.
3. 차량이 아직 돌아오지 않았으면 가능한 시각까지 출발을 미룹니다.
4. 결과는 차량별 회차표, 전체 목록, Gantt 타임라인으로 보여주고 엑셀로 내려받을 수 있습니다.
5. 배차 간격을 `0`으로 두면 회차시간과 인가 대수로 자동 계산합니다.

## 실행과 확인

```powershell
cd backend
uv run python -m uvicorn app.main:app --reload --port 8000
```

새 터미널에서:

```powershell
cd frontend
npm install
npm run dev
```

검증 명령:

```powershell
uv run --project backend python -c "from app.core.scheduler import calculate_schedule"

cd frontend
npm run build
```

## 배포 전 확인할 점

- 로컬에서는 Vite 프록시가 `/api`를 `http://localhost:8000`으로 전달합니다. 별도 도메인 배포 시 `frontend/.env`의 `VITE_API_BASE_URL`에 실제 백엔드 API 주소를 설정합니다.
- FastAPI CORS는 현재 모든 출처를 허용합니다. 운영 환경에서는 프론트엔드 도메인만 허용하도록 좁힙니다.
- 이 버전에는 기사 자동 배정, 충전기 자리 검사, 배터리 잔량 계산이 없습니다.
