import os
import json
import datetime
from google.cloud import bigquery
import requests

PROJECT_ID = os.environ["GCP_PROJECT"]
DATASET = "raw"
TABLE = "coin_snapshots"

def fetch_coingecko():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 50,
        "page": 1,
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()

def to_rows(data, snapshot_date):
    rows = []
    for coin in data:
        rows.append({
            "snapshot_date": snapshot_date,
            "coin_id": coin["id"],
            "symbol": coin["symbol"],
            "name": coin["name"],
            "current_price": coin["current_price"],
            "market_cap": coin["market_cap"],
            "market_cap_rank": coin["market_cap_rank"],
            "total_volume": coin["total_volume"],
            "price_change_pct_24h": coin.get("price_change_percentage_24h"),
        })
    return rows

def load_to_bq(rows):
    client = bigquery.Client(project=PROJECT_ID)
    table_ref = f"{PROJECT_ID}.{DATASET}.{TABLE}"

    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        autodetect=True,
    )
    job = client.load_table_from_json(rows, table_ref, job_config=job_config)
    job.result()
    print(f"Loaded {len(rows)} rows into {table_ref}")

if __name__ == "__main__":
    snapshot_date = datetime.date.today().isoformat()
    data = fetch_coingecko()
    rows = to_rows(data, snapshot_date)
    load_to_bq(rows)