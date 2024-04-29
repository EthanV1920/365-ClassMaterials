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

    # log_sql = sqlalchemy.text("""
    #                           insert into
    #                           wholesale_purchase_history (
    #                               order_id,
    #                               sku,
    #                               ml_per_barrel,
    #                               potion_type,
    #                               price,
    #                               quantity,
    #                               is_red,
    #                               is_green,
    #                               is_blue,
    #                               is_dark)
    #                           values (
    #                               :order_id,
    #                               :sku,
    #                               :ml_per_barrel,
    #                               :potion_type,
    #                               :price,
    #                               :quantity,
    #                               :is_red,
    #                               :is_green,
    #                               :is_blue,
    #                               :is_dark)
    #                           """)

    # sql execution
    gold = data.get_gold()
    # with db.engine.begin() as connection:
    purchasedVolume = [0, 0, 0, 0]

    # gold and ml manipulation
    for barrel in barrels_delivered:
        spent += (barrel.price * barrel.quantity)
        for i, volume in enumerate(purchasedVolume):
            purchasedVolume[i] += barrel.potion_type[i] * barrel.ml_per_barrel
            data.add_wholesale_record(barrel, order_id)
    # TODO: Add an assertion for the length of the 4 element

        # connection.execute(log_sql,
        #                    {"order_id": order_id,
        #                     "sku": barrel.sku,
        #                     "ml_per_barrel": barrel.ml_per_barrel,
        #                     "potion_type": str(barrel.potion_type),
        #                     "price": barrel.price,
        #                     "quantity": barrel.quantity,
        #                     "is_red": bool(barrel.potion_type[0]),
        #                     "is_green": bool(barrel.potion_type[1]),
        #                     "is_blue": bool(barrel.potion_type[2]),
        #                     "is_dark": bool(barrel.potion_type[3]),
        #                     })

        gold -= spent
        print(f"Gold: {gold}")

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
    # if I have less than this many ml, buy more
    ml_threshold = 1000

    # barrel buying logic
    # TODO: Improve barrel logic
    for barrel in wholesale_catalog:
        # print(barrel)
        for index, potion in enumerate(barrel.potion_type):

            buy_more = (raw_data[index] < ml_threshold)
            enough_gold = (barrel.price + will_spend < gold)
            is_correct_color = (potion > 0)
            # print(f"""
            #       buy_more: {buy_more}
            #       enough_gold: {enough_gold}
            #       is_correct_color: {is_correct_color}
            #       """)

            if buy_more and enough_gold and is_correct_color:
                print(f"Barrel sku: {barrel.sku}")
                barrels_to_buy.append([barrel.sku, quantity_of_barrels])
                will_spend += barrel.price * barrels_to_buy[index][1]

    print(f"Estimated cost of product is {will_spend}")
    print(f"Potions to Buy: {barrels_to_buy}")

    purchase_request = []
    for potions in barrels_to_buy:
        purchase_request.append({
                "sku": potions[0],
                "quantity": potions[1]
                })

    return purchase_request
