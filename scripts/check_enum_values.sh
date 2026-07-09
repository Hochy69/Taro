#!/bin/bash
cd /opt/taro
docker compose exec -T postgres psql -U tarot -d tarot_db -c "SELECT unnest(enum_range(NULL::notificationtype));"
