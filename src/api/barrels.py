import sqlalchemy
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth

# User python imports
from src import database as db

router = APIRouter(
        prefix="/barrels",
        tags=["barrels"],
        dependencies=[Depends(auth.get_api_key)],
        )


class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int


@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """
    Version 1: Subtract gold price and add ml of potion
    """

    spent = 0
    ml_bought = 0

    for barrel in barrels_delivered:
        spent += (barrel.price * barrel.quantity)
        ml_bought += (barrel.ml_per_barrel * barrel.quantity)
        print(f"Bought ml: {ml_bought}")
        print(f"Spent: {spent}")

    # sql select statements for ml and gold
    ml_sql = sqlalchemy.text("""
                          SELECT num_green_ml
                          FROM global_inventory
                          """)

    gold_sql = sqlalchemy.text("""
                          SELECT gold
                          FROM global_inventory
                          """)
    # sql update stamtents for ml and gold
    update_sql = sqlalchemy.text("""
                                 UPDATE global_inventory
                                 SET gold = :gold,
                                 num_green_ml = :ml;
                                 """)

    # sql execution
    with db.engine.begin() as connection:
        # select sql
        potion_ml = connection.execute(ml_sql).scalar()
        gold = connection.execute(gold_sql).scalar()

        # gold and ml manipulation
        potion_ml += ml_bought
        gold -= spent
        print(f"Potions ml: {potion_ml}")
        print(f"Gold: {gold}")

        # update sql
        connection.execute(update_sql, {"gold": gold, "ml": potion_ml})

    print(f"barrels delivered: {barrels_delivered} order_id: {order_id}")

    return "OK"


# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """
    Version 1: if you have less than 10 potions buy more barrels
    """
    print(wholesale_catalog)

    # sql select statements for ml and gold
    sql = sqlalchemy.text("""
                          SELECT num_green_ml
                          FROM global_inventory
                          """)
    with db.engine.begin() as connection:
        potion_count = connection.execute(sql).scalar()

    if potion_count < 10:
        buy_green_count = 1

    for barrel in wholesale_catalog:
        if barrel.potion_type == [0, 100, 0, 0]:
            sku = barrel.sku
            print(f"SKU: {sku}")

    return [
            {
                "sku": sku,
                "quantity": buy_green_count,
                }
            ]
