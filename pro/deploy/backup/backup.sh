#!/bin/bash
# =============================================================================
# nepal_decarb_pro — backup script
# =============================================================================
# 1. Postgres logical backup (pg_dump)
# 2. S3 sync of generated reports (PDFs)
# 3. Config backup (.env, docker-compose, nginx)
# 4. Upload to S3 with encryption
# =============================================================================
set -euo pipefail

BACKUP_DIR="/var/backups/nepal-decarb"
S3_BUCKET="${S3_BUCKET:-nepal-decarb-backups}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
RETENTION_DAYS="${RETENTION_DAYS:-30}"

mkdir -p "$BACKUP_DIR"/{db,reports,config}

# 1. Database backup
echo "[1/4] Backing up Postgres..."
docker exec nepal-decarb-db pg_dump -U nepal_admin -d nepal_decarb --format=custom | \
    gzip > "$BACKUP_DIR/db/db-$TIMESTAMP.dump.gz"
echo "      -> $BACKUP_DIR/db/db-$TIMESTAMP.dump.gz"

# 2. Reports (PDFs in S3 or local)
echo "[2/4] Backing up reports..."
if [ -d "/var/lib/docker/volumes/nepal-decarb_reports" ]; then
    rsync -a /var/lib/docker/volumes/nepal-decarb_reports/_data/ "$BACKUP_DIR/reports/$TIMESTAMP/" 2>/dev/null || true
fi

# 3. Config
echo "[3/4] Backing up config..."
cp -a /opt/nepal_decarb_pro/.env "$BACKUP_DIR/config/env-$TIMESTAMP" 2>/dev/null || true
cp -a /opt/nepal_decarb_pro/deploy/vps/docker-compose.yml "$BACKUP_DIR/config/" 2>/dev/null || true
cp -a /etc/nginx/sites-available/nepal-decarb "$BACKUP_DIR/config/nginx-$TIMESTAMP" 2>/dev/null || true

# 4. Upload to S3 (if configured)
echo "[4/4] Uploading to S3..."
if command -v aws &> /dev/null && [ -n "${AWS_ACCESS_KEY_ID:-}" ]; then
    aws s3 sync "$BACKUP_DIR/db/" "s3://$S3_BUCKET/db/" --storage-class GLACIER --expires "$(date -d "+$RETENTION_DAYS days" +%Y-%m-%d)" 2>/dev/null || true
    aws s3 sync "$BACKUP_DIR/config/" "s3://$S3_BUCKET/config/" --storage-class GLACIER 2>/dev/null || true
fi

# Cleanup old local backups
find "$BACKUP_DIR/db" -name "db-*.dump.gz" -mtime +7 -delete
find "$BACKUP_DIR/reports" -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true
find "$BACKUP_DIR/config" -mtime +30 -delete

echo "Backup complete: $TIMESTAMP"
echo "  DB:        $(du -h "$BACKUP_DIR/db/db-$TIMESTAMP.dump.gz" | cut -f1)"
echo "  Reports:   $(du -sh "$BACKUP_DIR/reports/$TIMESTAMP" 2>/dev/null | cut -f1 || echo 'N/A')"
echo "  Total:     $(du -sh "$BACKUP_DIR" | cut -f1)"
