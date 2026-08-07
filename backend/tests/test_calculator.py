from app.schemas import ActivityInput, BusInput, DriverInput, ScheduleInput, TripInput
from app.services.calculator import calculate
from app.services.generator import generate
from app.main import health_check


def test_health_check_returns_ok():
    assert health_check() == {"status": "ok"}


def schedule(**changes):
    data = {
        "name": "테스트", "origin": "A", "destination": "B", "max_average_speed_kmh": 50,
        "buses": [BusInput(id="bus-1", name="1번 버스")],
        "drivers": [DriverInput(id="driver-1", name="김기사", work_start="08:00", work_end="18:00")],
        "trips": [TripInput(id="trip-1", departure_time="10:00", arrival_time="10:45", distance_km=30, bus_id="bus-1", driver_id="driver-1")],
        "activities": [],
    }
    return ScheduleInput(**(data | changes))


def test_calculate_speed_and_overnight_duration():
    result = calculate(schedule(trips=[TripInput(id="trip-1", departure_time="23:30", arrival_time="00:30", distance_km=30, bus_id="bus-1", driver_id="driver-1")]))
    assert result.trips[0].duration_minutes == 60
    assert result.trips[0].required_average_speed_kmh == 30


def test_calculate_marks_overlapping_bus_and_charge_time():
    result = calculate(schedule(activities=[ActivityInput(kind="charge", id="charge-1", start_time="10:10", bus_id="bus-1", to_charger_minutes=10, charge_minutes=30, to_departure_minutes=10)]))
    assert result.activities[0].total_minutes == 50
    assert result.activities[0].end_time == "11:00"
    assert any("버스 일정이 겹칩니다" in issue.message for issue in result.issues)


def generation(**changes):
    return {
        "first_departure": "06:00", "last_departure": "07:00", "outbound_minutes": 60,
        "inbound_minutes": 60, "min_rest_minutes": 5, "bus_count": 3, "interval_minutes": 20,
    } | changes


def test_generate_staggers_each_bus_by_the_input_headway():
    result = generate(schedule(generation=generation()))
    assert result.schedule and result.required_bus_count == 3
    outbound = [trip for trip in result.schedule.trips if trip.direction == "outbound"]
    assert [(trip.departure_time, trip.bus_id) for trip in outbound[:3]] == [
        ("06:00", result.schedule.buses[0].id), ("06:20", result.schedule.buses[1].id), ("06:40", result.schedule.buses[2].id),
    ]
    assert not calculate(result.schedule).issues


def test_generate_calculates_interval_when_input_is_zero():
    result = generate(schedule(generation=generation(bus_count=5, interval_minutes=0)))
    assert result.schedule and result.schedule.headway_minutes == 26
    assert [trip.departure_time for trip in result.schedule.trips if trip.direction == "outbound"] == ["06:00", "06:26", "06:52"]
