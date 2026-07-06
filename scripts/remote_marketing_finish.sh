#!/bin/bash
set -euo pipefail
cd /opt/taro
git fetch origin main
git reset --hard origin/main
bash scripts/apply_marketing_enums.sh
curl -sf http://localhost:8000/health && echo " backend ok"
bash scripts/check_marketing_pushes.sh
bash scripts/full_check_vps.sh
