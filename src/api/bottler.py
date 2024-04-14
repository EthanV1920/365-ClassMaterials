import sqlalchemy
from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth

# User python imports
from src import database as db

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

    bottled_potions = [0, 0, 0, 0]
    updated_ml = [0, 0, 0, 0]

    # TODO: will need to change later to handle mixed potions
    for potions in potions_delivered:
        for index, color in enumerate(potions.potion_type):
            bottled_potions[index] += potions.quantity * color / 100

    sql = sqlalchemy.text("""
                          SELECT
                          num_red_ml,
                          num_green_ml,
                          num_blue_ml
                          FROM global_inventory
                          """)

    update_sql = sqlalchemy.text("""
                                 UPDATE global_inventory
                                 SET
                                 num_red_ml = :red_ml,
                                 num_green_ml = :green_ml,
                                 num_blue_ml = :blue_ml;

                                 UPDATE potion_inventory
                                 SET quantity = :red_potions
                                 WHERE id = 1;

                                 UPDATE potion_inventory
                                 SET quantity = :green_potions
                                 WHERE id = 2;

                                 UPDATE potion_inventory
                                 SET quantity = :blue_potions
                                 where id = 3;
                                 """)

    # Adding SQL execution
    with db.engine.begin() as connection:
        potion_volume = connection.execute(sql).fetchall()
        print(f"Volume of Potions Before Botteling: {potion_volume}")
        for index, volume in enumerate(potion_volume[0]):
            updated_ml[index] = volume - (bottled_potions[index] * 100)


    with db.engine.begin() as connection:
        connection.execute(update_sql, {
                                 "red_ml": updated_ml[0],
                                 "green_ml": updated_ml[1],
                                 "blue_ml": updated_ml[2],
                                 "red_potions": bottled_potions[0],
                                 "green_potions": bottled_potions[1],
                                 "blue_potions": bottled_potions[2]
                                 })

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

    # Initial logic: bottle all barrels into red potions.

    sql = sqlalchemy.text("""
                          SELECT
                          num_red_ml,
                          num_green_ml,
                          num_blue_ml
                          FROM global_inventory
                          """)

    # Possible potions
    potions_to_bottle = [0, 0, 0]

    # Adding SQL execution
    with db.engine.begin() as connection:
        potion_volume = connection.execute(sql).fetchall()
        print(f"Volume of Potions in Inventory: {potion_volume}")
        for index, volume in enumerate(potion_volume[0]):
            while volume >= 100:
                potions_to_bottle[index] += 1
                volume -= 100

        print(f"Total requested bottles: {potions_to_bottle}")

    return [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": potions_to_bottle[0],
                },
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": potions_to_bottle[1],
                },
            {
                "potion_type": [0, 0, 100, 0],
                "quantity": potions_to_bottle[2],
                }
            ]


if __name__ == "__main__":
    print(get_bottle_plan())
