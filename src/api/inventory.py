from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
from src import database as db
import math
import sqlalchemy


router = APIRouter(
        prefix="/inventory",
        tags=["inventory"],
        dependencies=[Depends(auth.get_api_key)],
        )


@router.get("/audit")
def get_inventory():
    """
    Get the inventory.
    """
    print("Audit Being Performed")

    potion_sql = sqlalchemy.text("""
                                 SELECT sum(quantity)
                                 FROM potion_inventory
                                 """)

    ml_sql = sqlalchemy.text("""
                             SELECT num_red_ml +
                                    num_green_ml +
                                    num_blue_ml
                             FROM global_inventory
                             """)

    gold_sql = sqlalchemy.text("""
                               SELECT gold
                               FROM global_inventory
                               """)
    with db.engine.begin() as connection:
        potion_count = connection.execute(potion_sql).scalar()
        ml_count = connection.execute(ml_sql).scalar()
        gold_count = connection.execute(gold_sql).scalar()

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
