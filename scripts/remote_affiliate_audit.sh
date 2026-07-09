#!/bin/bash
set -euo pipefail
cd /opt/taro
git fetch origin main
git reset --hard origin/main
bash scripts/audit_stars_for_affiliate.sh
