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
         DATE(TIMESTAMP({{ filter_column }}) )BETWEEN
         DATE_SUB(DATE(CAST(filter_start_values.filter_start_value AS DATETIME)), INTERVAL 3 MONTH) AND
         DATE_SUB(DATE(filter_start_value), INTERVAL 2 MONTH)
)
-- Use the average trip_seconds as a replacement for NULL or 0 values
,mean_time AS (
    SELECT CAST(avg(duration) AS INT64) as avg_duration_seconds
    FROM filtered_data
)

SELECT
  start_station_name,
  IF(EXTRACT(dayofweek FROM start_date) BETWEEN 2 AND 6,'weekday','weekend') AS dayofweek,
    CAST(EXTRACT(HOUR FROM start_date) AS FLOAT64) AS hourofday,
    CAST( CASE WHEN duration is NULL then m.avg_duration_seconds
               WHEN duration <= 0 then m.avg_duration_seconds
               ELSE duration
               END AS FLOAT64) AS `{{ target_column }}`,
FROM filtered_data AS t, mean_time AS m
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
