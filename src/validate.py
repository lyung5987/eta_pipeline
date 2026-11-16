import pandas as pd
from datetime import datetime


def empty_test(df):
    return not df.empty

def required_columns(df):
    required = {"route_id", "route_seq", "stop_seq", "stop_id", "fetched_at", "status"}
    return required.issubset(df.columns)

def null_key(df):
    keys = ["route_id", "route_seq", "stop_seq", "stop_id"]
    return not df[keys].isna().any().any()

def status_valid(df):
    valid = {"ok", "no_eta", "disabled"}
    return df["status"].isin(valid).all()

def no_future_timestamps(df):
    return (df["fetched_at"] <= pd.Timestamp.now(tz="Asia/Hong_Kong")).all()

def wait_time(df):
    if "diff" not in df.columns:
        return True          # nothing to check yet (e.g. night run)
    diff = pd.to_numeric(df["diff"], errors="coerce").dropna()
    return diff.between(0, 120).all()

critical_checks = [empty_test, required_columns, null_key, status_valid]
warning_checks = [wait_time, no_future_timestamps]

def run_checks(df):
    results = []
    run_time = datetime.now().isoformat()
    for level, checks in (("critical", critical_checks), ("warning", warning_checks)):
        for check in checks:
            try:
                passed = bool(check(df))
            except Exception as e:
                print(f"ERROR in {check.__name__}: {e}")
                passed = False
            print(f"[{level}] check: {check.__name__}, status: {'PASS' if passed else 'FAIL'}")
            results.append({
                "run_time": run_time,
                "check_name": check.__name__,
                "level": level,
                "status": "PASS" if passed else "FAIL",
            })
    return results

def can_load(results):
    return not any(i["level"] == "critical" and i["status"] == "FAIL" for i in results)


if __name__ == "__main__":
    from transform import transform
    df = transform()
    results = run_checks(df)
    print("Safe to load:", can_load(results))




    


