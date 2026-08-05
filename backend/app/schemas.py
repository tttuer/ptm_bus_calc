from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

PositiveSpeed = Annotated[float, Field(gt=0, le=120)]
Distance = Annotated[float, Field(ge=0)]


class StopInput(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=80)]
    distance_from_previous_m: Distance = 0
    latitude: Annotated[float | None, Field(ge=-90, le=90)] = None
    longitude: Annotated[float | None, Field(ge=-180, le=180)] = None


class RouteInput(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=80)]
    average_speed_kmh: PositiveSpeed
    stops: list[StopInput] = Field(default_factory=list, max_length=300)


class StopResult(StopInput):
    segment_seconds: int
    cumulative_seconds: int


class RouteResult(RouteInput):
    id: str
    stops: list[StopResult]
    total_distance_m: float
    total_seconds: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


class EstimateResult(BaseModel):
    stops: list[StopResult]
    total_distance_m: float
    total_seconds: int


class DirectionRequest(BaseModel):
    origin_latitude: Annotated[float, Field(ge=-90, le=90)]
    origin_longitude: Annotated[float, Field(ge=-180, le=180)]
    destination_latitude: Annotated[float, Field(ge=-90, le=90)]
    destination_longitude: Annotated[float, Field(ge=-180, le=180)]


class DirectionResult(BaseModel):
    distance_m: int
