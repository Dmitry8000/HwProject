# Мониторинг платформы (Prometheus + Grafana)


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
- **Alerts** — правила из `prometheus/alert_rules.yml` (уведомления никуда не шлются, только отображение).

## Что на дашборде

| Панель | Зачем |
|--------|--------|
| ClickHouse / Prometheus **UP** | Жив ли сервис |
| **Память** | Не раздувается ли процесс при большом матче |
| **Интенсивность запросов** | Видно всплески при стриме и verify |
| **Running queries, HTTP, Kafka tasks** | Текущая нагрузка; задачи брокера Kafka в CH |
| **Ошибки запросов** | FailedQuery / FailedInsert за 5 минут |
| **Дисковый I/O** | Чтение/запись данных MergeTree |

## Конфигурация в репозитории

| Файл | Назначение |
|------|------------|
| `clickhouse/config.d/prometheus.xml` | Включение экспорта на :9363 |
| `prometheus/prometheus.yml` | Кого опрашивать |
| `prometheus/alert_rules.yml` | Учебные alert-правила |
| `grafana/provisioning/datasources/prometheus.yml` | Источник данных Grafana |
| `grafana/provisioning/dashboards/json/rugby-platform.json` | Дашборд |






