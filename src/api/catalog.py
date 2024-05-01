import sqlalchemy
from fastapi import APIRouter

# User python imports
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    NOTE: can return a max of 6 potions
    """
    catalog = []

    # TODO: Add External configuration in a view

    # SQL statements
    # might want to integreat a view in here so that you can change logic from
    # database layer
    select_sql = sqlalchemy.text("""
                                 select
                                     potion_inventory.name as potion_name,
                                     potion_purchase_history.sku as potion_sku,
                                     sum(potion_purchase_history.quantity) as potion_quantity,
                                     potion_inventory.price as potion_price,
                                     potion_inventory.potion_type as potion_type
                                 from
                                     potion_purchase_history
                                     join potion_inventory on potion_inventory.sku = potion_purchase_history.sku
                                 group by
                                 potion_sku,
                                     potion_name,
                                     potion_price,
                                     potion_type
                                 having
                                     sum(potion_purchase_history.quantity) > 0

                                 """)

    # Adding SQL execution
    with db.engine.begin() as connection:
        available_potions = connection.execute(select_sql).fetchall()
        print(f"Available Potions: {available_potions}")

        for potions in available_potions:
            catalog.append({
                "sku": potions[0],
                "name": potions[1],
                "quantity": potions[2],
                "price": potions[3],
                "potion_type": potions[4]
                })

        print(f"Catalog: {catalog}")

    return [catalog]
