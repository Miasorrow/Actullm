#!/bin/sh
set -e

uvicorn src.main:app --host 0.0.0.0 --port 8000 &

echo "Waiting for API..."
until curl -sSf http://127.0.0.1:8000/health >/dev/null; do
  sleep 0.5
done

echo "API up starting Nginx..."
exec nginx -g "daemon off;"