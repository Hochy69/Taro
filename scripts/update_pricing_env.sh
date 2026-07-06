#!/bin/bash
set -euo pipefail
cd /opt/taro

update_var() {
  local key="$1"
  local value="$2"
  if grep -q "^${key}=" .env; then
    sed -i "s/^${key}=.*/${key}=${value}/" .env
  else
    echo "${key}=${value}" >> .env
  fi
}

update_var PRICE_SINGLE_SPREAD 69
update_var PRICE_COMPATIBILITY 99

docker compose up -d backend bot celery_worker celery_beat
sleep 5
curl -sf http://localhost:8000/api/v1/pricing | python3 -c "import sys,json; p=json.load(sys.stdin); assert p['single_spread']==69 and p['compatibility']==99; print('pricing OK', p['single_spread'], p['compatibility'])"
