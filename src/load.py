import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = "data/eta.db"

def get_conn(db_path=DB_PATH):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(db_path)


def init_db(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS fact_eta (
        route_id INTEGER NOT NULL, route_seq INTEGER NOT NULL,
        stop_seq INTEGER NOT NULL, stop_id INTEGER NOT NULL,
        fetched_at TEXT NOT NULL, generated_at TEXT,
        enabled INTEGER, status TEXT NOT NULL,
        eta_seq INTEGER NOT NULL DEFAULT 0,
        diff INTEGER, eta_timestamp TEXT,
        remarks_tc TEXT, remarks_sc TEXT, remarks_en TEXT,
        is_scheduled INTEGER, is_delayed INTEGER,
        source_file TEXT,
        UNIQUE (route_id, route_seq, stop_seq, fetched_at, eta_seq)
    );

    CREATE TABLE IF NOT EXISTS dim_stop (
        route_id   INTEGER NOT NULL,
        route_seq  INTEGER NOT NULL,
        stop_seq   INTEGER NOT NULL,
        stop_id    INTEGER NOT NULL,
        name_en    TEXT,
        name_tc    TEXT,
        name_sc    TEXT,
        PRIMARY KEY (route_id, route_seq, stop_seq)
    );

    CREATE TABLE IF NOT EXISTS validation_log (
        run_time   TEXT,
        check_name TEXT,
        level      TEXT,
        status     TEXT,
        source_file TEXT
    );

    CREATE TABLE IF NOT EXISTS processed_files (
        filename  TEXT PRIMARY KEY,
        loaded_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()


def already_loaded(conn, filename):
    cur = conn.execute("SELECT 1 FROM processed_files WHERE filename = ?", (filename,))
    return cur.fetchone() is not None


def prepare_fact(df, filename):
    out = df.copy()
    for col in ("fetched_at", "generated_at", "eta_timestamp"):
        if col in out.columns:
            out[col] = out[col].apply(lambda t: t.isoformat() if pd.notna(t) else None)
    out["enabled"] = out["enabled"].astype(int)
    out["source_file"] = filename
    cols = ["route_id", "route_seq", "stop_seq", "stop_id", "fetched_at",
            "generated_at", "enabled", "status", "eta_seq", "diff",
            "eta_timestamp", "remarks_tc", "remarks_sc", "remarks_en",
            "is_scheduled", "is_delayed", "source_file"]
    out = out.reindex(columns=cols)
    out["eta_seq"] = out["eta_seq"].fillna(0).astype(int)
    return out


def load_fact(conn, df):
    placeholders = ",".join("?" * len(df.columns))
    sql = f"INSERT OR IGNORE INTO fact_eta ({','.join(df.columns)}) VALUES ({placeholders})"
    rows = df.astype(object).where(df.notna(), None).values.tolist()

    before = conn.total_changes
    conn.executemany(sql, rows)
    inserted = conn.total_changes - before

    return inserted


def load_validation(conn, results, filename):
    log = pd.DataFrame(results)
    log["source_file"] = filename
    log.to_sql("validation_log", conn, if_exists="append", index=False)


def load_dim_stop(conn, stops_df):
    sql = """
    INSERT INTO dim_stop (route_id, route_seq, stop_seq, stop_id, name_en, name_tc, name_sc)
    VALUES (?,?,?,?,?,?,?)
    ON CONFLICT (route_id, route_seq, stop_seq) DO UPDATE SET
        stop_id = excluded.stop_id,
        name_en = COALESCE(excluded.name_en, dim_stop.name_en),
        name_tc = COALESCE(excluded.name_tc, dim_stop.name_tc),
        name_sc = COALESCE(excluded.name_sc, dim_stop.name_sc);
    """
    cols = ["route_id", "route_seq", "stop_seq", "stop_id",
            "stop_name_en", "stop_name_tc", "stop_name_sc"]
    df = (stops_df.reindex(columns=cols).drop_duplicates(subset=["route_id", "route_seq", "stop_seq"]))
    rows = df.astype(object).where(df.notna(), None).values.tolist()
    conn.executemany(sql, rows)


def run(df, results, source_path):
    filename = Path(source_path).name
    conn = get_conn()
    try:
        init_db(conn)
        if already_loaded(conn, filename):
            print(f"SKIP: {filename} already loaded")
            return
        load_validation(conn, results, filename)
        load_dim_stop(conn, df)
        n = load_fact(conn, prepare_fact(df, filename))
        conn.execute("INSERT INTO processed_files (filename) VALUES (?)", (filename,))
        conn.commit()
        print(f"Loaded {n} rows from {filename}")
    finally:
        conn.close()


if __name__ == "__main__":
    from transform import transform, latest_raw
    from validate import run_checks, can_load
    path = latest_raw()
    df = transform(path)
    results = run_checks(df)
    if can_load(results):
        run(df, results, path)
    else:
        print("Critical validation failed; not loading.")