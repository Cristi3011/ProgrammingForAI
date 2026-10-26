"""HTTP boundary for personalized and chronological feeds."""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.services.feed_service import FeedService

router = APIRouter()


def get_feed_service(request: Request) -> FeedService:
    """Get the shared feed service created for this app."""
    return request.app.state.feed_service


@router.get("/feed")
def get_feed(
    user_id: int = Query(..., description="ID of the user requesting a feed"),
    limit: int = Query(20, ge=1, le=50),
    strategy: Literal["for_you", "chronological"] = Query("for_you"),
    service: FeedService = Depends(get_feed_service),
) -> dict:
    response = service.get_feed(user_id=user_id, limit=limit, strategy=strategy)
    if response is None:
        raise HTTPException(status_code=404, detail=f"User {user_id} was not found.")
    return response
