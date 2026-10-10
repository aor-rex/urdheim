# Urdheim python services: api, receiver, poll, snap, listen.
# One image, CMD picks the service (see docker/entrypoint.sh).
# Dokploy: one service per CMD, same image.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists \
    && pip install --no-cache-dir -r requirements.txt

COPY api ./api
COPY web-next/app/og-fonts ./web-next/app/og-fonts
COPY brain ./brain
COPY watcher ./watcher
COPY listener ./listener
COPY poster ./poster
COPY receiver ./receiver
COPY schema.sql migrate.sql ./

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh \
 && for s in api receiver poll snap listen; do \
      printf '#!/bin/sh\nexec /entrypoint.sh %s "$@"\n' "$s" > /usr/local/bin/$s \
      && chmod +x /usr/local/bin/$s; done
# ^ service shims: Dokploy puts the app command ("snap", "poll", ...)
#   in the executable slot on fresh deploys, bypassing image ENTRYPOINT.
#   A shim on PATH makes `snap` resolve no matter which slot it lands in.

EXPOSE 8091
ENTRYPOINT ["/entrypoint.sh"]
CMD ["api"]
