# Развёртывание и запуск

Пошаговая инструкция для **Windows** (PowerShell).  
---

## Предварительные требования

| Компонент | Версия / примечание |
|-----------|---------------------|
| **Docker Desktop** | Запущен |
| **Python** | 3.10+ (producer + bootstrap Superset) |
| **Порты** | 9092, 3000, 18088, 19090, 28123, 29000, 29363 |

```powershell
docker version
docker compose version
```

---

## Первый запуск

```powershell
cd C:\OtusChHomework\Project
.\scripts\setup.ps1
pip install -r producer\requirements.txt -r scripts\requirements.txt
cd producer
python stream_match.py --fresh
cd ..
python scripts\bootstrap_superset_dashboard.py
```


## URL и учётные записи

| Сервис | URL | Логин |
|--------|-----|-------|
| ClickHouse HTTP | http://localhost:28123 | default, без пароля |
| Superset | http://localhost:18088 | admin / admin |
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:19090 | — |
| Kafka | localhost:9092 | — |

---

## Повторный запуск

### Поднять стек

```powershell
docker compose up -d
```

### Новый матч

```powershell
cd producer
python stream_match.py --fresh
```

Superset: **F5** на дашборде. Bootstrap не нужен.

### Обновить Superset (чарты, фильтр, датасеты)

```powershell
python scripts\bootstrap_superset_dashboard.py
```

### Полный сброс

```powershell
docker compose down -v
```

## Остановка

```powershell
docker compose down
```

