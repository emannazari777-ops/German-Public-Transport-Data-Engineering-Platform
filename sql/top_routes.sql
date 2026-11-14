-- Top 20 routes by scheduled trips
-- Counts trips in the GTFS dataset, not daily departures.

SELECT
    r.route_id,
    r.route_short_name,
    r.route_long_name,
    r.route_type,
    COUNT(t.trip_id) AS scheduled_trip_count
FROM read_parquet('data/silver/routes.parquet') AS r
JOIN read_parquet('data/silver/trips.parquet') AS t
    ON r.route_id = t.route_id
GROUP BY
    r.route_id,
    r.route_short_name,
    r.route_long_name,
    r.route_type
ORDER BY
    scheduled_trip_count DESC,
    r.route_id
LIMIT 20;