from datetime import UTC, datetime

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request, Response, status
from pymongo import ReturnDocument

from app.database import schedules_collection
from app.schemas import GenerationResult, ScheduleInput, ScheduleResult
from app.services.calculator import calculate
from app.services.generator import generate

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.post("/generate", response_model=GenerationResult)
async def generate_schedule(schedule: ScheduleInput):
    try:
        return generate(schedule)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


def schedule_result(document: dict) -> ScheduleResult:
    return calculate(ScheduleInput(**document), id=str(document["_id"]),
                     created_at=document.get("created_at"), updated_at=document.get("updated_at"))


def object_id(value: str) -> ObjectId:
    if not ObjectId.is_valid(value): raise HTTPException(status_code=404, detail="시간표를 찾을 수 없습니다.")
    return ObjectId(value)


async def find_schedule(request: Request, schedule_id: str) -> dict:
    document = await schedules_collection(request.app).find_one({"_id": object_id(schedule_id)})
    if not document: raise HTTPException(status_code=404, detail="시간표를 찾을 수 없습니다.")
    return document


@router.get("", response_model=list[ScheduleResult])
async def list_schedules(request: Request):
    documents = await schedules_collection(request.app).find().sort("updated_at", -1).to_list(None)
    return [schedule_result(document) for document in documents]


@router.post("", response_model=ScheduleResult, status_code=status.HTTP_201_CREATED)
async def create_schedule(request: Request, schedule: ScheduleInput):
    now = datetime.now(UTC)
    document = {**schedule.model_dump(), "created_at": now, "updated_at": now}
    result = await schedules_collection(request.app).insert_one(document)
    document["_id"] = result.inserted_id
    return schedule_result(document)


@router.get("/{schedule_id}", response_model=ScheduleResult)
async def get_schedule(request: Request, schedule_id: str):
    return schedule_result(await find_schedule(request, schedule_id))


@router.put("/{schedule_id}", response_model=ScheduleResult)
async def update_schedule(request: Request, schedule_id: str, schedule: ScheduleInput):
    document = await schedules_collection(request.app).find_one_and_update(
        {"_id": object_id(schedule_id)}, {"$set": {**schedule.model_dump(), "updated_at": datetime.now(UTC)}},
        return_document=ReturnDocument.AFTER)
    if not document: raise HTTPException(status_code=404, detail="시간표를 찾을 수 없습니다.")
    return schedule_result(document)


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(request: Request, schedule_id: str):
    result = await schedules_collection(request.app).delete_one({"_id": object_id(schedule_id)})
    if not result.deleted_count: raise HTTPException(status_code=404, detail="시간표를 찾을 수 없습니다.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
