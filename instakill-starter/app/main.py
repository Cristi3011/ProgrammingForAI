
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.database import init_db
from app.api.search import router as search_router
from app.services.search_service import SearchService


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    app.state.search_service = SearchService()
    yield


app = FastAPI(title="InstaKill", lifespan=lifespan)

app.include_router(search_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
