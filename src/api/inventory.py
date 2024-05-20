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
    gold = data.get_gold()
    golbals = data.get_globals()
    potion_requested = golbals.more_capacity
    ml_requested = golbals.more_potions
    print(f"More Potions: {potion_requested}")
    print(f"More {ml_requested}")
    print(f"Gold: {gold}")

    gold_to_spend = (ml_requested + potion_requested) * 1000
    print(f"Gold to spend: {gold_to_spend}")

    if (gold_to_spend > gold):
        print(f"Not enough gold. To spend: {gold_to_spend} Actual: {gold}")
        return {
                "potion_capacity": 0,
                "ml_capacity": 0
                }

    return {
            "potion_capacity": potion_requested,
            "ml_capacity": ml_requested
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

    inventory_sql = sqlalchemy.text("""
                                    insert into
                                        inventory_history(
                                                space,
                                                potion_storage,
                                                order_id
                                            )
                                    values(
                                            :space,
                                            :potion_storage,
                                            :order_id
                                          );
                                    update global_variables
                                    set
                                        more_capacity = 0,
                                        more_potions = 0
                                    """)

    inventory_options = {
                         "space": capacity_purchase.ml_capacity,
                         "potion_storage": capacity_purchase.potion_capacity,
                         "order_id": order_id
                        }

    data.set_gold(-(capacity_purchase.potion_capacity + capacity_purchase.ml_capacity))

    with db.engine.begin() as connection:
        connection.execute(inventory_sql, inventory_options)

    return "OK"
