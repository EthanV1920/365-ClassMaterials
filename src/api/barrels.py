import sqlalchemy
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth

# User python imports
from src import database as db
from src import potion_data as data

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

    print(f"Bought ml: {potion_ml}")
    print(f"Spent: {spent}")

    # sql execution
    gold = data.get_gold()
    # with db.engine.begin() as connection:
    purchasedVolume = [0, 0, 0, 0]

    # gold and ml manipulation
    # TODO: Add an assertion for the length of the 4 element
    for barrel in barrels_delivered:
        spent += (barrel.price * barrel.quantity)
        data.add_wholesale_barrel(barrel, order_id)
        for i, volume in enumerate(purchasedVolume):
            purchasedVolume[i] += barrel.potion_type[i] * barrel.ml_per_barrel

    gold -= spent
    print(f"Gold: {gold}")
    data.set_gold(-spent)

    print(f"barrels delivered: {barrels_delivered} order_id: {order_id}")

    return "OK"


# Gets called every other tick
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """
    Logic handling which barrels to buy
    """
    print(wholesale_catalog)

    # sql select statements for ml and gold
    potion_sql = sqlalchemy.text("""
                          select
                            quantity
                          from
                            potion_inventory
                          where
                            id <= 4;
                          """)

    raw_data = data.get_raw_volume()
    print(f"raw_data: {raw_data}")
    gold = data.get_gold()
    print(f"gold: {gold}")

    barrels_to_buy = []
    will_spend = 0
    quantity_of_barrels = 1
    # Calculate the available room
    globals = data.get_globals()
    room = globals.space - sum(raw_data)
    volume_to_buy = 0

    print(f"Room: {room}")
    # barrel buying logic
    # TODO: Improve barrel logic
    for barrel in wholesale_catalog:
        # print(barrel)
        for index, potion in enumerate(barrel.potion_type):

            is_correct_barrel = False
            if ("LARGE" in barrel.sku):
                is_correct_barrel = True

            enough_gold = (barrel.price + will_spend < gold)
            is_correct_color = (potion > 0)

            buy_more = False
            if (volume_to_buy + barrel.ml_per_barrel < room):
                buy_more = True

            if buy_more and enough_gold and is_correct_color and is_correct_barrel:
                print(f"Barrel sku: {barrel.sku}")
                barrels_to_buy.append([barrel.sku, quantity_of_barrels])
                print(f"Barrels to buy: {barrels_to_buy}")
                will_spend += barrel.price * barrels_to_buy[index][1]
                volume_to_buy += barrel.ml_per_barrel

    print(f"Estimated cost of product is {will_spend}")
    print(f"Barrels to Buy: {barrels_to_buy}")
    print(f"Volume to Buy: {volume_to_buy}")

    purchase_request = []
    for potions in barrels_to_buy:
        purchase_request.append({
            "sku": potions[0],
            "quantity": potions[1]
                })

    return purchase_request
