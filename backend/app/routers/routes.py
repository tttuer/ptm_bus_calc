from datetime import UTC, datetime

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request, Response, status
from pymongo import ReturnDocument

from app.database import routes_collection
from app.schemas import DirectionRequest, DirectionResult, EstimateResult, RouteInput, RouteResult
from app.services.calculator import estimate
from app.services.directions import driving_distance

router = APIRouter(prefix="/routes", tags=["routes"])


def route_result(document: dict) -> RouteResult:
    route = RouteInput(**document)
    calculation = estimate(route)
    return RouteResult(**{
        **route.model_dump(),
        **calculation.model_dump(),
        "id": str(document["_id"]),
        "created_at": document.get("created_at"),
        "updated_at": document.get("updated_at"),
    })


def object_id(route_id: str) -> ObjectId:
    if not ObjectId.is_valid(route_id):
        raise HTTPException(status_code=404, detail="노선을 찾을 수 없습니다.")
    return ObjectId(route_id)


async def find_route(request: Request, route_id: str) -> dict:
    document = await routes_collection(request.app).find_one({"_id": object_id(route_id)})
    if not document:
        raise HTTPException(status_code=404, detail="노선을 찾을 수 없습니다.")
    return document


@router.get("", response_model=list[RouteResult])
async def list_routes(request: Request):
    documents = await routes_collection(request.app).find().sort("updated_at", -1).to_list(None)
    return [route_result(document) for document in documents]


@router.post("", response_model=RouteResult, status_code=status.HTTP_201_CREATED)
async def create_route(request: Request, route: RouteInput):
    now = datetime.now(UTC)
    document = {**route.model_dump(), "created_at": now, "updated_at": now}
    result = await routes_collection(request.app).insert_one(document)
    document["_id"] = result.inserted_id
    return route_result(document)


@router.post("/estimate", response_model=EstimateResult)
async def estimate_route(route: RouteInput):
    return estimate(route)


@router.post("/driving-distance", response_model=DirectionResult)
async def get_driving_distance(direction: DirectionRequest):
    return await driving_distance(direction)


@router.get("/{route_id}", response_model=RouteResult)
async def get_route(request: Request, route_id: str):
    return route_result(await find_route(request, route_id))


@router.put("/{route_id}", response_model=RouteResult)
async def update_route(request: Request, route_id: str, route: RouteInput):
    route_object_id = object_id(route_id)
    result = await routes_collection(request.app).find_one_and_update(
        {"_id": route_object_id},
        {"$set": {**route.model_dump(), "updated_at": datetime.now(UTC)}},
        return_document=ReturnDocument.AFTER,
    )
    if not result:
        raise HTTPException(status_code=404, detail="노선을 찾을 수 없습니다.")
    return route_result(result)


@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_route(request: Request, route_id: str):
    result = await routes_collection(request.app).delete_one({"_id": object_id(route_id)})
    if not result.deleted_count:
        raise HTTPException(status_code=404, detail="노선을 찾을 수 없습니다.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
