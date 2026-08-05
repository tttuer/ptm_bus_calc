from pymongo import AsyncMongoClient

from app.config import MONGODB_DB, MONGODB_URI


def create_client() -> AsyncMongoClient:
    return AsyncMongoClient(MONGODB_URI)


def routes_collection(app):
    return app.state.mongo[MONGODB_DB].routes
