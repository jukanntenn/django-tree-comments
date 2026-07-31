#!/usr/bin/env bash
# e2e database setup: start PG, run migrations, seed demo data.
# Usage: bash e2e/setup-db.sh
set -euo pipefail

echo "[e2e] Starting PostgreSQL..."
docker compose -f e2e/docker-compose.yml up -d postgres

echo "[e2e] Waiting for PG to be ready..."
for i in $(seq 1 30); do
  if docker exec treecomments-e2e-postgres pg_isready -U treecomments >/dev/null 2>&1; then
    echo "[e2e] PG is ready"
    break
  fi
  sleep 1
done

echo "[e2e] Running migrate + seed..."
cd examples/default
TREE_COMMENTS_DB_BACKEND=postgres \
TREE_COMMENTS_DB_NAME=tree_comments_e2e \
TREE_COMMENTS_DB_PORT=5433 \
uv run python manage.py migrate
TREE_COMMENTS_DB_BACKEND=postgres \
TREE_COMMENTS_DB_NAME=tree_comments_e2e \
TREE_COMMENTS_DB_PORT=5433 \
uv run python manage.py seed_comments
cd ../..

echo "[e2e] Ready. Run tests: cd e2e && npm test"
