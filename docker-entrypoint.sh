#!/bin/sh
set -eu

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  python -m app.core.database_bootstrap
fi

exec "$@"
