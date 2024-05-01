from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy

from src import database as db
from src import potion_data as data

router = APIRouter(
        prefix="/inventory",
        tags=["inventory"],

        )


@router.get("/audit")
def get_inventory():
    """
    Get the inventory.
    """
    print("Audit Being Performed")

    potion_count = data.get_potion_count()

    raw_ml = data.get_raw_volume()
    ml_count = 0
    for raw in raw_ml:
        ml_count += raw

    gold_count = data.get_gold()

    return {"number_of_potions": potion_count,
            "ml_in_barrels": ml_count,
            "gold": gold_count}


# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion.
    Each additional capacity unit costs 1000 gold.
    """

    return {
            "potion_capacity": 0,
            "ml_capacity": 0
            }


class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int


# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase: CapacityPurchase, order_id: int):
    """
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion.
    Each additional capacity unit costs 1000 gold.
    """

    return "OK"
