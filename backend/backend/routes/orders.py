from fastapi import APIRouter, HTTPException
from backend.services.sheets import read_sheet, append_row
from uuid import uuid4
from datetime import datetime

router = APIRouter()


def map_products(rows):
    headers = rows[0]
    return [dict(zip(headers, row)) for row in rows[1:]]


@router.post("/")
async def create_order(data: dict):
    product_id = data.get("product_id")
    order_type = data.get("type")
    name = data.get("name")
    phone = data.get("phone")
    email = data.get("email", "")
    note = data.get("note", "")

    if not product_id or not order_type or not name or not phone:
        raise HTTPException(400, "Missing fields")

    rows = read_sheet("PRODUCTS!A1:Z")
    products = map_products(rows)

    product = next((p for p in products if p["id"] == product_id), None)

    if not product:
        raise HTTPException(404, "Product not found")

    # Validate logic
    if order_type == "preorder" and product.get("preorder") != "yes":
        raise HTTPException(400, "Product not allow preorder")

    if order_type == "buy" and int(product.get("stock", 0)) <= 0:
        raise HTTPException(400, "Out of stock")

    order_id = "O-" + str(uuid4())

    append_row("ORDERS!A1", [
        order_id,
        product_id,
        order_type,
        name,
        phone,
        email,
        note,
        "web",
        "new",
        datetime.utcnow().isoformat()
    ])

    return {"success": True, "order_id": order_id}