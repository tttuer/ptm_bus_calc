from math import ceil

from app.schemas import ActivityInput, BusInput, GenerationResult, ScheduleInput, TripInput
from app.services.calculator import to_minutes


def clock_text(minutes: int) -> str:
    minute = minutes % 1_440
    return f"{minute // 60:02}:{minute % 60:02}"


def generate(schedule: ScheduleInput) -> GenerationResult:
    settings = schedule.generation
    if not settings: raise ValueError("배차 기본 조건을 입력하세요.")
    first, last = to_minutes(settings.first_departure), to_minutes(settings.last_departure)
    if last < first: last += 1_440
    cycle = settings.outbound_minutes + settings.inbound_minutes + settings.min_rest_minutes * 2
    interval = settings.interval_minutes or ceil(cycle / settings.bus_count)
    buses = [BusInput(name=f"{index + 1}호차") for index in range(settings.bus_count)]
    vehicles = [{"available": first, "arrival": None, "round": 0} for _ in buses]
    trips, activities, departures = [], [], []
    slot, vehicle_index = first, 0
    while slot <= last:
        vehicle = vehicles[vehicle_index]
        departure = max(slot, vehicle["available"])
        if vehicle["arrival"] is not None and departure > vehicle["arrival"]:
            activities.append(ActivityInput(id=f"rest-origin-{len(activities)}", kind="rest", start_time=clock_text(vehicle["arrival"]), bus_id=buses[vehicle_index].id, duration_minutes=departure - vehicle["arrival"]))
        vehicle["round"] += 1
        round_no = vehicle["round"]
        outbound_arrival = departure + settings.outbound_minutes
        inbound_departure = outbound_arrival + settings.min_rest_minutes
        inbound_arrival = inbound_departure + settings.inbound_minutes
        trips.extend((
            TripInput(id=f"{vehicle_index}-{round_no}-out", direction="outbound", departure_time=clock_text(departure), arrival_time=clock_text(outbound_arrival), distance_km=1, bus_id=buses[vehicle_index].id),
            TripInput(id=f"{vehicle_index}-{round_no}-in", direction="inbound", departure_time=clock_text(inbound_departure), arrival_time=clock_text(inbound_arrival), distance_km=1, bus_id=buses[vehicle_index].id),
        ))
        activities.append(ActivityInput(id=f"rest-destination-{len(activities)}", kind="rest", start_time=clock_text(outbound_arrival), bus_id=buses[vehicle_index].id, duration_minutes=settings.min_rest_minutes))
        vehicle.update(available=inbound_arrival + settings.min_rest_minutes, arrival=inbound_arrival)
        departures.append(departure)
        slot = departure + interval
        vehicle_index = (vehicle_index + 1) % settings.bus_count
    headways = [later - earlier for earlier, later in zip(departures, departures[1:])]
    result = schedule.model_copy(update={"headway_minutes": interval, "buses": buses, "drivers": [], "trips": trips, "activities": activities})
    return GenerationResult(schedule=result, required_bus_count=settings.bus_count, actual_headway_minutes=headways, message=f"{settings.bus_count}대 기준, {interval}분 간격으로 차량별 회차 시간표를 만들었습니다.")
