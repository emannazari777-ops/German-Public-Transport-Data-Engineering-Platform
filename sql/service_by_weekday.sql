
-- Scheduled trips by weekday across the full GTFS calendar period.
-- Regular calendar schedules are combined with date exceptions.
-- Each active trip is counted once for each operating date.
-- These are scheduled trips, not actual completed journeys.

WITH date_range AS (
    SELECT
        CAST(
            strptime(MIN(start_date), '%Y%m%d')
            AS DATE
        ) AS first_date,
        CAST(
            strptime(MAX(end_date), '%Y%m%d')
            AS DATE
        ) AS last_date
    FROM read_parquet('data/silver/calendar.parquet')
),

service_dates AS (
    SELECT
        CAST(g.day AS DATE) AS service_date
    FROM date_range,
    generate_series(
        first_date,
        last_date,
        INTERVAL 1 DAY
    ) AS g(day)
),

regular_services AS (
    SELECT
        c.service_id,
        d.service_date
    FROM read_parquet('data/silver/calendar.parquet') AS c
    CROSS JOIN service_dates AS d
    WHERE
        d.service_date BETWEEN
            CAST(strptime(c.start_date, '%Y%m%d') AS DATE)
            AND
            CAST(strptime(c.end_date, '%Y%m%d') AS DATE)
        AND CASE dayofweek(d.service_date)
            WHEN 0 THEN c.sunday
            WHEN 1 THEN c.monday
            WHEN 2 THEN c.tuesday
            WHEN 3 THEN c.wednesday
            WHEN 4 THEN c.thursday
            WHEN 5 THEN c.friday
            WHEN 6 THEN c.saturday
        END = 1
),

exceptions AS (
    SELECT
        service_id,
        CAST(strptime(date, '%Y%m%d') AS DATE)
            AS service_date,
        exception_type
    FROM read_parquet('data/silver/calendar_dates.parquet')
),

active_services AS (
    SELECT
        r.service_id,
        r.service_date
    FROM regular_services AS r
    WHERE NOT EXISTS (
        SELECT 1
        FROM exceptions AS e
        WHERE
            e.service_id = r.service_id
            AND e.service_date = r.service_date
    )

    UNION ALL

    SELECT
        e.service_id,
        e.service_date
    FROM exceptions AS e
    WHERE e.exception_type = 1
),

trips_per_service AS (
    SELECT
        service_id,
        COUNT(*) AS trip_count
    FROM read_parquet('data/silver/trips.parquet')
    GROUP BY service_id
)

SELECT
    dayofweek(a.service_date) AS weekday_number,
    dayname(a.service_date) AS weekday_name,
    COUNT(DISTINCT a.service_date) AS dates_with_service,
    SUM(t.trip_count) AS total_scheduled_trips,
    ROUND(
        SUM(t.trip_count) * 1.0
        / COUNT(DISTINCT a.service_date),
        2
    ) AS average_trips_per_active_date
FROM active_services AS a
JOIN trips_per_service AS t
    ON a.service_id = t.service_id
GROUP BY
    weekday_number,
    weekday_name
ORDER BY
    CASE weekday_number
        WHEN 0 THEN 7
        ELSE weekday_number
    END;
