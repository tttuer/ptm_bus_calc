from datetime import datetime
from typing import Annotated, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

TimeText = Annotated[str, Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")]
DistanceKm = Annotated[float, Field(gt=0, le=2_000)]
Speed = Annotated[float, Field(gt=0, le=120)]


class BusInput(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: Annotated[str, Field(min_length=1, max_length=40)]


class DriverInput(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: Annotated[str, Field(min_length=1, max_length=40)]
    work_start: TimeText
    work_end: TimeText


class GenerationSettings(BaseModel):
    first_departure: TimeText
    last_departure: TimeText
    outbound_minutes: Annotated[int, Field(ge=1, le=360)]
    inbound_minutes: Annotated[int, Field(ge=1, le=360)]
    min_rest_minutes: Annotated[int, Field(ge=0, le=360)] = 10
    bus_count: Annotated[int, Field(ge=1, le=100)] = 1
    interval_minutes: Annotated[int, Field(ge=0, le=360)] = 0


class RouteStopInput(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: Annotated[str, Field(min_length=1, max_length=80)]
    travel_weight: Annotated[float, Field(ge=0, le=100)] = 1
    dwell_minutes: Annotated[int, Field(ge=0, le=10)] = 1


class StopTime(BaseModel):
    stop_id: str
    stop_name: str
    arrival_time: TimeText
    departure_time: TimeText


class TripInput(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    direction: Literal["outbound", "inbound"] = "outbound"
    departure_time: TimeText
    arrival_time: TimeText
    distance_km: DistanceKm
    bus_id: str | None = None
    driver_id: str | None = None
    stop_times: list[StopTime] = Field(default_factory=list, max_length=200)


class ActivityInput(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    kind: Literal["rest", "charge"]
    start_time: TimeText
    bus_id: str
    driver_id: str | None = None
    duration_minutes: Annotated[int, Field(ge=0, le=1_440)] = 0
    to_charger_minutes: Annotated[int, Field(ge=0, le=360)] = 0
    to_charger_distance_km: Annotated[float, Field(ge=0, le=500)] = 0
    charge_minutes: Annotated[int, Field(ge=0, le=1_440)] = 0
    to_departure_minutes: Annotated[int, Field(ge=0, le=360)] = 0
    to_departure_distance_km: Annotated[float, Field(ge=0, le=500)] = 0

    @model_validator(mode="after")
    def validate_duration(self):
        if self.kind == "rest" and not self.duration_minutes:
            raise ValueError("휴게시간을 입력하세요.")
        if self.kind == "charge" and not self.charge_minutes:
            raise ValueError("충전시간을 입력하세요.")
        return self


class ScheduleInput(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=80)]
    origin: Annotated[str, Field(min_length=1, max_length=80)]
    destination: Annotated[str, Field(min_length=1, max_length=80)]
    max_average_speed_kmh: Speed = 60
    headway_minutes: Annotated[int, Field(ge=1, le=360)] = 30
    generation: GenerationSettings | None = None
    stops: list[RouteStopInput] = Field(default_factory=list, max_length=200)
    buses: list[BusInput] = Field(default_factory=list, max_length=100)
    drivers: list[DriverInput] = Field(default_factory=list, max_length=200)
    trips: list[TripInput] = Field(default_factory=list, max_length=1_000)
    activities: list[ActivityInput] = Field(default_factory=list, max_length=1_000)


class Issue(BaseModel):
    severity: Literal["warning", "error"]
    entity_id: str
    message: str


class TripResult(TripInput):
    duration_minutes: int
    required_average_speed_kmh: float


class ActivityResult(ActivityInput):
    end_time: str
    total_minutes: int


class ScheduleResult(ScheduleInput):
    id: str = ""
    trips: list[TripResult]
    activities: list[ActivityResult]
    issues: list[Issue]
    created_at: datetime | None = None
    updated_at: datetime | None = None


class GenerationResult(BaseModel):
    schedule: ScheduleInput | None = None
    required_bus_count: int
    actual_headway_minutes: list[int]
    message: str
