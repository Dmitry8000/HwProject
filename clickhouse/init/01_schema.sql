-- Справочники и хранилище событий (без Kafka — создаётся при первом старте volume)

CREATE DATABASE IF NOT EXISTS rugby;

CREATE TABLE IF NOT EXISTS rugby.matches
(
    match_id       UInt32,
    home_team_id   UInt16,
    away_team_id   UInt16,
    competition    LowCardinality(String),
    season         UInt16,
    venue          String,
    match_date     Date,
    home_score     UInt8,
    away_score     UInt8
)
ENGINE = MergeTree
ORDER BY (season, match_date, match_id);

CREATE TABLE IF NOT EXISTS rugby.players
(
    player_id      UInt32,
    player_name    String,
    team_id        UInt16,
    position       LowCardinality(String),
    position_group LowCardinality(String)
)
ENGINE = MergeTree
ORDER BY (team_id, player_id);

CREATE TABLE IF NOT EXISTS rugby.match_events
(
    match_id       UInt32,
    event_id       UInt32,
    phase_number   UInt16,
    team_id        UInt16,
    player_id      UInt32,
    event_type     LowCardinality(String),
    x_coord        Float32,
    y_coord        Float32,
    field_zone     LowCardinality(String),
    gain_line      Int8,
    outcome        LowCardinality(String),
    minute         UInt8,
    half           UInt8,
    is_set_piece   UInt8,
    event_time     DateTime
)
ENGINE = MergeTree
PARTITION BY match_id
ORDER BY (match_id, event_time, event_id);

-- Витрина метрик: пересчитывается запросом / MV при вставке (см. sql/03_marts.sql)
