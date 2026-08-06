import math
from typing import List, Dict, Any, Tuple
from app.models.schedule import ScheduleRequest, ScheduleEntry, ScheduleResponse

def time_to_minutes(time_str: str) -> int:
    """'HH:MM' 형식의 시간 문자열을 분 단위 정수로 변환"""
    try:
        parts = time_str.split(':')
        return int(parts[0]) * 60 + int(parts[1])
    except (ValueError, IndexError):
        raise ValueError(f"Invalid time format: {time_str}. Expected 'HH:MM'")

def minutes_to_time(minutes: int) -> str:
    """분 단위 정수를 'HH:MM' 형식의 시간 문자열로 변환"""
    minutes = int(minutes) % 1440
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"

def calculate_schedule(req: ScheduleRequest) -> ScheduleResponse:
    try:
        start_min = time_to_minutes(req.first_departure)
        end_min = time_to_minutes(req.last_departure)
    except ValueError as e:
        return ScheduleResponse(success=False, message=str(e), interval_minutes=0.0, warnings=[], schedule=[])

    if start_min >= end_min:
        return ScheduleResponse(
            success=False,
            message="첫차 시간이 막차 시간보다 늦거나 같을 수 없습니다.",
            interval_minutes=0.0,
            warnings=[],
            schedule=[]
        )

    # 1. 배차 간격(Interval) 결정
    if req.interval_minutes and req.interval_minutes > 0:
        interval = req.interval_minutes
    else:
        # 차량 N대가 회차 휴식을 취하며 순환하기 위한 최소 배차간격 계산
        cycle_time = req.one_way_time + req.min_rest_time + req.return_way_time + req.min_rest_time
        interval = math.ceil(cycle_time / req.bus_count)
        if interval < 5:
            interval = 5

    # 2. 순연 시뮬레이션 방식 (Shift-based Dispatching)
    # 차량별 상태 초기화: 차량 ID, 현재 위치('START'/'END'), 다음 출차 가능 시각(available_time), 현재 회차 수
    vehicles = []
    for i in range(1, req.bus_count + 1):
        vehicles.append({
            "id": i,
            "location": "START",
            "available_time": start_min, # 첫출발 시에는 휴식 대기 없이 즉시 가용
            "rounds": 0
        })

    schedule_entries: List[ScheduleEntry] = []
    warnings: List[str] = []

    # 기점 출발 타임라인 시뮬레이션
    # current_go_slot: 다음 기점 출발 예정 시각
    current_go_slot = start_min
    bus_index = 0 # 차량 순환 인덱스 (0 ~ bus_count-1)

    while current_go_slot <= end_min:
        v = vehicles[bus_index]

        # 기점 출발 시각 결정:
        # 예정 슬롯 시각(current_go_slot)과 차량의 휴식 완료 시각(v.available_time) 중 늦은 시각에 출발
        actual_go_dept = max(current_go_slot, v["available_time"])

        # 기점 ➔ 종점 운행 정보 생성
        v["rounds"] += 1
        round_no = v["rounds"]
        actual_go_arr = actual_go_dept + req.one_way_time

        schedule_entries.append(
            ScheduleEntry(
                bus_id=v["id"],
                round_no=round_no,
                direction="GO",
                departure_time=minutes_to_time(actual_go_dept),
                arrival_time=minutes_to_time(actual_go_arr),
                rest_time_after=0 # 종점 휴식 시간은 종점 출발 시 정해짐
            )
        )

        # 종점 ➔ 기점 운행 시각 결정:
        # 종점 도착 후 최소 휴식시간(req.min_rest_time)을 보장받은 후 출발
        # (단, 1회차인 경우 준비된 기사님으로 즉시 출발 가능하도록 설정)
        rest_at_end = req.min_rest_time if round_no > 1 else 0
        actual_back_dept = actual_go_arr + rest_at_end
        actual_back_arr = actual_back_dept + req.return_way_time

        schedule_entries.append(
            ScheduleEntry(
                bus_id=v["id"],
                round_no=round_no,
                direction="BACK",
                departure_time=minutes_to_time(actual_back_dept),
                arrival_time=minutes_to_time(actual_back_arr),
                rest_time_after=0 # 기점 도착 후 다음 기점 출발 시까지의 휴식
            )
        )

        # 차량의 다음 기점 출발 가능 시각 업데이트 (기점 도착 + 최소 휴식시간)
        v["available_time"] = actual_back_arr + req.min_rest_time

        # 다음 배차 슬롯 업데이트 (실제 출발한 시각 + 배차간격)
        current_go_slot = actual_go_dept + interval

        # 다음 순번 차량 지정 (Round-Robin)
        bus_index = (bus_index + 1) % req.bus_count

    # 3. 각 운행 간 실제 휴식 시간(rest_time_after) 정밀 계산
    schedule_entries.sort(key=lambda x: (x.bus_id, x.round_no, 0 if x.direction == "GO" else 1))

    for i in range(len(schedule_entries)):
        curr_e = schedule_entries[i]
        curr_arr = time_to_minutes(curr_e.arrival_time)

        # 동일 차량의 바로 다음 운행 찾기
        if i + 1 < len(schedule_entries) and schedule_entries[i+1].bus_id == curr_e.bus_id:
            next_e = schedule_entries[i+1]
            next_dep = time_to_minutes(next_e.departure_time)
            if next_dep < curr_arr:
                next_dep += 1440
            curr_e.rest_time_after = next_dep - curr_arr
        else:
            curr_e.rest_time_after = 0

    # 동일 시각 출차 겹침 검사 (순연 적용 후 최종 검증)
    # 중복 경고 메시지 필터링
    unique_warnings = list(dict.fromkeys(warnings))

    return ScheduleResponse(
        success=True,
        message="배차 시간표가 성공적으로 자동 생성되었습니다.",
        interval_minutes=float(interval),
        warnings=unique_warnings,
        schedule=schedule_entries
    )
