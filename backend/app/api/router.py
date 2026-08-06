from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List
import io

from app.models.schedule import ScheduleRequest, ScheduleResponse, ScheduleEntry
from app.core.scheduler import calculate_schedule
from app.services.excel_generator import generate_schedule_excel

router = APIRouter(prefix="/schedule", tags=["Schedule"])

@router.post("/generate", response_model=ScheduleResponse)
def generate_schedule_endpoint(request: ScheduleRequest):
    """배차 파라미터를 입력받아 배차 시간표를 자동 계산하여 반환"""
    response = calculate_schedule(request)
    if not response.success:
        raise HTTPException(status_code=400, detail=response.message)
    return response

@router.post("/export-excel")
def export_excel_endpoint(entries: List[ScheduleEntry]):
    """배차 일정 리스트(수동 수정본 포함)를 전달받아 엑셀 파일 다운로드 스트림 반환"""
    if not entries:
        raise HTTPException(status_code=400, detail="내보낼 배차 데이터가 존재하지 않습니다.")

    try:
        excel_data = generate_schedule_excel(entries)

        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=bus_schedule.xlsx"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"엑셀 파일 생성 중 오류 발생: {str(e)}")
