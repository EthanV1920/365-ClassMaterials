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

    # for barrel in barrels_delivered:
    #     for i, potion in enumerate(potion_ml):
    #         potion_ml[i] += (barrel.potion_type[i]/100) * barrel.ml_per_barrel

        # spent += (barrel.price * barrel.quantity)

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
        purchasedVolume = [0, 0, 0, 0]

        # gold and ml manipulation
        for barrel in barrels_delivered:
            spent += (barrel.price * barrel.quantity)
            for i, volume in enumerate(purchasedVolume):
                purchasedVolume[i] += barrel.potion_type[i] * barrel.ml_per_barrel

            connection.execute(log_sql,
                               {"order_id": order_id,
                                "sku": barrel.sku,
                                "ml_per_barrel": barrel.ml_per_barrel,
                                "potion_type": str(barrel.potion_type),
                                "price": barrel.price,
                                "quantity": barrel.quantity})

        for potion in potion_ml_result.fetchall():
            for index, volume in enumerate(potion):
                potion_ml[index] = purchasedVolume[index] + volume

        gold -= spent
        print(f"Purchased Volume: {purchasedVolume}")
        print(f"Potions to DB: {potion_ml}")
        print(f"Gold: {gold}")

        # update sql
        connection.execute(update_sql, {"gold": gold,
                                        "rml": potion_ml[0],
                                        "gml": potion_ml[1],
                                        "bml": potion_ml[2]})

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
    gold_sql = sqlalchemy.text("""
                          select
                            gold
                          from
                            global_inventory;
                          """)

    potion_sql = sqlalchemy.text("""
                          select
                            quantity
                          from
                            potion_inventory
                          where
                            id <= 4;
                          """)
    with db.engine.begin() as connection:
        gold = connection.execute(gold_sql).scalar()
        inventory = connection.execute(potion_sql).fetchall()
        print(f"Potion Inventory: {inventory}")
        # for potion in inventory.fetchall():
        #     print(f"Potion Count: {potion}")

    barrels_to_buy = []
    willSpend = 0

    # barrel buying logic
    for barrel in wholesale_catalog:
        for index, potion in enumerate(barrel.potion_type):
            # print(f"Index: {index}")
            forecast = barrel.price + willSpend
            if inventory[index][0] < 10 and forecast < gold and potion > 0:
                print(f"Barrel sku: {barrel.sku}")
                # barrels_to_buy[index][1] += 1 / potion
                barrels_to_buy.append([barrel.sku, 1])
                willSpend += barrel.price * barrels_to_buy[index][1]

    print(f"Estimated cost of product is {willSpend}")
    print(f"Potions to Buy: {barrels_to_buy}")

    purchase_request = []
    for potions in barrels_to_buy:
        purchase_request.append({
                "sku": potions[0],
                "quantity": potions[1]
                })

    return purchase_request
