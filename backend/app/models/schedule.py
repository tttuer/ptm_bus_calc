from pydantic import BaseModel, Field
from typing import List, Optional

class ScheduleRequest(BaseModel):
    first_departure: str = Field(..., description="기점 첫차 출발 시간 (Format: HH:MM)", examples=["06:00"])
    last_departure: str = Field(..., description="기점 막차 출발 시간 (Format: HH:MM)", examples=["22:30"])
    one_way_time: int = Field(..., description="기점 -> 종점 소요 시간 (분)", ge=5)
    return_way_time: int = Field(..., description="종점 -> 기점 소요 시간 (분)", ge=5)
    min_rest_time: int = Field(..., description="회차 시 최소 보장 휴식 시간 (분)", ge=0)
    bus_count: int = Field(..., description="운행 차량 대수 (대)", ge=1)
    interval_minutes: Optional[int] = Field(default=0, description="사용자 지정 배차 간격 (분). 0 지정 시 자동 계산", ge=0)

class ScheduleEntry(BaseModel):
    bus_id: int = Field(..., description="차량 번호 (1호차, 2호차 등)")
    round_no: int = Field(..., description="해당 차량의 운행 회차 순번")
    direction: str = Field(..., description="운행 방향 (기점->종점: 'GO', 종점->기점: 'BACK')")
    departure_time: str = Field(..., description="출발 시각 (HH:MM)")
    arrival_time: str = Field(..., description="도착 시각 (HH:MM)")
    rest_time_after: int = Field(..., description="도착 후 부여되는 휴식 시간 (분)")

class ScheduleResponse(BaseModel):
    success: bool
    message: str
    interval_minutes: float = Field(..., description="계산된 평균 배차 간격 (분)")
    warnings: List[str] = Field(default_factory=list, description="배차 간격 좁음 또는 시간 겹침 관련 경고 목록")
    schedule: List[ScheduleEntry] = Field(default_factory=list)
