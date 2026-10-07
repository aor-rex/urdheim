# Urdheim python services: api, receiver, poll, snap, listen.
# One image, CMD picks the service (see docker/entrypoint.sh).
# Dokploy: one service per CMD, same image.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api brain watcher listener poster receiver schema.sql migrate.sql ./

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8091
ENTRYPOINT ["/entrypoint.sh"]
CMD ["api"]
