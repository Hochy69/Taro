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
sleep 12
curl -sf http://localhost:8000/api/v1/pricing -o /tmp/pricing.json
python3 -c "import json; p=json.load(open('/tmp/pricing.json')); assert p['single_spread']==69 and p['compatibility']==99; print('pricing OK', p['single_spread'], p['compatibility'])"
