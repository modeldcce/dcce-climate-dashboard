#!/usr/bin/env python3
"""Fetch GA4 month-to-date and lifetime unique visitors/page views for GitHub Pages.
Requires GA4_PROPERTY_ID and GA4_SERVICE_ACCOUNT_JSON as environment variables.
"""
import json
import os
from datetime import datetime, date
from pathlib import Path
from zoneinfo import ZoneInfo

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Metric, RunReportRequest
from google.oauth2 import service_account

TIMEZONE = ZoneInfo('Asia/Bangkok')
START_DATE = os.getenv('GA4_START_DATE', '2026-10-16')
PROPERTY_ID = os.environ['GA4_PROPERTY_ID']  # GA4 property ID, NOT stream ID
CREDENTIALS = json.loads(os.environ['GA4_SERVICE_ACCOUNT_JSON'])
OUTPUT = Path(os.getenv('STATS_OUTPUT', 'visitor_stats.json'))


def query(client, start, end):
    response = client.run_report(RunReportRequest(
        property=f'properties/{PROPERTY_ID}',
        date_ranges=[DateRange(start_date=start, end_date=end)],
        metrics=[Metric(name='totalUsers'), Metric(name='screenPageViews')],
    ))
    if not response.rows:
        return {'unique_visitors': 0, 'page_views': 0}
    values = response.rows[0].metric_values
    return {'unique_visitors': int(values[0].value), 'page_views': int(values[1].value)}


def main():
    now = datetime.now(TIMEZONE)
    start = date.fromisoformat(START_DATE)
    if start > now.date():
        raise ValueError('GA4_START_DATE is in the future')
    creds = service_account.Credentials.from_service_account_info(
        CREDENTIALS, scopes=['https://www.googleapis.com/auth/analytics.readonly'])
    client = BetaAnalyticsDataClient(credentials=creds)
    first_this_month = now.date().replace(day=1)
    month_start = max(start, first_this_month)
    data = {
        'timezone': 'Asia/Bangkok',
        'start_date': start.isoformat(),
        'updated_at_th': now.strftime('%Y-%m-%d %H:%M:%S %z'),
        'month': {'period': now.strftime('%Y-%m'), **query(client, month_start.isoformat(), now.date().isoformat())},
        'lifetime': query(client, start.isoformat(), now.date().isoformat()),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Updated:', OUTPUT, '| period:', data['month']['period'])


if __name__ == '__main__':
    main()
