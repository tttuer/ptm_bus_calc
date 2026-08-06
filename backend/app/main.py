from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import router as schedule_router

app = FastAPI(
    title="시내버스 배차 시간표 자동 생성 API",
    description="시내버스 배차 조건(첫차/막차, 소요시간, 휴식시간, 차량수)을 활용한 배차 자동 생성 및 엑셀 출력",
    version="1.0.0"
)

# CORS 설정 (Vue.js 프론트엔드 연동)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실 배포 시에는 구체적인 도메인 설정 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(schedule_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Bus Schedule Auto-Generator API is running."}
