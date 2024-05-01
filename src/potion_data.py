import sqlalchemy
# from fastapi import APIRouter, Depends
# from pydantic import BaseModel
# from src.api import auth

# User python imports
from src import database as db


def add_customers(customers):
    """
    given a list of customers add them to the customer table makeing sure to
    not add duplicates
    """


def add_bottle_record(used_volume):
    """
    add a bottle record to the wholesale table showing that ml was removed
    while botteling
    """
    log_sql = sqlalchemy.text("""
                              insert into
                              wholesale_purchase_history (
                                  order_id,
                                  sku,
                                  ml_per_barrel,
                                  potion_type,
                                  price,
                                  quantity,
                                  is_red,
                                  is_green,
                                  is_blue,
                                  is_dark)
                              values (
                                  :order_id,
                                  :sku,
                                  :ml_per_barrel,
                                  :potion_type,
                                  :price,
                                  :quantity,
                                  :is_red,
                                  :is_green,
                                  :is_blue,
                                  :is_dark)
                              """)

    for i, volume in enumerate(used_volume):
        is_list = [0, 0, 0, 0]
        is_list[i] = 1
        db_request(log_sql,
                   {"order_id": -1,
                    "sku": 'bottle trueup',
                    "ml_per_barrel": -volume,
                    "potion_type": str(is_list),
                    "price": 0,
                    "quantity": 1,
                    "is_red": bool(is_list[0]),
                    "is_green": bool(is_list[1]),
                    "is_blue": bool(is_list[2]),
                    "is_dark": bool(is_list[3]),
                    })

    # return response


def add_wholesale_barrel(barrel, order_id=-2):
    """
    add a wholesale record after receiving or taking out ml
    """
    log_sql = sqlalchemy.text("""
                              insert into
                              wholesale_purchase_history (
                                  order_id,
                                  sku,
                                  ml_per_barrel,
                                  potion_type,
                                  price,
                                  quantity,
                                  is_red,
                                  is_green,
                                  is_blue,
                                  is_dark)
                              values (
                                  :order_id,
                                  :sku,
                                  :ml_per_barrel,
                                  :potion_type,
                                  :price,
                                  :quantity,
                                  :is_red,
                                  :is_green,
                                  :is_blue,
                                  :is_dark)
                              """)

    response = db_request(log_sql,
                          {"order_id": order_id,
                           "sku": barrel.sku,
                           "ml_per_barrel": barrel.ml_per_barrel,
                           "potion_type": str(barrel.potion_type),
                           "price": barrel.price,
                           "quantity": barrel.quantity,
                           "is_red": bool(barrel.potion_type[0]),
                           "is_green": bool(barrel.potion_type[1]),
                           "is_blue": bool(barrel.potion_type[2]),
                           "is_dark": bool(barrel.potion_type[3]),
                           })

    return response

def get_raw_volume():
    """
    return the raw ml for each color type
    """
    raw_sql = sqlalchemy.text("""
                              select
                                  'red' as potion_type,
                                  coalesce(sum(ml_per_barrel * quantity), 0) as raw_volume
                              from
                                  wholesale_purchase_history
                              where
                                  is_red = TRUE

                              union

                              select
                                  'green' as potion_type,
                                  coalesce(sum(ml_per_barrel * quantity), 0) as raw_volume
                              from
                                  wholesale_purchase_history
                              where
                                  is_green = TRUE

                              union

                              select
                                  'blue' as potion_type,
                                  coalesce(sum(ml_per_barrel * quantity), 0) as raw_volume
                              from
                                  wholesale_purchase_history
                              where
                                  is_blue = TRUE

                              union

                              select
                                  'dark' as potion_type,
                                  coalesce(sum(ml_per_barrel * quantity), 0) as raw_volume
                              from
                                  wholesale_purchase_history
                              where
                                  is_dark = TRUE;
                              """)

    with db.engine.begin() as connection:
        raw_volume = connection.execute(raw_sql).fetchall()
        raw_volumes = {}
        for color in raw_volume:
            raw_volumes[color[0]] = color[1]

        ordered_volumes = []
        ordered_volumes.append(raw_volumes['red'])
        ordered_volumes.append(raw_volumes['green'])
        ordered_volumes.append(raw_volumes['blue'])
        ordered_volumes.append(raw_volumes['dark'])

        return ordered_volumes


def get_gold():
    """
    return the current gold count
    """
    gold_sql = sqlalchemy.text("""
                  select
                    gold
                  from
                    global_inventory;
                  """)
    return db_request(gold_sql).scalar()


def db_request(query, options={}):
    """
    from sqltext return a cursor
    """
    with db.engine.begin() as connection:
        return connection.execute(query, options)
