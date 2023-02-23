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

with filtered_data as (
    SELECT
    *
    FROM `{{ source_dataset }}.{{ source_table }}`
    WHERE
         DATE({{ filter_column }}) BETWEEN
         DATE_SUB(DATE("{{ filter_start_value }}"), INTERVAL 3 MONTH) AND
         DATE_SUB(DATE("{{ filter_start_value }}"), INTERVAL 2 MONTH)
)

,mean_time as (
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
FROM filtered_data as t, mean_time as m
WHERE
    trip_miles > 0 AND fare > 0 AND fare < 1500
    {% for field in ["fare", "trip_start_timestamp", "pickup_longitude",
                "pickup_latitude", "dropoff_longitude", "dropoff_latitude","payment_type","company"] %}
        AND `{{ field }}` IS NOT NULL
    {% endfor %}
