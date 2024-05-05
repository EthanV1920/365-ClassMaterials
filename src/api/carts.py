import sqlalchemy
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum

# User python imports
from src import database as db
from src import potion_data as data

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"


class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"


@router.get("/search/", tags=["search"])
def search_orders(
        customer_name: str = "",
        potion_sku: str = "",
        search_page: str = "",
        sort_col: search_sort_options = search_sort_options.timestamp,
        sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku,
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
                {
                    "line_item_id": 1,
                    "item_sku": "1 oblivion potion",
                    "customer_name": "Scaramouche",
                    "line_item_total": 50,
                    "timestamp": "2021-01-01T00:00:00Z",
                }
        ],
    }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int


@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Get the customers that visited the shop today then prints them in the
    render log and passes them to the database.
    """
    print(customers)

    # INFO: add a way to link to other categories
    log_sql = sqlalchemy.text("""
                              insert into
                                  customer_visits(
                                      visit_id,
                                      customer_name,
                                      character_class,
                                      level)
                              values (
                                  :visit_id,
                                  :name,
                                  :class,
                                  :level);
                              """)

    customer_data = []
    for customer in customers:
        insert_statement = {
                'visit_id': visit_id,
                'name': customer.customer_name,
                'class': customer.character_class,
                'level': customer.level}

        customer_data.append(insert_statement)

    with db.engine.begin() as connection:
        connection.execute(log_sql, customer_data)

    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """
    Create a new cart in the table and return the id to the buyer.
    """
    # TODO: Add a carts table and cart_item table and then link them together
    # cart item key potion_id + cart_id
    # INFO: You can write "default_values" in order to use default
    cart_sql = sqlalchemy.text("""
                               insert into
                                   carts (sku,
                                          quantity)
                               values
                                   ('nosku', 0)
                               returning
                                   cart_id;
                               """)

    with db.engine.begin() as connection:
        # TODO: Change to scalar(1)
        cart_id = connection.execute(cart_sql).scalar()

    print(f"""New cart made for {Customer} cart_id: {cart_id}""")

    return {"cart_id": cart_id}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    add_item = sqlalchemy.text("""
                               insert into carts(cart_id,
                                                 sku,
                                                 quantity)
                               values(:cart_id,
                                      :sku,
                                      :quantity);
                               delete from carts
                               where
                                    cart_id = :cart_id
                                    and sku = 'nosku'
                                    and quantity = 0
                               """)
    line_values = {'cart_id': cart_id,
                   'sku': item_sku,
                   'quantity': cart_item.quantity}

    with db.engine.begin() as connection:
        result = connection.execute(add_item, line_values)
        print(f"Added {cart_item.quantity} sku: {item_sku} to cart: {cart_id}")

    return result


class CartCheckout(BaseModel):
    payment: str


@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """
    calculate final price and then finish sale
    """
    # TODO: Clean this up; better separation of entities
    # I need to separate out meaning of tables
    # TODO: Combine the statements and remove the union
    checkout_sql = sqlalchemy.text("""
                                   insert into potion_purchase_history(cart_id, sku, quantity)
                                   select
                                       cart_id,
                                       sku,
                                       -quantity
                                   from
                                       carts
                                   where
                                       cart_id = :cart_id ;

                                   select
                                       sum(quantity) as potion_count
                                   from
                                       carts
                                   where
                                   cart_id = :cart_id
                                   union
                                   select
                                       sum(potion_inventory.price * carts.quantity) as potion_price
                                   from
                                       carts
                                       join potion_inventory on potion_inventory.sku = carts.sku;


                                   """)

    checkout_values = {'cart_id': cart_id}

    with db.engine.begin() as connection:
        # TODO: Change fetchall() to first and then reference by name
        checkout_info = connection.execute(checkout_sql, checkout_values).fetchall()
        potion_count = checkout_info[0][0]
        cost = checkout_info[1][0]
        print(f"cart: {cart_id} checked out with {potion_count} potion(s) costing {cost} gold")

    data.set_gold(cost)

    return {"total_potions_bought": potion_count, "total_gold_paid": cost}


# Adding SQL execution
# with db.engine.begin() as connection:
#    result = connection.execute(sqlalchemy.text())
