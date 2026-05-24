-- Проверка после стрима событий

SELECT 'match_events rows' AS check_name, count() AS value FROM rugby.match_events;

SELECT
    player_name,
    carry_attempts,
    gain_line_success_pct,
    offload_attempts,
    offload_success_pct,
    tackle_attempts,
    tackle_completion_pct
FROM rugby.v_player_match_metrics
WHERE carry_attempts > 0 OR offload_attempts > 0 OR tackle_attempts > 0
ORDER BY gain_line_success_pct DESC
LIMIT 10;

SELECT
    field_zone,
    sum(events_count) AS total_events
FROM rugby.v_player_zone_activity
GROUP BY field_zone
ORDER BY field_zone;
