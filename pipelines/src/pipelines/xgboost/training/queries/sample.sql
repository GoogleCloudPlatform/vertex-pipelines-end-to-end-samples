DROP TABLE IF EXISTS `{{ preprocessing_dataset }}.{{ target_table }}`;

CREATE TABLE `{{ preprocessing_dataset }}.{{ target_table }}` AS (
SELECT
	*
FROM
	`{{ source_dataset }}.{{ source_table }}` AS t
WHERE
	MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(t))),
	{{ num_lots }}) IN {{ lots }});
