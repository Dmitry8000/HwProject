# Apache Superset — подключение и дашборды


**Superset** — веб-приложение для графиков и дашбордов поверх баз данных.  

В проекте — **регбийная аналитика** из ClickHouse.

---

## Дашборд

После `stream_match.py --fresh` и bootstrap:

```powershell

pip install -r scripts\requirements.txt

python scripts\bootstrap_superset_dashboard.py

```

Скрипт **идемпотентный**: если дашборд **«Rugby Analytics — KPI игроков»** уже есть — обновляет чарты и фильтр «Команда», иначе создаёт новый. Экспорт: `superset/exports/rugby_analytics.zip`.

---
## Датасеты и чарты

| Dataset | VIEW | Чарты |

|---------|------|--------|

| `v_player_match_metrics` | KPI игроков | Gain Line %, Offload vs Tackle, таблица |

| `v_player_zone_activity` | Зоны + count | Heatmap |



| Фильтр на дашборде | Колонка |

|--------------------|---------|

| **Команда** | `team_name` (Стрела / Ак Барс) |


Heatmap: [HEATMAP.md](HEATMAP.md)

---


