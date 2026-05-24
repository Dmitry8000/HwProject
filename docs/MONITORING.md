# Мониторинг платформы (Prometheus + Grafana)

В проекте **уже развёрнут** мониторинг технического состояния ClickHouse — это не спортивные KPI (они в Superset), а **здоровье процесса БД** во время стрима событий.

## Схема

```text
ClickHouse :9363/metrics  ──pull──►  Prometheus :9090  ──►  Grafana :3000
                                              │
                                         alert_rules.yml
                                         (правила без Alertmanager)
```

| Инструмент | Роль |
|------------|------|
| **ClickHouse** | Отдаёт метрики на `/metrics` (порт 9363 внутри Docker) |
| **Prometheus** | Раз в 15 с забирает метрики (scrape) |
| **Grafana** | Готовый дашборд «Rugby Platform — мониторинг» |

## Как открыть

После `docker compose up -d` или `.\scripts\setup.ps1`:

| Сервис | URL | Логин |
|--------|-----|-------|
| **Grafana** | http://localhost:3000 | admin / admin |
| **Prometheus** | http://localhost:19090 | — |
| Метрики CH (raw) | http://localhost:29363/metrics | — |

### Grafana

1. Войти admin / admin.
2. Меню **Dashboards** → папка **Rugby** → **Rugby Platform — мониторинг**.

Дашборд подхватывается автоматически из `grafana/provisioning/` (перезапуск не нужен после первого `up`).

### Prometheus

- **Status → Targets** — оба target должны быть **UP**: `clickhouse`, `prometheus`.
- **Alerts** — учебные правила из `prometheus/alert_rules.yml` (уведомления никуда не шлются, только отображение).

## Что на дашборде (простыми словами)

| Панель | Зачем |
|--------|--------|
| ClickHouse / Prometheus **UP** | Жив ли сервис |
| **Память** | Не раздувается ли процесс при большом матче |
| **Интенсивность запросов** | Видно всплески при стриме и verify |
| **Running queries, HTTP, Kafka tasks** | Текущая нагрузка; задачи брокера Kafka в CH |
| **Ошибки запросов** | FailedQuery / FailedInsert за 5 минут |
| **Дисковый I/O** | Чтение/запись данных MergeTree |

Во время `python stream_match.py` обычно растут **insert/s**, **память** и **disk write** — это нормальный признак работы пайплайна.

## Проверка одной командой

```powershell
.\scripts\verify-monitoring.ps1
```

Ожидается: targets UP, в ответе метрик есть `ClickHouseMetrics_MemoryTracking`.

## Конфигурация в репозитории

| Файл | Назначение |
|------|------------|
| `clickhouse/config.d/prometheus.xml` | Включение экспорта на :9363 |
| `prometheus/prometheus.yml` | Кого опрашивать |
| `prometheus/alert_rules.yml` | Учебные alert-правила |
| `grafana/provisioning/datasources/prometheus.yml` | Источник данных Grafana |
| `grafana/provisioning/dashboards/json/rugby-platform.json` | Дашборд |

## Отличие от Superset

| | Superset | Grafana + Prometheus |
|---|----------|----------------------|
| Данные | События матча, KPI игроков | Метрики процесса ClickHouse |
| Вопрос | «Кто лучше сыграл?» | «БД жива и не падает?» |
| Источник | SQL / ClickHouse | HTTP `/metrics` |

Для защиты проекта нужны **оба**: бизнес-дашборд + мониторинг инфраструктуры.

## Что сказать на защите (30 сек)

> Мы мониторим не регбийные показатели, а платформу: Prometheus забирает метрики ClickHouse, Grafana показывает память, запросы, ошибки и I/O. При падении CH срабатывает правило ClickHouseDown во вкладке Alerts Prometheus. Спортивная аналитика — в Superset.

## Ограничения учебного стенда

- **Alertmanager не развёрнут** — алерты только видны в UI Prometheus.
- **Kafka и Zookeeper** отдельно не экспортируются; косвенно видны задачи `BackgroundMessageBrokerSchedulePoolTask` в ClickHouse.
- Порог памяти в алерте (1.5 GB) задан для демо, в production настраивается иначе.

## Changelog

| Дата | Изменение |
|------|-----------|
| 2026-05-19 | Документ и расширенный дашборд Grafana |
