from app.schemas import EstimateResult, RouteInput, StopResult


def estimate(route: RouteInput) -> EstimateResult:
    speed_mps = route.average_speed_kmh * 1000 / 3600
    total_distance = 0.0
    total_seconds = 0
    stops = []

    for index, stop in enumerate(route.stops):
        distance = 0 if index == 0 else stop.distance_from_previous_m
        seconds = round(distance / speed_mps)
        total_distance += distance
        total_seconds += seconds
        stops.append(StopResult(**stop.model_dump(), segment_seconds=seconds, cumulative_seconds=total_seconds))

    return EstimateResult(stops=stops, total_distance_m=total_distance, total_seconds=total_seconds)
