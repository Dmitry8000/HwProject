"""
ClickHouse → Superset: database, datasets, charts, dashboard, export ZIP.

Идемпотентно: если дашборд уже есть — обновляет чарты и фильтр «Команда».

Запуск (после init-superset.ps1 и stream_match.py):
  pip install -r scripts/requirements.txt
  python scripts/bootstrap_superset_dashboard.py
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
EXPORT_PATH = ROOT / "superset" / "exports" / "rugby_analytics.zip"

SUPERSET_URL = "http://localhost:18088"
USERNAME = "admin"
PASSWORD = "admin"
DB_NAME = "ClickHouse Rugby"
SQLALCHEMY_URI = "clickhousedb://default@clickhouse:8123/rugby"
DASHBOARD_TITLE = "Rugby Analytics — KPI игроков"

TABLE_COLUMNS = [
    "team_name",
    "player_name",
    "position",
    "carry_attempts",
    "gain_line_success_pct",
    "offload_success_pct",
    "tackle_completion_pct",
]

METRIC_GAIN = {
    "expressionType": "SIMPLE",
    "column": {"column_name": "gain_line_success_pct"},
    "aggregate": "AVG",
    "label": "Gain Line %",
}

METRICS_KPI = [
    {
        "expressionType": "SIMPLE",
        "column": {"column_name": "offload_success_pct"},
        "aggregate": "AVG",
        "label": "Offload %",
    },
    {
        "expressionType": "SIMPLE",
        "column": {"column_name": "tackle_completion_pct"},
        "aggregate": "AVG",
        "label": "Tackle %",
    },
]


def bar_params(metrics: list, row_limit: int) -> dict:
    return {
        "x_axis": "player_name",
        "metrics": metrics,
        "groupby": [],
        "row_limit": row_limit,
        "order_desc": True,
        "orientation": "vertical",
        "show_legend": True,
    }


def heatmap_params() -> dict:
    return {
        "metric": {
            "expressionType": "SIMPLE",
            "column": {"column_name": "events_count"},
            "aggregate": "SUM",
            "label": "SUM(events_count)",
        },
        "groupby": ["field_zone"],
        "column": "player_name",
        "linear_color_scheme": "greens",
        "normalize_across": "heatmap",
        "row_limit": 10000,
    }


def chart_specs(ds_metrics: int, ds_zones: int) -> list[dict]:
    return [
        {
            "slice_name": "Gain Line Success %",
            "dataset_id": ds_metrics,
            "viz_type": "echarts_timeseries_bar",
            "params": bar_params([METRIC_GAIN], 20),
        },
        {
            "slice_name": "KPI: Offload vs Tackle %",
            "dataset_id": ds_metrics,
            "viz_type": "echarts_timeseries_bar",
            "params": bar_params(METRICS_KPI, 15),
        },
        {
            "slice_name": "Таблица метрик игроков",
            "dataset_id": ds_metrics,
            "viz_type": "table",
            "params": {"all_columns": TABLE_COLUMNS, "row_limit": 50, "order_desc": True},
        },
        {
            "slice_name": "Heatmap: активность по зонам",
            "dataset_id": ds_zones,
            "viz_type": "heatmap_v2",
            "params": heatmap_params(),
        },
    ]


def login(session: requests.Session) -> None:
    resp = session.post(
        f"{SUPERSET_URL}/api/v1/security/login",
        json={"username": USERNAME, "password": PASSWORD, "provider": "db", "refresh": True},
        timeout=30,
    )
    resp.raise_for_status()
    token = resp.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}", "Referer": SUPERSET_URL})
    csrf = session.get(f"{SUPERSET_URL}/api/v1/security/csrf_token/", timeout=30)
    csrf.raise_for_status()
    session.headers["X-CSRFToken"] = csrf.json()["result"]


def wait_for_superset(session: requests.Session, attempts: int = 30) -> None:
    for _ in range(attempts):
        try:
            login(session)
            return
        except Exception:
            time.sleep(2)
    raise RuntimeError("Superset API not available. Run .\\scripts\\init-superset.ps1")


def get_database_id(session: requests.Session) -> int:
    q = json.dumps({"filters": [{"col": "database_name", "opr": "eq", "value": DB_NAME}]})
    resp = session.get(f"{SUPERSET_URL}/api/v1/database/", params={"q": q}, timeout=30)
    resp.raise_for_status()
    items = resp.json().get("result", [])
    if items:
        return items[0]["id"]

    payload = {
        "database_name": DB_NAME,
        "engine": "clickhousedb",
        "sqlalchemy_uri": SQLALCHEMY_URI,
        "expose_in_sqllab": True,
        "allow_run_async": False,
        "allow_ctas": False,
        "allow_cvas": False,
        "allow_dml": False,
    }
    resp = session.post(f"{SUPERSET_URL}/api/v1/database/", json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()["id"]


def get_or_create_dataset(session: requests.Session, database_id: int, table: str) -> int:
    q = json.dumps(
        {
            "filters": [
                {"col": "schema", "opr": "eq", "value": "rugby"},
                {"col": "table_name", "opr": "eq", "value": table},
            ]
        }
    )
    resp = session.get(f"{SUPERSET_URL}/api/v1/dataset/", params={"q": q}, timeout=30)
    resp.raise_for_status()
    items = resp.json().get("result", [])
    if items:
        return items[0]["id"]

    payload = {"database": database_id, "schema": "rugby", "table_name": table}
    resp = session.post(f"{SUPERSET_URL}/api/v1/dataset/", json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()["id"]


def refresh_dataset(session: requests.Session, dataset_id: int) -> None:
    resp = session.put(f"{SUPERSET_URL}/api/v1/dataset/{dataset_id}/refresh", timeout=60)
    resp.raise_for_status()
    print(f"  Refreshed dataset id={dataset_id}")


def find_chart(session: requests.Session, slice_name: str) -> dict | None:
    q = json.dumps({"filters": [{"col": "slice_name", "opr": "eq", "value": slice_name}]})
    resp = session.get(f"{SUPERSET_URL}/api/v1/chart/", params={"q": q}, timeout=30)
    resp.raise_for_status()
    items = resp.json().get("result", [])
    return items[0] if items else None


def upsert_chart(session: requests.Session, spec: dict) -> int:
    existing = find_chart(session, spec["slice_name"])
    payload = {
        "slice_name": spec["slice_name"],
        "viz_type": spec["viz_type"],
        "datasource_id": spec["dataset_id"],
        "datasource_type": "table",
        "params": json.dumps(spec["params"]),
    }
    if existing:
        cid = existing["id"]
        session.put(f"{SUPERSET_URL}/api/v1/chart/{cid}", json=payload, timeout=60).raise_for_status()
        print(f"  Updated chart id={cid}: {spec['slice_name']}")
        return cid

    resp = session.post(f"{SUPERSET_URL}/api/v1/chart/", json=payload, timeout=60)
    resp.raise_for_status()
    cid = resp.json()["id"]
    print(f"  Created chart id={cid}: {spec['slice_name']}")
    return cid


def find_dashboard(session: requests.Session) -> dict | None:
    q = json.dumps({"filters": [{"col": "dashboard_title", "opr": "eq", "value": DASHBOARD_TITLE}]})
    resp = session.get(f"{SUPERSET_URL}/api/v1/dashboard/", params={"q": q}, timeout=30)
    resp.raise_for_status()
    items = resp.json().get("result", [])
    return items[0] if items else None


def chart_ids_on_dashboard(dashboard: dict) -> list[int]:
    position = json.loads(dashboard.get("position_json") or "{}")
    ids: list[int] = []
    for node in position.values():
        if isinstance(node, dict) and node.get("type") == "CHART":
            cid = node.get("meta", {}).get("chartId")
            if cid:
                ids.append(int(cid))
    return sorted(ids)


def team_filter_config(ds_metrics: int, ds_zones: int, chart_ids: list[int]) -> list[dict]:
    return [
        {
            "id": f"NATIVE_FILTER-{uuid.uuid4().hex[:8]}",
            "name": "Команда",
            "filterType": "filter_select",
            "targets": [
                {"datasetId": ds_metrics, "column": {"name": "team_name"}},
                {"datasetId": ds_zones, "column": {"name": "team_name"}},
            ],
            "defaultDataMask": {"extraFormData": {}, "filterState": {}, "ownState": {}},
            "controlValues": {
                "enableEmptyFilter": False,
                "multiSelect": True,
                "searchAllOptions": False,
                "inverseSelection": False,
            },
            "cascadeParentIds": [],
            "scope": {"rootPath": ["ROOT_ID"], "excluded": []},
            "type": "NATIVE_FILTER",
            "description": "",
            "chartsInScope": chart_ids,
            "tabsInScope": [],
        }
    ]


def apply_team_filter(
    session: requests.Session,
    dashboard_id: int,
    ds_metrics: int,
    ds_zones: int,
    chart_ids: list[int],
) -> None:
    dash = session.get(f"{SUPERSET_URL}/api/v1/dashboard/{dashboard_id}", timeout=30).json()["result"]
    meta = json.loads(dash.get("json_metadata") or "{}")
    meta["show_native_filters"] = True
    meta["native_filter_configuration"] = team_filter_config(ds_metrics, ds_zones, chart_ids)
    session.put(
        f"{SUPERSET_URL}/api/v1/dashboard/{dashboard_id}",
        json={"json_metadata": json.dumps(meta)},
        timeout=60,
    ).raise_for_status()
    print(f"  Filter «Команда» on dashboard id={dashboard_id}")


def create_dashboard(session: requests.Session, chart_ids: list[int], ds_metrics: int, ds_zones: int) -> int:
    position = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
        "GRID_ID": {
            "type": "GRID",
            "id": "GRID_ID",
            "children": [f"ROW-{i}" for i in range(len(chart_ids))],
            "parents": ["ROOT_ID"],
        },
    }
    for i, cid in enumerate(chart_ids):
        row_id = f"ROW-{i}"
        chart_key = f"CHART-{cid}"
        position[row_id] = {
            "type": "ROW",
            "id": row_id,
            "children": [chart_key],
            "parents": ["ROOT_ID", "GRID_ID"],
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
        }
        position[chart_key] = {
            "type": "CHART",
            "id": chart_key,
            "children": [],
            "parents": ["ROOT_ID", "GRID_ID", row_id],
            "meta": {"width": 12, "height": 50, "chartId": cid, "sliceName": f"chart_{cid}"},
        }

    json_metadata = {
        "chart_configuration": {},
        "global_chart_configuration": {},
        "show_native_filters": True,
        "native_filter_configuration": team_filter_config(ds_metrics, ds_zones, chart_ids),
    }
    resp = session.post(
        f"{SUPERSET_URL}/api/v1/dashboard/",
        json={
            "dashboard_title": DASHBOARD_TITLE,
            "published": True,
            "json_metadata": json.dumps(json_metadata),
            "position_json": json.dumps(position),
        },
        timeout=60,
    )
    resp.raise_for_status()
    dashboard_id = resp.json()["id"]
    for cid in chart_ids:
        session.put(
            f"{SUPERSET_URL}/api/v1/chart/{cid}",
            json={"dashboards": [dashboard_id]},
            timeout=30,
        ).raise_for_status()
    return dashboard_id


def export_dashboard(session: requests.Session, dashboard_id: int) -> None:
    q = json.dumps([dashboard_id])
    resp = session.get(
        f"{SUPERSET_URL}/api/v1/dashboard/export/",
        params={"q": q},
        timeout=120,
    )
    resp.raise_for_status()
    EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    EXPORT_PATH.write_bytes(resp.content)
    print(f"Exported: {EXPORT_PATH}")


def sync_superset(session: requests.Session, *, force_new_dashboard: bool) -> int:
    db_id = get_database_id(session)
    print(f"Database id={db_id}")

    ds_metrics = get_or_create_dataset(session, db_id, "v_player_match_metrics")
    ds_zones = get_or_create_dataset(session, db_id, "v_player_zone_activity")
    refresh_dataset(session, ds_metrics)
    refresh_dataset(session, ds_zones)

    specs = chart_specs(ds_metrics, ds_zones)
    chart_ids = [upsert_chart(session, spec) for spec in specs]

    dash = None if force_new_dashboard else find_dashboard(session)
    if dash:
        dash_id = dash["id"]
        print(f"Updating existing dashboard id={dash_id}")
        on_dash = chart_ids_on_dashboard(dash)
        filter_charts = sorted(set(on_dash) | set(chart_ids))
        apply_team_filter(session, dash_id, ds_metrics, ds_zones, filter_charts)
    else:
        dash_id = create_dashboard(session, chart_ids, ds_metrics, ds_zones)
        print(f"Created dashboard id={dash_id}: {DASHBOARD_TITLE}")

    export_dashboard(session, dash_id)
    return dash_id


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap Superset dashboard for Rugby Analytics")
    parser.add_argument(
        "--new-dashboard",
        action="store_true",
        help="Always create a new dashboard (default: update existing by title)",
    )
    args = parser.parse_args()

    session = requests.Session()
    wait_for_superset(session)
    print("Logged in to Superset.")

    dash_id = sync_superset(session, force_new_dashboard=args.new_dashboard)
    print(f"Open: {SUPERSET_URL}/superset/dashboard/{dash_id}/")


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as exc:
        print(f"HTTP error: {exc.response.status_code} {exc.response.text}", file=sys.stderr)
        sys.exit(1)
