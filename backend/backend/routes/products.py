from fastapi import APIRouter, HTTPException, Query
from backend.services.sheets import read_sheet
from cachetools import TTLCache

router = APIRouter()

# Cache toàn bộ products
cache = TTLCache(maxsize=1, ttl=60)


def map_products(rows):
    headers = rows[0]
    return [
        dict(zip(headers, row))
        for row in rows[1:]
    ]


def get_cached_products():
    if "products" in cache:
        return cache["products"]

    rows = read_sheet("PRODUCTS!A1:Z")
    products = map_products(rows)

    # Normalize + filter active
    normalized = []
    for p in products:
        if p.get("active", "").lower() != "true":
            continue

        normalized.append({
            **p,
            "category": (p.get("category") or "").lower(),
            "subcategory": (p.get("subcategory") or "").lower(),
        })

    cache["products"] = normalized
    return normalized


@router.get("/")
async def get_products(
    category: str | None = Query(default=None),
    subcategory: str | None = Query(default=None)
):
    products = get_cached_products()

    # Filter theo category
    if category:
        category = category.lower()
        products = [p for p in products if p.get("category") == category]

    # Filter theo subcategory
    if subcategory:
        subcategory = subcategory.lower()
        products = [p for p in products if p.get("subcategory") == subcategory]

    return products

@router.get("/categories/all")
async def get_categories():
    products = get_cached_products()

    result = {}
    for p in products:
        cat = p.get("category")
        sub = p.get("subcategory")

        if not cat:
            continue

        if cat not in result:
            result[cat] = set()

        if sub:
            result[cat].add(sub)

    return {
        cat: list(subs)
        for cat, subs in result.items()
    }

@router.get("/{product_id}")
async def get_product(product_id: str):
    products = get_cached_products()

    for p in products:
        if p.get("id") == product_id:
            return p

    raise HTTPException(status_code=404, detail="Product not found")