CREATE VIEW IF NOT EXISTS v_wait_by_hour AS
SELECT
  strftime('%H', substr(fetched_at, 1, 19)) AS hour_hk,
  COUNT(*) AS eta_rows,
  ROUND(AVG(diff), 2) AS avg_wait_min,
  ROUND(100.0 * AVG(is_scheduled), 1) AS pct_scheduled,
  ROUND(100.0 * AVG(is_delayed), 1) AS pct_delayed
FROM fact_eta
WHERE status = 'ok'
GROUP BY hour_hk;


CREATE VIEW IF NOT EXISTS v_no_service_by_hour AS
SELECT
  strftime('%H', substr(fetched_at, 1, 19)) AS hour_hk,
  ROUND(100.0 * SUM(status = 'no_eta') / COUNT(*), 1) AS pct_no_eta
FROM fact_eta
GROUP BY hour_hk;


CREATE VIEW IF NOT EXISTS v_wait_by_stop AS
SELECT d.route_seq, d.stop_seq, d.name_en,
       ROUND(AVG(f.diff), 2) AS avg_wait_min,
       COUNT(*) AS eta_rows
FROM fact_eta f
JOIN dim_stop d USING (route_id, route_seq, stop_seq)
WHERE f.status = 'ok'
GROUP BY d.route_seq, d.stop_seq, d.name_en;


CREATE VIEW IF NOT EXISTS v_validation AS
SELECT check_name, level,
       ROUND(100.0 * SUM(status = 'PASS') / COUNT(*), 1) AS pass_pct,
       COUNT(*) AS runs
FROM validation_log
GROUP BY check_name, level;


CREATE VIEW IF NOT EXISTS v_freshness AS
SELECT MAX(fetched_at) AS last_fetch,
       COUNT(DISTINCT source_file) AS runs_loaded,
       COUNT(*) AS total_rows
FROM fact_eta;