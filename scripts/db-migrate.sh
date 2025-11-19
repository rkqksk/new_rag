#!/usr/bin/env bash
# Database migration script

set -e

ACTION=${1:-upgrade}

echo "🗄️  Database Migration"
echo "====================="
echo "Action: $ACTION"
echo ""

source .venv/bin/activate

case $ACTION in
  upgrade)
    echo "Running migrations..."
    alembic upgrade head
    echo "✅ Migrations complete"
    ;;
  downgrade)
    echo "Reverting last migration..."
    alembic downgrade -1
    echo "✅ Migration reverted"
    ;;
  create)
    if [ -z "$2" ]; then
      echo "Usage: ./scripts/db-migrate.sh create 'migration message'"
      exit 1
    fi
    echo "Creating migration: $2"
    alembic revision --autogenerate -m "$2"
    echo "✅ Migration created"
    ;;
  history)
    alembic history
    ;;
  current)
    alembic current
    ;;
  *)
    echo "Usage: ./scripts/db-migrate.sh {upgrade|downgrade|create|history|current}"
    exit 1
    ;;
esac
