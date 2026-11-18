import json
import pandas as pd
from pathlib import Path
from config import RAW_DIR, ROOT

def latest_raw(folder=RAW_DIR):
    files = sorted(Path(folder).glob("eta_run_*.json"))
    if not files:
        raise FileNotFoundError(f"No eta_run_*.json files in {folder}")
    return files[-1]


def load_raw(path):
    with open(path, encoding="utf-8") as f: #utf-8 preserve chinese chars
        return json.load(f)

def flatten(records):
    rows = []
    for rec in records:
        resp = rec["response"]
        data = resp["data"]
        base = {
            "fetched_at": rec["fetched_at"],
            "generated_at": resp["generated_timestamp"],
            "route_id": rec["route_id"],
            "route_seq": rec["route_seq"],
            "stop_seq": rec["stop_seq"],
            "stop_id": rec["stop_id"],
            "enabled": data["enabled"],
            "stop_name_en": rec.get("stop_name_en"),
            "stop_name_tc": rec.get("stop_name_tc"),
            "stop_name_sc": rec.get("stop_name_sc"),
        }
        etas = data.get("eta", [])
        if not etas:
            rows.append({**base, "status": "no_eta"})
        else:
            for e in etas:
                rows.append({**base, "status": "ok", **e})
    return pd.DataFrame(rows)

def transform(path = None):
    if path is None:
        path = latest_raw()
    df = flatten(load_raw(path))
    df["fetched_at"] = pd.to_datetime(df["fetched_at"], utc=True).dt.tz_convert("Asia/Hong_Kong")
    df["generated_at"] = pd.to_datetime(df["generated_at"], utc=True).dt.tz_convert("Asia/Hong_Kong")
    if "timestamp" in df.columns:
        df = df.rename(columns={"timestamp": "eta_timestamp"})
        df["eta_timestamp"] = pd.to_datetime(df["eta_timestamp"], utc=True).dt.tz_convert("Asia/Hong_Kong")
    if "remarks_en" in df.columns:
        df["is_scheduled"] = (df["remarks_en"] == "Scheduled").astype(int)
        df["is_delayed"] = (df["remarks_en"] == "Delayed").astype(int)
    return df


if __name__ == "__main__":
    df = transform()
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    df.to_csv(f"{ROOT}/data/processed/eta_flat.csv", index=False, encoding="utf-8-sig")
    print(df.shape)