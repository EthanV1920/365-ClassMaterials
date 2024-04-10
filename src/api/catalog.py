import sqlalchemy
from fastapi import APIRouter

# User python imports
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    # Adding SQL execution
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(
            "SELECT gold FROM global_inventory"))

    for row in result:
        print(row[0])
        goldCount = row[0]
        goldCount += 100
        print(goldCount)

        sql = sqlalchemy.text("""
                              UPDATE global_inventory
                              SET gold = :gold
                              WHERE num_green_potions = 1
                              """)
        # print(sql)
        with db.engine.begin() as connection:
            connection.execute(sql, {"gold": goldCount})

    return [
            {
                "sku": "RED_POTION_0",
                "name": "red potion",
                "quantity": 1,
                "price": 50,
                "potion_type": [100, 0, 0, 0],
            }
        ]
