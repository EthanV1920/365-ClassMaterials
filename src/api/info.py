from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/info",
    tags=["info"],
    dependencies=[Depends(auth.get_api_key)],
)


class Timestamp(BaseModel):
    day: str
    hour: int


@router.post("/current_time")
def post_time(timestamp: Timestamp):
    """
    Share current time.
    """
    # WARN: how do I add the time stamp function?
    # this tells me the game time
    return "OK"
