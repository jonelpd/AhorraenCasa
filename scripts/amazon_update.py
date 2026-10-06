#!/usr/bin/env python3
import json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path
import requests

TOKEN_URL = "https://api.amazon.co.uk/auth/o2/token"
API_URL = "https://creatorsapi.amazon/catalog/v1"
MARKETPLACE = "www.amazon.es"
PARTNER_TAG = os.environ.get("AMAZON_PARTNER_TAG", "jonelpd-21")
CLIENT_ID = os.environ.get("AMAZON_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("AMAZON_CLIENT_SECRET", "").strip()

if not CLIENT_ID or not CLIENT_SECRET:
    raise SystemExit(
        "Amazon Creators API no está configurada. Añade AMAZON_CLIENT_ID y "
        "AMAZON_CLIENT_SECRET como GitHub Actions secrets para activar la "
        "actualización automática del catálogo."
    )

def token():
    r = requests.post(
        TOKEN_URL,
        headers={"Content-Type": "application/json"},
        json={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": "creatorsapi::default",
        },
        timeout=30,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"Amazon token {r.status_code}: {r.text[:800]}")
    return r.json()["access_token"]

def call(path, payload, access_token):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "x-marketplace": MARKETPLACE,
    }
    r = requests.post(API_URL + path, headers=headers, json=payload, timeout=30)
    if r.status_code >= 400:
        raise RuntimeError(f"Amazon API {r.status_code}: {r.text[:1000]}")
    return r.json()

def lowest_new_offer(item):
    listings = (item.get("offersV2") or {}).get("listings") or []
    candidates = []
    for listing in listings:
        condition = ((listing.get("condition") or {}).get("value") or "").upper()
        if condition and condition not in {"NEW", "NUEVO"}:
            continue
        money = ((listing.get("price") or {}).get("money") or {})
        amount = money.get("amount")
        if isinstance(amount, (int, float)):
            candidates.append({
                "amount": amount,
                "currency": money.get("currency", "EUR"),
            })
    return min(candidates, key=lambda x: x["amount"]) if candidates else None

def normalize(item):
    title = ((item.get("itemInfo") or {}).get("title") or {}).get("displayValue")
    availability = None
    listings = (item.get("offersV2") or {}).get("listings") or []
    if listings:
        availability = ((listings[0].get("availability") or {}).get("type"))
    return {
        "asin": item.get("asin"),
        "title": title,
        "price": lowest_new_offer(item),
        "availability": availability,
        "url": item.get("detailPageURL"),
    }

def search_cheapest(query, search_index, access_token):
    payload = {
        "keywords": query,
        "searchIndex": search_index or "All",
        "itemCount": 10,
        "marketplace": MARKETPLACE,
        "partnerTag": PARTNER_TAG,
        "availability": "Available",
        "condition": "New",
        "sortBy": "Price:LowToHigh",
        "resources": [
            "itemInfo.title",
            "offersV2.listings.price",
            "offersV2.listings.availability",
            "offersV2.listings.condition",
        ],
    }
    data = call("/searchItems", payload, access_token)
    items = (data.get("searchResult") or {}).get("items") or []
    candidates = []
    for item in items:
        price = lowest_new_offer(item)
        if price is not None:
            normalized = normalize(item)
            normalized["_price_value"] = price["amount"]
            candidates.append(normalized)
    if not candidates:
        return None
    candidates.sort(key=lambda x: x["_price_value"])
    result = candidates[0]
    result.pop("_price_value", None)
    return result

def main():
    catalog = json.loads(Path("data/amazon-products.json").read_text(encoding="utf-8"))
    access = token()
    output = {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "marketplace": MARKETPLACE,
        "products": {},
    }

    products = catalog.get("products", [])

    # Exact products: refresh their current offer without replacing the ASIN.
    asins = [p["asin"] for p in products if p.get("asin")]
    asin_to_id = {p["asin"]: p["id"] for p in products if p.get("asin") and p.get("id")}
    for i in range(0, len(asins), 10):
        payload = {
            "itemIds": asins[i:i+10],
            "itemIdType": "ASIN",
            "marketplace": MARKETPLACE,
            "partnerTag": PARTNER_TAG,
            "condition": "New",
            "resources": [
                "itemInfo.title",
                "offersV2.listings.price",
                "offersV2.listings.availability",
                "offersV2.listings.condition",
            ],
        }
        data = call("/getItems", payload, access)
        for item in (data.get("itemsResult") or {}).get("items", []):
            key = asin_to_id.get(item.get("asin"), item.get("asin"))
            if key:
                output["products"][key] = normalize(item)
        time.sleep(1)

    # Discovery products: search up to 10 current results and select the
    # lowest-priced new available result. No price history or alerts are kept.
    for p in products:
        query = p.get("keywords") or p.get("search")
        if not query:
            continue
        result = search_cheapest(query, p.get("searchIndex", "All"), access)
        if result:
            output["products"][p["id"]] = result
        time.sleep(1)

    Path("data").mkdir(exist_ok=True)
    Path("data/amazon-products-live.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

if __name__ == "__main__":
    main()
