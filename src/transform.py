import json
import pandas as pd
from pathlib import Path

def latest_raw(folder="data/raw"):
    files = sorted(Path(folder).glob("eta_run_*.json"))
    return files[-1]

data_path = latest_raw()

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
        }
        etas = data.get("eta", [])
        if not etas:
            rows.append({**base, "status": "no_eta"})
        else:
            for e in etas:
                rows.append({**base, "status": "ok", **e})
    return pd.DataFrame(rows)

def transform(path = data_path):
    df = flatten(load_raw(path))
    if "diff" in df.columns:
        df["fetched_at"] = pd.to_datetime(df["fetched_at"], utc=True).dt.tz_convert("Asia/Hong_Kong")
        df["generated_at"] = pd.to_datetime(df["generated_at"], utc=True).dt.tz_convert("Asia/Hong_Kong")
    return df


if __name__ == "__main__":
    df = transform()
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    df.to_csv("data/processed/eta_flat.csv", index=False, encoding="utf-8-sig")
    print(df.shape)