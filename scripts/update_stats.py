import json
import os
from datetime import date, timedelta
from pathlib import Path

import requests
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "stats.json"

SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/webmasters.readonly",
]

def env(name, required=True):
    value = os.environ.get(name, "").strip()
    if required and not value:
        raise RuntimeError(f"Falta la variable/secret {name}.")
    return value

def credentials():
    raw = env("GOOGLE_SERVICE_ACCOUNT_JSON")
    info = json.loads(raw)
    return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)

def ga_report(session, property_id, dimensions, metrics, start, end, limit=1000):
    url = f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport"
    body = {
        "dateRanges": [{"startDate": start, "endDate": end}],
        "dimensions": [{"name": x} for x in dimensions],
        "metrics": [{"name": x} for x in metrics],
        "limit": limit,
        "orderBys": [{"metric": {"metricName": metrics[0]}, "desc": True}],
    }
    r = session.post(url, json=body, timeout=60)
    r.raise_for_status()
    data = r.json()
    rows = []
    for row in data.get("rows", []):
        rows.append({
            "dimensions": [v.get("value", "") for v in row.get("dimensionValues", [])],
            "metrics": [v.get("value", "") for v in row.get("metricValues", [])],
        })
    return rows

def sc_report(session, site_url, dimensions, start, end, limit=1000):
    encoded = requests.utils.quote(site_url, safe="")
    url = f"https://www.googleapis.com/webmasters/v3/sites/{encoded}/searchAnalytics/query"
    body = {
        "startDate": start,
        "endDate": end,
        "dimensions": dimensions,
        "rowLimit": limit,
        "dataState": "final",
    }
    r = session.post(url, json=body, timeout=60)
    r.raise_for_status()
    return r.json().get("rows", [])

def main():
    property_id = env("GA4_PROPERTY_ID")
    site_url = env("SEARCH_CONSOLE_SITE_URL")
    creds = credentials()
    session = AuthorizedSession(creds)

    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=364)
    start_s, end_s = start.isoformat(), end.isoformat()

    # GA4
    ga_daily = ga_report(session, property_id, ["date"], ["activeUsers", "screenPageViews"], start_s, end_s, 1000)
    ga_pages = ga_report(session, property_id, ["pagePath"], ["screenPageViews", "activeUsers"], start_s, end_s, 1000)
    ga_countries = ga_report(session, property_id, ["country"], ["activeUsers"], start_s, end_s, 250)
    ga_sources = ga_report(session, property_id, ["sessionDefaultChannelGroup"], ["activeUsers"], start_s, end_s, 100)

    # Search Console
    sc_daily = sc_report(session, site_url, ["date"], start_s, end_s, 1000)
    sc_queries = sc_report(session, site_url, ["query"], start_s, end_s, 250)
    sc_countries = sc_report(session, site_url, ["country"], start_s, end_s, 250)
    sc_pages = sc_report(session, site_url, ["page"], start_s, end_s, 250)

    payload = {
        "generatedAt": date.today().isoformat(),
        "site": "https://ahorraencasaya.es/",
        "periodDaysAvailable": 365,
        "status": "connected",
        "ga4": {
            "daily": ga_daily,
            "pages": ga_pages,
            "countries": ga_countries,
            "sources": ga_sources,
        },
        "searchConsole": {
            "daily": sc_daily,
            "queries": sc_queries,
            "countries": sc_countries,
            "pages": sc_pages,
        },
        "monetization": {
            "amazonClicks": None,
            "solarClicks": None,
            "adsenseRevenue": None,
            "affiliateRevenue": None,
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Estadísticas actualizadas: {OUT}")

if __name__ == "__main__":
    main()
