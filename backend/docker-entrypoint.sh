#!/bin/sh
set -e

if [ "$RUN_MIGRATIONS" = "true" ]; then
  alembic upgrade head
fi

exec "$@"
