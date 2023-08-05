-- If preprocessing dataset don't exist, create it
CREATE SCHEMA IF NOT EXISTS `{{ preprocessing_dataset }}`
  OPTIONS (
    description = 'Preprocessing Dataset',
    location = '{{ dataset_region }}');

-- We recreate the ingestion table every time the pipeline run,
-- so we need to drop the generated in the  previous run
DROP TABLE IF EXISTS `{{ preprocessing_dataset }}.{{ ingested_table }}`;

CREATE TABLE `{{ preprocessing_dataset }}.{{ ingested_table }}` AS (
WITH filter_start_values AS (
SELECT
	IF('{{ filter_start_value }}' = '',
	CURRENT_DATETIME(),
	CAST('{{ filter_start_value }}' AS DATETIME)) AS filter_start_value
)
-- Ingest data between 2 and 3 months ago
,filtered_data AS (
    SELECT
    *
    FROM `{{ source_dataset }}.{{ source_table }}`, filter_start_values
    WHERE
         DATE({{ filter_column }}) BETWEEN
         DATE_SUB(DATE(CAST(filter_start_values.filter_start_value AS DATETIME)), INTERVAL 3 MONTH) AND
         DATE_SUB(DATE(filter_start_value), INTERVAL 2 MONTH)
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
    (fare + tips + tolls + extras) AS `{{ target_column }}`,
FROM filtered_data AS t, mean_time AS m
WHERE
    trip_miles > 0 AND fare > 0 AND fare < 1500
    {% for field in ['fare', 'trip_start_timestamp', 'pickup_longitude',
                'pickup_latitude', 'dropoff_longitude', 'dropoff_latitude','payment_type','company'] %}
        AND `{{ field }}` IS NOT NULL
    {% endfor %}
);

-- Drop and creation of train, testing and validations tables
DROP TABLE IF EXISTS `{{ preprocessing_dataset }}.{{ train_table }}`;

CREATE TABLE `{{ preprocessing_dataset }}.{{ train_table }}` AS (
SELECT
	*
FROM
	`{{ preprocessing_dataset }}.{{ ingested_table }}` AS t
WHERE
	MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(t))),
	10) IN (0, 1, 2, 3, 4, 5, 6, 7));

DROP TABLE IF EXISTS `{{ preprocessing_dataset }}.{{ validation_table }}`;

CREATE TABLE `{{ preprocessing_dataset }}.{{ validation_table }}` AS (
SELECT
	*
FROM
	`{{ preprocessing_dataset }}.{{ ingested_table }}` AS t
WHERE
	MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(t))),
	10) IN (8));

DROP TABLE IF EXISTS `{{ preprocessing_dataset }}.{{ test_table }}`;

CREATE TABLE `{{ preprocessing_dataset }}.{{ test_table }}` AS (
SELECT
	*
FROM
	`{{ preprocessing_dataset }}.{{ ingested_table }}` AS t
WHERE
	MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(t))),
	10) IN (9));
