import sqlite3, pandas as pd
from pathlib import Path
from config import DB_PATH, ROOT

views = ["v_wait_by_hour", "v_no_service_by_hour", "v_wait_by_stop",
         "v_validation", "v_freshness"]
out = ROOT / "data" / "exports"
out.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
conn.executescript(Path(ROOT / "sql" / "views.sql").read_text(encoding="utf-8"))
for v in views:
    pd.read_sql(f"SELECT * FROM {v}", conn).to_csv(out / f"{v}.csv", index=False, encoding="utf-8-sig")
conn.close()