import json
import os
from datetime import datetime, timezone

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
    RunRealtimeReportRequest,
    FilterExpression,
    Filter,
)

PROPERTY_ID = os.environ["GA4_PROPERTY_ID"]
OUTPUT = "data/analytics-dashboard.json"
client = BetaAnalyticsDataClient()

def report(dimensions, metrics, date_ranges=None, dimension_filter=None, limit=20):
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name=x) for x in dimensions],
        metrics=[Metric(name=x) for x in metrics],
        date_ranges=date_ranges or [DateRange(start_date="28daysAgo", end_date="today")],
        dimension_filter=dimension_filter,
        limit=limit,
    )
    response = client.run_report(request)
    rows = []
    for row in response.rows:
        rows.append({
            "dimensions": [v.value for v in row.dimension_values],
            "metrics": [v.value for v in row.metric_values],
        })
    return rows

def realtime(dimensions, metrics, limit=20):
    request = RunRealtimeReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name=x) for x in dimensions],
        metrics=[Metric(name=x) for x in metrics],
        limit=limit,
    )
    response = client.run_realtime_report(request)
    rows = []
    for row in response.rows:
        rows.append({
            "dimensions": [v.value for v in row.dimension_values],
            "metrics": [v.value for v in row.metric_values],
        })
    return rows

def event_filter(event_name):
    return FilterExpression(
        filter=Filter(
            field_name="eventName",
            string_filter=Filter.StringFilter(value=event_name),
        )
    )

summary = report(
    [],
    ["activeUsers", "totalUsers", "sessions", "screenPageViews", "eventCount", "averageSessionDuration"],
    limit=1,
)
events = report(["eventName"], ["eventCount"], limit=100)
affiliate = report(["eventName"], ["eventCount"], dimension_filter=event_filter("affiliate_click"), limit=1)
reads = report(["eventName"], ["eventCount"], dimension_filter=event_filter("content_read"), limit=1)
top_pages = report(["pagePath"], ["screenPageViews", "activeUsers"], limit=15)
countries = report(["country"], ["activeUsers"], limit=10)
devices = report(["deviceCategory"], ["activeUsers"], limit=10)
languages = report(["language"], ["activeUsers"], limit=10)
realtime_rows = realtime(["country", "deviceCategory"], ["activeUsers"], limit=30)

def first_metric(rows, index=0, default=0):
    try:
        return float(rows[0]["metrics"][index])
    except (IndexError, ValueError):
        return default

data = {
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "period": "Últimos 28 días",
    "summary": {
        "active_users": first_metric(summary, 0),
        "total_users": first_metric(summary, 1),
        "sessions": first_metric(summary, 2),
        "page_views": first_metric(summary, 3),
        "events": first_metric(summary, 4),
        "avg_session_seconds": first_metric(summary, 5),
        "affiliate_clicks": first_metric(affiliate),
        "content_reads": first_metric(reads),
    },
    "top_pages": top_pages,
    "countries": countries,
    "devices": devices,
    "languages": languages,
    "realtime": realtime_rows,
    "events": events[:30],
}

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Dashboard data written to {OUTPUT}")
