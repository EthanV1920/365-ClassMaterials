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
    catalog = ""

    # SQL statements
    select_sql = sqlalchemy.text("""
                                 SELECT *
                                 FROM
                                     potion_inventory
                                 WHERE
                                     quantity > 0;
                                 """)

    # Adding SQL execution
    with db.engine.begin() as connection:
        available_potions = connection.execute(select_sql).fetchall()
        print(f"Available Potions: {available_potions}")

        for potions in available_potions:
            catalog += f"""
                           {{
                               "sku": {potions[1]},
                               "name": {potions[2]},
                               "quantity": {potions[3]},
                               "price": {potions[4]},
                               "potion_type": {potions[5]},
                               }},"""

        print(f"Catalog: {catalog}")

    return [catalog]
