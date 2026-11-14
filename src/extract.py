import requests
import time
import json
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = "https://data.etagmb.gov.hk"
TARGET_ROUTE_ID = 2004825  # 11M

def get_json(path, retries=3, timeout=10):
    url = f"{BASE_URL}{path}"
    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt+1} failed for {url}: {e}")
            time.sleep(2 ** attempt)
    return None

def save_raw(name, payload):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    with open(f"data/raw/{name}_{ts}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)

def fetch_eta(route_id, route_seq, stop_seq, stop_id):
    payload = get_json(f"/eta/route-stop/{route_id}/{route_seq}/{stop_seq}")
    if payload is None:
        print(f"FAILED: {route_id} seq{route_seq} stop{stop_seq}")
        return None
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "route_id": route_id, "route_seq": route_seq,
        "stop_seq": stop_seq, "stop_id": stop_id,
        "response": payload,
    }

def run():
    records = []
    for route_seq in (1, 2):
        stops = get_json(f"/route-stop/{TARGET_ROUTE_ID}/{route_seq}")
        if stops is None:
            print(f"No stop list for direction {route_seq}")
            continue
        for s in stops["data"]["route_stops"]:
            rec = fetch_eta(TARGET_ROUTE_ID, route_seq, s["stop_seq"], s["stop_id"])
            if rec is not None:
                records.append(rec)
            time.sleep(0.5)
    save_raw("eta_run", records)

if __name__ == "__main__":
    run()








