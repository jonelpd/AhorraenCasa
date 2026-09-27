#!/usr/bin/env python3
import json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path
import requests

TOKEN_URL = "https://api.amazon.co.uk/auth/o2/token"
API_URL = "https://creatorsapi.amazon/catalog/v1"
MARKETPLACE = "www.amazon.es"
PARTNER_TAG = os.environ.get("AMAZON_PARTNER_TAG", "jonelpd-21")
CLIENT_ID = os.environ["AMAZON_CLIENT_ID"]
CLIENT_SECRET = os.environ["AMAZON_CLIENT_SECRET"]

def token():
    r = requests.post(TOKEN_URL, headers={"Content-Type":"application/json"}, data=json.dumps({
        "grant_type":"client_credentials",
        "client_id":CLIENT_ID,
        "client_secret":CLIENT_SECRET,
        "scope":"creatorsapi::default"
    }), timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]

def call(path, payload, access_token):
    headers={"Authorization":f"Bearer {access_token}","Content-Type":"application/json","x-marketplace":MARKETPLACE}
    r=requests.post(API_URL+path, headers=headers, json=payload, timeout=30)
    if r.status_code >= 400:
        raise RuntimeError(f"Amazon API {r.status_code}: {r.text[:1000]}")
    return r.json()

def normalize(item):
    price=None
    listings=(item.get("offersV2") or {}).get("listings") or []
    for listing in listings:
        p=((listing.get("price") or {}).get("money") or {})
        if p.get("amount") is not None:
            price={"amount":p["amount"],"currency":p.get("currency","EUR")}
            break
    availability=None
    if listings:
        availability=((listings[0].get("availability") or {}).get("type"))
    title=((item.get("itemInfo") or {}).get("title") or {}).get("displayValue")
    return {
        "asin":item.get("asin"),
        "title":title,
        "price":price,
        "availability":availability,
        "url":item.get("detailPageURL"),
    }

def main():
    catalog=json.load(open("data/amazon-products.json",encoding="utf-8"))
    access=token()
    output={"updatedAt":datetime.now(timezone.utc).isoformat(),"marketplace":MARKETPLACE,"products":{}}

    asins=[p["asin"] for p in catalog["products"] if p.get("asin")]
    for i in range(0,len(asins),10):
        payload={"itemIds":asins[i:i+10],"itemIdType":"ASIN","marketplace":MARKETPLACE,
                 "partnerTag":PARTNER_TAG,
                 "resources":["itemInfo.title","offersV2.listings.price","offersV2.listings.availability"]}
        data=call("/getItems",payload,access)
        for item in (data.get("itemsResult") or {}).get("items",[]):
            output["products"][item["asin"]]=normalize(item)
        time.sleep(1)

    for p in [x for x in catalog["products"] if x.get("keywords")]:
        payload={"keywords":p["keywords"],"searchIndex":p.get("searchIndex","All"),
                 "itemCount":1,"marketplace":MARKETPLACE,"partnerTag":PARTNER_TAG,
                 "resources":["itemInfo.title","offersV2.listings.price","offersV2.listings.availability"]}
        data=call("/searchItems",payload,access)
        items=(data.get("searchResult") or {}).get("items") or []
        if items:
            item=normalize(items[0])
            output["products"][p["id"]]=item
        time.sleep(1)

    Path("data").mkdir(exist_ok=True)
    Path("data/amazon-products-live.json").write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")

if __name__=="__main__":
    main()
