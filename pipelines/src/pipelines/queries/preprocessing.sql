-- Create dataset if it doesn't exist
CREATE SCHEMA IF NOT EXISTS `{{ dataset }}`
  OPTIONS (
    description = 'Chicago Taxi Trips with Turbo Template',
    location = '{{ location }}');

-- Create (or replace) table with preprocessed data
DROP TABLE IF EXISTS `{{ dataset }}.{{ table }}`;
CREATE TABLE `{{ dataset }}.{{ table }}` AS (
WITH start_timestamps AS (
SELECT
	IF('{{ start_timestamp }}' = '',
	CURRENT_DATETIME(),
	CAST('{{ start_timestamp }}' AS DATETIME)) AS start_timestamp
)
-- Ingest data between 2 and 3 months ago
,filtered_data AS (
    SELECT
    *
    FROM `{{ source }}`, start_timestamps
    WHERE
         DATE(trip_start_timestamp) BETWEEN
         DATE_SUB(DATE(CAST(start_timestamps.start_timestamp AS DATETIME)), INTERVAL 3 MONTH) AND
         DATE_SUB(DATE(start_timestamp), INTERVAL 2 MONTH)
)
-- Use the average trip_seconds as a replacement for NULL or 0 values
,mean_time AS (
    SELECT CAST(avg(trip_seconds) AS INT64) as avg_trip_seconds
    FROM filtered_data
)

SELECT
    CAST(EXTRACT(DAYOFWEEK FROM trip_start_timestamp) AS FLOAT64) AS dayofweek,
    CAST(EXTRACT(HOUR FROM trip_start_timestamp) AS FLOAT64) AS hourofday,
    ST_DISTANCE(
        ST_GEOGPOINT(pickup_longitude, pickup_latitude),
        ST_GEOGPOINT(dropoff_longitude, dropoff_latitude)) AS trip_distance,
    trip_miles,
    CAST( CASE WHEN trip_seconds is NULL then m.avg_trip_seconds
               WHEN trip_seconds <= 0 then m.avg_trip_seconds
               ELSE trip_seconds
               END AS FLOAT64) AS trip_seconds,
    payment_type,
    company,
    {% if label %}
    (fare + tips + tolls + extras) AS `{{ label }}`,
    {% endif %}
FROM filtered_data AS t, mean_time AS m
WHERE
    trip_miles > 0 AND fare > 0 AND fare < 1500
    {% for field in [
        'fare', 'trip_start_timestamp', 'pickup_longitude', 'pickup_latitude',
        'dropoff_longitude', 'dropoff_latitude','payment_type','company' ] %}
        AND `{{ field }}` IS NOT NULL
    {% endfor %}
);
