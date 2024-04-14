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
    potion_ml = [0, 0, 0, 0]

    for barrel in barrels_delivered:
        for i, potion in enumerate(potion_ml):
            potion_ml[i] += (barrel.potion_type[i]/100) * barrel.ml_per_barrel

        spent += (barrel.price * barrel.quantity)

    print(f"Bought ml: {potion_ml}")
    print(f"Spent: {spent}")

    # sql select statements for ml and gold
    ml_sql = sqlalchemy.text("""
                             SELECT num_red_ml, num_green_ml, num_blue_ml
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
                                 num_red_ml = :rml,
                                 num_green_ml = :gml,
                                 num_blue_ml = :bml;
                                 """)

    log_sql = sqlalchemy.text("""
                              insert into
                              wholesale_purchase_history (
                                  order_id,
                                  sku,
                                  ml_per_barrel,
                                  potion_type,
                                  price,
                                  quantity)
                              values (
                                  :order_id,
                                  :sku,
                                  :ml_per_barrel,
                                  :potion_type,
                                  :price,
                                  :quantity)
                              """)

    # sql execution
    with db.engine.begin() as connection:
        # select sql
        potion_ml_result = connection.execute(ml_sql)
        gold = connection.execute(gold_sql).scalar()

        # gold and ml manipulation
        for potion in potion_ml_result.fetchall():
            for index, volume in enumerate(potion):
                potion_ml[index] += volume

        gold -= spent
        print(f"Potions to DB: {potion_ml}")
        print(f"Gold: {gold}")

        # update sql
        connection.execute(update_sql, {"gold": gold,
                                        "rml": potion_ml[0],
                                        "gml": potion_ml[1],
                                        "bml": potion_ml[2]})
        for barrel in barrels_delivered:
            connection.execute(log_sql, {"order_id": order_id,
                                         "sku": barrel.sku,
                                         "ml_per_barrel": barrel.ml_per_barrel,
                                         "potion_type": str(barrel.potion_type),
                                         "price": barrel.price,
                                         "quantity": barrel.quantity})

    print(f"barrels delivered: {barrels_delivered} order_id: {order_id}")

    return "OK"


# Gets called every other tick
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """
    Version 1: if you have less than 10 potions buy more barrels
    TODO: add a tracking system for unique potions
    """
    print(wholesale_catalog)

    # sql select statements for ml and gold
    sql = sqlalchemy.text("""
                          SELECT num_green_ml, num_red_ml, num_blue_ml
                          FROM global_inventory
                          """)
    with db.engine.begin() as connection:
        potion_count = connection.execute(sql).scalar()

    red_sku = ''
    green_sku = ''
    blue_sku = ''

    # barrel buying logic
    if potion_count < 10:
        buy_green_count = 1
    else:
        buy_green_count = 0

    buy_red_count = 0
    buy_blue_count = 0

    for barrel in wholesale_catalog:
        if barrel.potion_type == [100, 0, 0, 0]:
            red_sku = barrel.sku
            print(f"red sku: {red_sku}")
        if barrel.potion_type == [0, 100, 0, 0]:
            green_sku = barrel.sku
            print(f"green sku: {green_sku}")
        if barrel.potion_type == [0, 0, 100, 0]:
            blue_sku = barrel.sku
            print(f"blue sku: {blue_sku}")

    return [
            {
                "sku": red_sku,
                "quantity": buy_red_count,
                },
            {
                "sku": green_sku,
                "quantity": buy_green_count,
                },
            {
                "sku": blue_sku,
                "quantity": buy_blue_count,
                },
            ]
