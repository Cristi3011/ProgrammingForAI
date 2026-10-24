"""HTTP boundary for semantic search."""
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.services.search_service import SearchService

router = APIRouter()


def get_search_service(request: Request) -> SearchService:
    """Get the shared application service created for this app."""
    return request.app.state.search_service


@router.get("/search")
def search_posts(
    q: str = Query(..., min_length=1, description="Text to search for"),
    limit: int = Query(..., ge=1, le=20, description="Maximum number of results (1–20)"),
    service: SearchService = Depends(get_search_service),
) -> dict:
    if not q.strip():
        raise HTTPException(status_code=422, detail="Query parameter 'q' must not be empty.")
    return service.search(q.strip(), limit)