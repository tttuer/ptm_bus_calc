from app.core.scheduler import calculate_schedule, time_to_minutes
from app.models.schedule import ScheduleRequest


def test_schedule_never_leaves_origin_after_last_departure():
    result = calculate_schedule(ScheduleRequest(
        first_departure="06:00", last_departure="22:30", one_way_time=60,
        return_way_time=60, min_rest_time=15, bus_count=5, interval_minutes=15,
    ))

    departures = [time_to_minutes(entry.departure_time) for entry in result.schedule if entry.direction == "GO"]
    assert result.success
    assert max(departures) <= time_to_minutes("22:30")
