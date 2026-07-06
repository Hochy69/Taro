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

update_var PRICE_SINGLE_SPREAD 59
update_var PRICE_COMPATIBILITY 79
update_var PRICE_SUBSCRIPTION_1M 399
update_var PRICE_SUBSCRIPTION_3M 999
update_var PRICE_SUBSCRIPTION_6M 1799
update_var PRICE_SPREAD_PACK_3 149
update_var PRICE_SPREAD_PACK_5 229

docker compose up -d --build backend bot frontend celery_worker celery_beat
sleep 45
curl -sf http://localhost:8000/api/v1/pricing -o /tmp/pricing.json
python3 -c "
import json
p = json.load(open('/tmp/pricing.json'))
assert p['single_spread'] == 59
assert p['compatibility'] == 79
assert p['love_bundle']['stars'] == 110
plans = {x['plan']: x['stars'] for x in p['plans']}
assert plans['month_1'] == 399
assert plans['month_3'] == 999
assert plans['month_6'] == 1799
print('pricing OK', p['single_spread'], p['compatibility'], p['love_bundle']['stars'])
"
