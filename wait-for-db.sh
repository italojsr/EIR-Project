#!/usr/bin/env bash
set -e

HOST="${1:-db}"
PORT="${2:-1433}"
TIMEOUT="${3:-60}"

echo "Waiting for $HOST:$PORT up to ${TIMEOUT}s..."
for i in $(seq 1 "$TIMEOUT"); do
  if (echo > /dev/tcp/$HOST/$PORT) >/dev/null 2>&1; then
    echo "DB is reachable!"
    exit 0
  fi
  sleep 1
done

echo "Timed out waiting for $HOST:$PORT"
exit 1