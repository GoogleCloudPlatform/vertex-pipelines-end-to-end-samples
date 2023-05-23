-- Copyright 2022 Google LLC

-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at

--     https://www.apache.org/licenses/LICENSE-2.0

-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

-- Treat "filter_start_value" as the current time, unless it is empty then use CURRENT_DATETIME() instead
-- This allows us to set the filter_start_value to a specific time for testing or for backfill
with filter_start_values as (
    SELECT 
    IF("{{ filter_start_value }}" = '', CURRENT_DATETIME(), CAST("{{ filter_start_value }}" AS DATETIME)) as filter_start_value
)
-- Ingest data between 2 and 3 months ago
,filtered_data as (
    SELECT
    *
    FROM `{{ source_dataset }}.{{ source_table }}`, filter_start_values
    WHERE
         DATE({{ filter_column }}) BETWEEN
         DATE_SUB(DATE(CAST(filter_start_values.filter_start_value as DATETIME)), INTERVAL 3 MONTH) AND
         DATE_SUB(DATE(filter_start_value), INTERVAL 2 MONTH)
)


SELECT
    start_station_name,
    starttime,
    end_station_name,
    IF(EXTRACT(DAYOFWEEK FROM starttime) = 1 OR EXTRACT(DAYOFWEEK FROM starttime) = 7, true, false) AS is_weekend,
    tripduration AS `{{ target_column }}`
FROM `bigquery-public-data.new_york_citibike.citibike_trips`
WHERE
    (tripduration IS NOT NULL OR tripduration > 0)
