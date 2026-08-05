from app.schemas import RouteInput, StopInput
from app.services.calculator import estimate
from app.routers.routes import route_result
from bson import ObjectId


def test_estimate_calculates_segment_and_total_time():
    result = estimate(RouteInput(
        name="테스트",
        average_speed_kmh=40,
        stops=[StopInput(name="출발"), StopInput(name="도착", distance_from_previous_m=10_000)],
    ))

    assert result.total_distance_m == 10_000
    assert result.total_seconds == 900
    assert result.stops[1].segment_seconds == 900
    assert result.stops[1].cumulative_seconds == 900


def test_route_result_uses_calculated_stops_once():
    route = route_result({
        "_id": ObjectId(),
        "name": "테스트",
        "average_speed_kmh": 30,
        "stops": [{"name": "출발", "distance_from_previous_m": 0}],
    })

    assert route.stops[0].cumulative_seconds == 0
