import sqlalchemy
from fastapi import APIRouter, Depends
# from enum import Enum
from pydantic import BaseModel
from src.api import auth

# User python imports
from src import database as db
from src import potion_data as data

router = APIRouter(
        prefix="/bottler",
        tags=["bottler"],
        dependencies=[Depends(auth.get_api_key)],
        )


class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int


@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """
    Receive the bottles that were ordered and add them to your inventory as
    well as subtract the volume of each potion that was used.
    """
    print(f"potions delivered: {potions_delivered} order_id: {order_id}")

    potion_sql = sqlalchemy.text("""
                                 insert into
                                     potion_purchase_history (cart_id,
                                                              sku,
                                                              quantity)
                                 values(
                                     -1,
                                     (select
                                          sku
                                      from
                                          potion_inventory
                                      where
                                      potion_type = :potion_type),
                                     :quantity
                                     )
                                 """)

    bottled_potions = [0, 0, 0, 0]

    # TODO: will need to change later to handle mixed potions
    potion_types = []
    for potions in potions_delivered:
        potion_types.append({'potion_type': potions.potion_type,
                             'quantity': potions.quantity})
        for index, color in enumerate(potions.potion_type):
            bottled_potions[index] += potions.quantity * color

    with db.engine.begin() as connection:
        connection.execute(potion_sql, potion_types)

    data.add_bottle_record(bottled_potions)

    print(f"Bottled Potions: {bottled_potions}")

    # add to wholesale leader to track ml

    return "OK"


@router.post("/plan")
def get_bottle_plan():
    """
    Get the volume of liquid for each color of potion and then figure out how
    many bottles will be needed. Return your bottleing plan.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Possible potions
    bottle_request = []
    potion_count = data.get_potion_count()

    # Adding SQL execution
    # TODO: Add logic to make more potions of different types
    potion_volume = data.get_raw_volume()
    print(f"Volume of Potions in Inventory: {potion_volume}")
    potion_storage = data.get_globals().potion_storage
    print(f"Potion Storage Available: {potion_storage}")
    for index, volume in enumerate(potion_volume):
        potions_to_bottle = 0
        while volume >= 100:
            if potions_to_bottle >= (potion_storage - potion_count)/3 - 1:
                break
            potions_to_bottle += 1
            volume -= 100

        if potions_to_bottle > 0:
            potion_type = [0, 0, 0, 0]
            potion_type[index] = 100
            bottle_request.append({
                "potion_type": potion_type,
                "quantity": potions_to_bottle,
                })

    print(f"Potions to Bottle {potions_to_bottle}")

    print(f"Total requested bottles: {bottle_request}")

    return bottle_request


if __name__ == "__main__":
    print(get_bottle_plan())
