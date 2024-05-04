import sqlalchemy
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from src import database as db


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)


@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    sql = sqlalchemy.text("""
                          update
                              global_inventory
                          set
                              gold = 100;
                          delete from wholesale_purchase_history;
                          delete from potion_purchase_history;
                          delete from customer_visits;
                          delete from carts;
                          """)

    with db.engine.begin() as connection:
        connection.execute(sql)

    print("Reset Store")

    return "OK"
