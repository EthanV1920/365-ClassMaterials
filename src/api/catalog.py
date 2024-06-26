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

    # TODO: Add External configuration in a view (put this logic in a view)
    # TODO: I need to add a limit of 6 and logic to decide on what to show
    #       probably base on customer level and type put this all in SQL

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
        available_potions = connection.execute(select_sql)
        print(f"Available Potions: {available_potions}")

        for potions in available_potions:
            catalog.append({
                "sku": potions.potion_sku,
                "name": potions.potion_name,
                "quantity": potions.potion_quantity,
                "price": potions.potion_price,
                "potion_type": potions.potion_type
                })

        print(f"Catalog: {catalog}")

    return catalog
