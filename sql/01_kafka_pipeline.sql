-- Выполнять после старта Kafka и ClickHouse (scripts/setup.ps1)

CREATE TABLE IF NOT EXISTS rugby.match_events_kafka
(
    match_id       UInt32,
    event_id       UInt32,
    phase_number   UInt16,
    team_id        UInt16,
    player_id      UInt32,
    event_type     String,
    x_coord        Float32,
    y_coord        Float32,
    gain_line      Int8,
    outcome        String,
    minute         UInt8,
    half           UInt8,
    is_set_piece   UInt8,
    event_time     DateTime
)
ENGINE = Kafka
SETTINGS
    kafka_broker_list = 'kafka:29092',
    kafka_topic_list = 'rugby.match.events',
    kafka_group_name = 'rugby_ch_consumer',
    kafka_format = 'JSONEachRow',
    kafka_num_consumers = 1,
    kafka_skip_broken_messages = 1;

CREATE MATERIALIZED VIEW IF NOT EXISTS rugby.mv_match_events_kafka_to_mt
TO rugby.match_events
AS
SELECT
    match_id,
    event_id,
    phase_number,
    team_id,
    player_id,
    event_type,
    x_coord,
    y_coord,
    multiIf(
        team_id = 1, multiIf(x_coord < 33, 'own_22', x_coord < 67, 'midfield', 'opp_22'),
        team_id = 2, multiIf(x_coord > 67, 'own_22', x_coord < 33, 'opp_22', 'midfield'),
        'midfield'
    ) AS field_zone,
    gain_line,
    outcome,
    minute,
    half,
    is_set_piece,
    event_time
FROM rugby.match_events_kafka;
