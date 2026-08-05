import asyncio
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import HTTPException

from app.config import KAKAO_REST_API_KEY
from app.schemas import DirectionRequest, DirectionResult


def fetch_distance(direction: DirectionRequest) -> int:
    query = urlencode({
        "origin": f"{direction.origin_longitude},{direction.origin_latitude}",
        "destination": f"{direction.destination_longitude},{direction.destination_latitude}",
        "priority": "RECOMMEND",
    })
    request = Request(
        f"https://apis-navi.kakaomobility.com/v1/directions?{query}",
        headers={"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"},
    )
    with urlopen(request, timeout=10) as response:
        return json.load(response)["routes"][0]["summary"]["distance"]


async def driving_distance(direction: DirectionRequest) -> DirectionResult:
    if not KAKAO_REST_API_KEY:
        raise HTTPException(status_code=503, detail="카카오 REST API 키가 설정되지 않았습니다.")
    try:
        return DirectionResult(distance_m=await asyncio.to_thread(fetch_distance, direction))
    except (IndexError, KeyError, OSError, ValueError):
        raise HTTPException(status_code=502, detail="카카오 도로 거리를 가져오지 못했습니다.")
