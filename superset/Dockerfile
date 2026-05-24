FROM apache/superset:latest

USER root
RUN uv pip install --python /app/.venv/bin/python --no-cache "clickhouse-connect==0.7.19" \
 && uv pip install --python /app/.venv/bin/python --no-cache "SQLAlchemy==1.4.54"

USER superset
