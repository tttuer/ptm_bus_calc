from collections import defaultdict

from app.schemas import ActivityInput, ActivityResult, Issue, ScheduleInput, ScheduleResult, TripInput, TripResult


def to_minutes(value: str) -> int:
    hour, minute = map(int, value.split(":"))
    return hour * 60 + minute


def time_text(minutes: int) -> str:
    day, minute = divmod(minutes, 1_440)
    return f"{'익일 ' if day else ''}{minute // 60:02}:{minute % 60:02}"


def interval(start: str, end: str) -> tuple[int, int]:
    start_minutes, end_minutes = to_minutes(start), to_minutes(end)
    return start_minutes, end_minutes + (1_440 if end_minutes <= start_minutes else 0)


def activity_minutes(activity: ActivityInput) -> int:
    return activity.duration_minutes if activity.kind == "rest" else sum((
        activity.to_charger_minutes, activity.charge_minutes, activity.to_departure_minutes,
    ))


def trip_result(trip: TripInput) -> TripResult:
    start, end = interval(trip.departure_time, trip.arrival_time)
    duration = end - start
    return TripResult(**trip.model_dump(), duration_minutes=duration,
                      required_average_speed_kmh=round(trip.distance_km / (duration / 60), 1))


def activity_result(activity: ActivityInput) -> ActivityResult:
    total = activity_minutes(activity)
    return ActivityResult(**activity.model_dump(), total_minutes=total,
                          end_time=time_text(to_minutes(activity.start_time) + total))


def overlaps(events: list[tuple[int, int, str]], label: str) -> list[Issue]:
    issues = []
    for (_, previous_end, _), (start, _, entity_id) in zip(sorted(events), sorted(events)[1:]):
        if start < previous_end:
            issues.append(Issue(severity="error", entity_id=entity_id, message=f"{label} 일정이 겹칩니다."))
    return issues


def in_shift(start: int, end: int, work_start: str, work_end: str) -> bool:
    shift_start, shift_end = interval(work_start, work_end)
    if start < shift_start: start, end = start + 1_440, end + 1_440
    return shift_start <= start and end <= shift_end


def validate(schedule: ScheduleInput, trips: list[TripResult], activities: list[ActivityResult]) -> list[Issue]:
    issues: list[Issue] = []
    bus_ids = {bus.id for bus in schedule.buses}
    drivers = {driver.id: driver for driver in schedule.drivers}
    events: dict[tuple[str, str], list[tuple[int, int, str]]] = defaultdict(list)

    for trip in trips:
        start, end = interval(trip.departure_time, trip.arrival_time)
        if not trip.bus_id: issues.append(Issue(severity="warning", entity_id=trip.id, message="배정할 차량이 없습니다."))
        elif trip.bus_id not in bus_ids: issues.append(Issue(severity="error", entity_id=trip.id, message="배정한 버스를 찾을 수 없습니다."))
        driver = drivers.get(trip.driver_id) if trip.driver_id else None
        if trip.driver_id and not driver: issues.append(Issue(severity="error", entity_id=trip.id, message="배정한 기사를 찾을 수 없습니다."))
        elif driver and not in_shift(start, end, driver.work_start, driver.work_end): issues.append(Issue(severity="warning", entity_id=trip.id, message="기사 근무시간 밖의 운행입니다."))
        if trip.required_average_speed_kmh > schedule.max_average_speed_kmh:
            issues.append(Issue(severity="warning", entity_id=trip.id, message=f"필요 평균속도 {trip.required_average_speed_kmh}km/h가 기준을 넘습니다."))
        if trip.bus_id: events[("버스", trip.bus_id)].append((start, end, trip.id))
        if trip.driver_id: events[("기사", trip.driver_id)].append((start, end, trip.id))

    for activity in activities:
        start, end = to_minutes(activity.start_time), to_minutes(activity.start_time) + activity.total_minutes
        if activity.bus_id not in bus_ids: issues.append(Issue(severity="error", entity_id=activity.id, message="배정한 버스를 찾을 수 없습니다."))
        events[("버스", activity.bus_id)].append((start, end, activity.id))
        if activity.driver_id:
            if activity.driver_id not in drivers: issues.append(Issue(severity="error", entity_id=activity.id, message="배정한 기사를 찾을 수 없습니다."))
            events[("기사", activity.driver_id)].append((start, end, activity.id))

    for (kind, _), resource_events in events.items(): issues.extend(overlaps(resource_events, kind))
    return issues


def calculate(schedule: ScheduleInput, **extra) -> ScheduleResult:
    trips = [trip_result(trip) for trip in schedule.trips]
    activities = [activity_result(activity) for activity in schedule.activities]
    data = schedule.model_dump() | extra
    data.update(trips=trips, activities=activities, issues=validate(schedule, trips, activities))
    return ScheduleResult(**data)
