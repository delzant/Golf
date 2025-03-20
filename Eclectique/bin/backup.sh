#!/bin/bash
# bin/backup.sh
# Sauvegarde de la base de données

BACKUP_DIR="/home/ec2-user/Golf/Eclectique/backups"
DB_PATH="/home/ec2-user/Golf/Eclectique/eclectique.db"
DATE=$(date +%Y%m%d-%H%M%S)

mkdir -p "$BACKUP_DIR"
cp "$DB_PATH" "$BACKUP_DIR/eclectique_$DATE.db"
echo "Base de données sauvegardée dans $BACKUP_DIR/eclectique_$DATE.db"

# Suppression des sauvegardes de plus de 30 jours
find "$BACKUP_DIR" -name "eclectique_*.db" -mtime +30 -delete
echo "Nettoyage des sauvegardes anciennes terminé"