"""
Генерация синтетического матча и потоковая отправка событий в Kafka.

Примеры:
  python stream_match.py
  python stream_match.py --events 3000 --delay 0.08
  python stream_match.py --fresh
"""

from __future__ import annotations

import argparse
import json
import random
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from kafka import KafkaProducer

TOPIC = "rugby.match.events"
BOOTSTRAP_SERVERS = ["localhost:9092"]
CLICKHOUSE_HTTP = "http://localhost:28123"
MATCH_ID = 1001
TEAM_HOME = 1  # РК «Стрела»
TEAM_AWAY = 2  # РК «Ак Барс»
PLAYERS_HOME = list(range(101, 113))
PLAYERS_AWAY = list(range(201, 213))

DEFAULT_EVENTS = 2500
DEFAULT_DELAY = 0.10

EVENT_TYPES_PHASE = ["carry", "pass", "ruck", "offload", "tackle", "kick"]
SET_PIECES = ["lineout", "scrum"]


def zone_from_x(x: float) -> str:
    if x < 33:
        return "own_22"
    if x < 67:
        return "midfield"
    return "opp_22"


def pick_gain_line() -> int:
    return random.choices([1, 0, -1], weights=[55, 25, 20])[0]


def pick_outcome(event_type: str) -> str:
    if event_type == "offload":
        return random.choices(["success", "fail"], weights=[72, 28])[0]
    if event_type == "tackle":
        return random.choices(["success", "fail"], weights=[84, 16])[0]
    if event_type in ("lineout", "scrum"):
        return random.choices(["success", "fail"], weights=[78, 22])[0]
    return random.choices(["success", "fail", "turnover"], weights=[70, 20, 10])[0]


def truncate_events() -> None:
    query = urllib.parse.urlencode({"query": "TRUNCATE TABLE rugby.match_events"})
    req = urllib.request.Request(f"{CLICKHOUSE_HTTP}/?{query}", method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        resp.read()
    print("Truncated rugby.match_events")


def build_event(
    event_id: int,
    phase_number: int,
    team_id: int,
    player_id: int,
    minute: int,
    half: int,
    base_time: datetime,
) -> dict:
    event_type = random.choice(EVENT_TYPES_PHASE)
    is_set_piece = 0
    gain_line = 0

    if random.random() < 0.04:
        event_type = random.choice(SET_PIECES)
        is_set_piece = 1

    x_coord = round(random.uniform(5, 95), 1)
    y_coord = round(random.uniform(3, 65), 1)

    if event_type == "carry":
        gain_line = pick_gain_line()

    outcome = pick_outcome(event_type)
    event_time = base_time + timedelta(seconds=event_id * 2)

    return {
        "match_id": MATCH_ID,
        "event_id": event_id,
        "phase_number": phase_number,
        "team_id": team_id,
        "player_id": player_id,
        "event_type": event_type,
        "x_coord": x_coord,
        "y_coord": y_coord,
        "gain_line": gain_line,
        "outcome": outcome,
        "minute": min(minute, 80),
        "half": half,
        "is_set_piece": is_set_piece,
        "event_time": event_time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def roster_for_team(team_id: int) -> list[int]:
    return PLAYERS_HOME if team_id == TEAM_HOME else PLAYERS_AWAY


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stream synthetic rugby match events to Kafka")
    parser.add_argument(
        "--events",
        type=int,
        default=DEFAULT_EVENTS,
        help=f"Number of events (default: {DEFAULT_EVENTS})",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY,
        help=f"Delay between events in seconds (default: {DEFAULT_DELAY})",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Truncate match_events in ClickHouse before streaming",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    total = args.events
    delay_sec = args.delay

    if args.fresh:
        truncate_events()

    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        acks="all",
        retries=5,
    )

    base_time = datetime.now(timezone.utc).replace(tzinfo=None)
    event_id = 0
    phase = 1
    attacking_team = TEAM_HOME
    minute = 1
    half = 1
    progress_step = max(50, total // 20)

    eta_min = total * delay_sec / 60
    print(
        f"Streaming {total} events to '{TOPIC}' "
        f"(delay {delay_sec}s, ~{eta_min:.1f} min)..."
    )

    for _ in range(total):
        event_id += 1
        if event_id % max(1, total // 16) == 0:
            minute = min(80, minute + 5)
        if event_id == total // 2:
            half = 2
            minute = 41

        player_id = random.choice(roster_for_team(attacking_team))
        event = build_event(event_id, phase, attacking_team, player_id, minute, half, base_time)
        producer.send(TOPIC, event)

        if event["outcome"] == "turnover" or (
            event["event_type"] == "tackle"
            and event["outcome"] == "success"
            and random.random() < 0.35
        ):
            phase += 1
            attacking_team = TEAM_AWAY if attacking_team == TEAM_HOME else TEAM_HOME

        if event_id % progress_step == 0:
            print(
                f"  sent {event_id}/{total} "
                f"(phase={phase}, zone={zone_from_x(event['x_coord'])})"
            )

        time.sleep(delay_sec)

    producer.flush()
    producer.close()
    print("Done. Wait a few seconds, then: .\\scripts\\verify.ps1")


if __name__ == "__main__":
    main()
