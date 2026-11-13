import requests
import time
from datetime import datetime, timezone
import json


BASE_URL = "https://data.etagmb.gov.hk/"
target_route_id = 2004825

def get_json(path, retries = 3, time_out = 10):
    url = f"{BASE_URL}{path}"
    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=time_out)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            print(f"Attempt failed for {url}:{e}")
            time.sleep(2**attempt)
    return None


def fetch_and_save_eta(route_id, route_seq, stop_id):
    payload = get_json(f"/eta/route-stop/{route_id}/{stop_id}")
    if payload is None:
        print(f"FAILED: {route_id} {stop_id}")
        return
    record = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "route_id": route_id,
        "route_seq": route_seq,
        "stop_id": stop_id,
        "response": payload,
    }
    return record

stop_id_list = []
stop_detail = get_json(f"/route-stop/{target_route_id}/1")
for i in stop_detail["data"]["route_stops"]:
    stop_id_list.append(i["stop_id"])

records = []
for i in stop_id_list:
    records.append(fetch_and_save_eta(target_route_id, 1, stop_id_list[i]))
    records.append(fetch_and_save_eta(target_route_id,2,stop_id_list[i]))
save_raw(f"eta_run", records)









