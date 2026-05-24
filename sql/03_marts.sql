-- Витрина трёх утверждённых KPI по игроку и матчу

CREATE OR REPLACE VIEW rugby.v_player_match_metrics AS
SELECT
    match_id,
    player_id,
    player_name,
    team_id,
    multiIf(team_id = 1, 'Стрела', team_id = 2, 'Ак Барс', concat('Команда ', toString(team_id))) AS team_name,
    position,
    position_group,
    carry_attempts,
    gain_line_wins,
    if(carry_attempts > 0, round(100.0 * gain_line_wins / carry_attempts, 2), 0) AS gain_line_success_pct,
    offload_attempts,
    offload_successes,
    if(offload_attempts > 0, round(100.0 * offload_successes / offload_attempts, 2), 0) AS offload_success_pct,
    tackle_attempts,
    tackle_successes,
    if(tackle_attempts > 0, round(100.0 * tackle_successes / tackle_attempts, 2), 0) AS tackle_completion_pct
FROM
(
    SELECT
        e.match_id AS match_id,
        e.player_id AS player_id,
        p.player_name AS player_name,
        p.team_id AS team_id,
        p.position AS position,
        p.position_group AS position_group,
        countIf(e.event_type = 'carry' AND e.gain_line IN (-1, 0, 1)) AS carry_attempts,
        countIf(e.event_type = 'carry' AND e.gain_line = 1) AS gain_line_wins,
        countIf(e.event_type = 'offload') AS offload_attempts,
        countIf(e.event_type = 'offload' AND e.outcome = 'success') AS offload_successes,
        countIf(e.event_type = 'tackle') AS tackle_attempts,
        countIf(e.event_type = 'tackle' AND e.outcome = 'success') AS tackle_successes
    FROM rugby.match_events AS e
    INNER JOIN rugby.players AS p ON p.player_id = e.player_id
    GROUP BY
        e.match_id,
        e.player_id,
        p.player_name,
        p.team_id,
        p.position,
        p.position_group
);

-- Heatmap: field_zone — own_22 / midfield / opp_22 относительно команды игрока
CREATE OR REPLACE VIEW rugby.v_player_zone_activity AS
SELECT
    e.match_id,
    e.player_id,
    p.player_name,
    p.team_id AS team_id,
    multiIf(p.team_id = 1, 'Стрела', p.team_id = 2, 'Ак Барс', concat('Команда ', toString(p.team_id))) AS team_name,
    multiIf(
        e.team_id = 1, multiIf(e.x_coord < 33, 'own_22', e.x_coord < 67, 'midfield', 'opp_22'),
        e.team_id = 2, multiIf(e.x_coord > 67, 'own_22', e.x_coord < 33, 'opp_22', 'midfield'),
        'midfield'
    ) AS field_zone,
    e.event_type,
    count() AS events_count
FROM rugby.match_events AS e
INNER JOIN rugby.players AS p ON p.player_id = e.player_id
GROUP BY e.match_id, e.player_id, p.player_name, p.team_id, team_name, field_zone, e.event_type;
