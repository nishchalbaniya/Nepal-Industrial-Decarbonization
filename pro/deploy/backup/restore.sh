#!/bin/bash
# =============================================================================
# nepal_decarb_pro — restore script
# =============================================================================
# Usage:
#   ./restore.sh                           # interactive: choose backup
#   ./restore.sh /path/to/db-X.dump.gz     # restore specific backup
# =============================================================================
set -euo pipefail

BACKUP_DIR="/var/backups/nepal-decarb"
BACKUP_FILE="${1:-}"

if [ -z "$BACKUP_FILE" ]; then
    echo "Available database backups:"
    ls -lh "$BACKUP_DIR/db/" | head -20
    echo
    read -p "Enter path to backup file: " BACKUP_FILE
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: $BACKUP_FILE not found"
    exit 1
fi

echo "WARNING: This will OVERWRITE the current database."
read -p "Type 'RESTORE' to continue: " confirm
if [ "$confirm" != "RESTORE" ]; then
    echo "Aborted."
    exit 1
fi

# Stop API (so no new connections)
echo "Stopping API..."
docker stop nepal-decarb-api nepal-decarb-streamlit || true

# Drop and recreate DB
echo "Recreating database..."
docker exec nepal-decarb-db dropdb -U nepal_admin nepal_decarb --if-exists
docker exec nepal-decarb-db createdb -U nepal_admin nepal_decarb

# Restore
echo "Restoring $BACKUP_FILE..."
gunzip -c "$BACKUP_FILE" | docker exec -i nepal-decarb-db pg_restore -U nepal_admin -d nepal_decarb --no-owner --role=nepal_admin

# Restart
echo "Starting services..."
docker start nepal-decarb-api nepal-decarb-streamlit

echo "Restore complete. Verifying..."
sleep 10
curl -fsS http://localhost:8000/health && echo "API healthy"
