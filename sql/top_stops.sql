-- Top 20 stops by scheduled stop events
-- Each stop_times row represents one scheduled stop event.

SELECT
    s.stop_id,
    s.stop_name,
    COUNT(*) AS scheduled_stop_count,
    COUNT(DISTINCT st.trip_id) AS unique_trips
FROM read_parquet('data/silver/stop_times.parquet') AS st
JOIN read_parquet('data/silver/stops.parquet') AS s
    ON st.stop_id = s.stop_id
GROUP BY
    s.stop_id,
    s.stop_name
ORDER BY
    scheduled_stop_count DESC,
    s.stop_id
LIMIT 20;