#!/bin/bash
set -e
if [ -z "$1" ]; then
    echo "Usage: ./backup.sh /path/to/backups"
    exit 1
fi
BACKUP_DIR=$1
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
tar -czf "$BACKUP_DIR/backup_data_$TIMESTAMP.tar.gz" -C /opt/mansur-assistant data/ .env
echo "Backup created at $BACKUP_DIR/backup_data_$TIMESTAMP.tar.gz"
echo "WARNING: MASTER_KEY is NOT in this backup. Store it separately in a safe!"
