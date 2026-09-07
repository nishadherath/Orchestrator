"""Catalog service: returns the product listing for a category, with any
active promotions applied."""
from shared.serialize import to_wire


def _load_products(n):
    return [
        {"id": i, "name": f"Product {i}", "price": 19.99 + i, "tags": ["new", "sale"]}
        for i in range(n)
    ]


def apply_promotions(products):
    """Apply active discount rules to each product line."""
    for product in products:
        if product["id"] % 7 == 0:
            product["price"] = round(product["price"] * 0.9, 2)
    return products


def handle_request(n=1):
    products = _load_products(n * 4)
    products = apply_promotions(products)
    return to_wire({"products": products})
