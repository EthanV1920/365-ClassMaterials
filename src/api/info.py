from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth

from src import potion_data as data

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
    Share current time in the game with the day being:
        > Edgeday
        > Bloomday
        > Aracanaday
        > Hearthday
        > Crownday
        > Blesseday
        > Soulday

    and the hour being a 24-hour number in increments of 2
    """

    print(f"The current time is: {timestamp.hour} on: {timestamp.day}")
    data.add_time_table(timestamp)

    return "OK"
