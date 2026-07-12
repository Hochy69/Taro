#!/bin/bash
set -euo pipefail
cd /opt/taro
echo "=== containers ==="
docker compose ps
echo "=== recent backend errors ==="
docker compose logs --tail=80 backend 2>&1 | grep -iE 'error|exception|traceback|card.of.day|/card-of-day|500' || true
echo "=== recent celery errors ==="
docker compose logs --tail=40 celery_worker 2>&1 | grep -iE 'error|exception|traceback|card' || true
echo "=== try card-of-day without auth ==="
curl -s -o /tmp/cod.json -w "HTTP %{http_code}\n" http://localhost:8000/api/v1/card-of-day || true
head -c 400 /tmp/cod.json; echo
echo "=== health ==="
curl -sf http://localhost:8000/health; echo
