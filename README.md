# 🚌 버스 배차 시간표 자동 생성 프로그램 (Bus Schedule Auto-Generator)

시내버스 운행 환경의 다양한 변수(첫차/막차, 기/종점 소요시간, 최소 법정 휴게시간, 차량수)를 고려하여 하루 운행 스케줄을 자동으로 산출하고, 수동 조정 및 엑셀 다운로드가 가능한 웹 애플리케이션입니다.

## 🌟 주요 기능
1. **배차 자동 계산**: 인가 차량 대수, 첫차/막차, 편도 소요시간, 최소 휴게시간, 희망 배차 간격을 받아 차량별 하루 운행표를 만듭니다. 배차 간격을 `0`으로 두면 차량 수와 회차 시간으로 자동 계산합니다.
2. **차량별 Gantt 타임라인**: 차량별(1호차~N호차) 운행 블록과 휴식 블록을 시각적으로 나타냅니다.
3. **종합 시간표 편집**: 테이블 뷰에서 특정 회차의 출발/도착 시간을 수동으로 조정할 수 있으며, 수정 시 뒷순번 휴식 시간이 실시간 재계산됩니다.
4. **엑셀 내보내기**: 수동 편집을 반영한 최종 배차 시간표를 이쁘게 서식화된 Excel 문서로 즉시 다운로드할 수 있습니다.

---

## 🛠️ 기술 스택 및 디렉터리 구조
- **백엔드**: Python 3.10+ / FastAPI / pandas / openpyxl / uv (의존성 관리)
- **프론트엔드**: Vue 3 (Vite, Composition API) / Vanilla CSS (Modern Dark Glassmorphism)

```text
auto_bus_schedule/
├── backend/                  # 백엔드 (Python/FastAPI)
│   ├── app/
│   │   ├── api/router.py     # API 라우터 (배차 생성, 엑셀 내보내기)
│   │   ├── core/scheduler.py # 배차 계산 및 시뮬레이션 엔진
│   │   ├── models/schedule.py# Pydantic 데이터 모델
│   │   ├── services/excel.py # openpyxl 기반 스타일드 엑셀 제너레이터
│   │   └── main.py           # FastAPI 메인 진입점
│   ├── pyproject.toml        # uv 패키지 메타파일
│   └── requirements.txt      # 파이썬 의존성 목록
├── frontend/                 # 프론트엔드 (Vue 3/Vite)
│   ├── src/
│   │   ├── App.vue           # 메인 대시보드 컴포넌트
│   │   ├── style.css         # 글로벌 다크 모드/유틸리티 CSS
│   │   └── main.js           # Vue 엔트리포인트
│   ├── index.html
│   └── package.json
├── run.bat                   # 윈도우용 일괄 실행 스크립트 (더블클릭 가능)
└── README.md                 # 본 문서
```

---

## 🚀 실행 방법 (Local Setup)

### 1. 사전 요구사항
- **Python**: 3.10 이상 버전 설치 필요 (시스템 경로 등록 권장)
- **Node.js**: LTS 버전 설치 필요
- **uv**: Python 패키지 관리를 위한 `uv` 설치 권장 (`pip install uv`)

### 2. 수동 실행 환경 설정
의존성이 이미 셋업되어 있으므로 바로 실행할 수 있습니다.

#### 백엔드 (FastAPI) 실행
```bash
cd backend
# 1. 가상환경 생성 (uv 사용 시)
uv venv .venv
# 2. 의존성 설치
uv pip install -r requirements.txt
# 3. FastAPI 개발 서버 실행
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8001
```
- API Swagger 문서: http://localhost:8001/docs

#### 프론트엔드 (Vue 3) 실행
```bash
cd frontend
# 1. 의존성 패키지 설치
npm install
# 2. Vite 개발 서버 실행
npm run dev
```
- 웹 애플리케이션 주소: http://localhost:5173

---

## ⚡ 빠른 실행 (윈도우 전용)
프로젝트 루트 디렉터리에 있는 `run.bat` 파일을 더블클릭하시면 백엔드와 프론트엔드 개발 서버가 각각 별도의 터미널 창으로 자동 기동됩니다.
- 서버가 켜진 후 크롬 등의 웹 브라우저에서 **http://localhost:5173** 으로 접속하십시오.

---

## 📌 현재 기준과 배포 메모

- 이 저장소는 `auto_bus_schedule` 구조를 기준으로 정리했습니다. 기사 자동 배정은 아직 포함하지 않으며, 휴식시간에는 충전시간을 함께 포함하는 방식입니다.
- 결과는 차량별 회차표, 전체 운행 목록, 운행 타임라인으로 확인하고 엑셀로 내려받을 수 있습니다.
- 현재 프론트엔드 API 주소는 개발용 `http://localhost:8001/api`로 고정되어 있습니다. 웹 배포 전에는 `frontend/src/App.vue`의 `API_BASE`를 실제 백엔드 주소 또는 환경변수로 바꿔야 합니다.
