#!/bin/bash
cd /opt/taro
docker compose exec -T postgres psql -U tarot -d tarot_db -c "SELECT id, notification_type FROM notifications LIMIT 5;"
