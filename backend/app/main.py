from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import ALLOWED_ORIGINS
from app.database import create_client
from app.routers.routes import router as routes_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mongo = create_client()
    yield
    await app.state.mongo.close()


app = FastAPI(title="Bus Time API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_methods=["*"], allow_headers=["*"])
app.include_router(routes_router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
