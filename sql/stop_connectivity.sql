
-- Top 20 stops by the number of distinct routes serving them.
-- This measures scheduled route connectivity, not passenger demand.
-- Stops are grouped by GTFS stop_id, so individual platforms
-- may appear separately.

SELECT
    s.stop_id,
    s.stop_name,
    COUNT(DISTINCT t.route_id) AS distinct_route_count,
    COUNT(DISTINCT st.trip_id) AS scheduled_trip_count,
    COUNT(*) AS scheduled_stop_events
FROM read_parquet('data/silver/stops.parquet') AS s
JOIN read_parquet('data/silver/stop_times.parquet') AS st
    ON s.stop_id = st.stop_id
JOIN read_parquet('data/silver/trips.parquet') AS t
    ON st.trip_id = t.trip_id
GROUP BY
    s.stop_id,
    s.stop_name
ORDER BY
    distinct_route_count DESC,
    scheduled_stop_events DESC,
    s.stop_id
LIMIT 20;
