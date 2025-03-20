#!/bin/bash
# bin/logs.sh
# Visualisation des logs

case "$1" in
  app)
    sudo journalctl -u eclectique -f
    ;;
  nginx)
    sudo tail -f /var/log/nginx/error.log /var/log/nginx/access.log
    ;;
  search)
    if [ -z "$2" ]; then
      echo "Spécifiez un terme de recherche"
      exit 1
    fi
    sudo journalctl -u eclectique | grep "$2"
    ;;
  tail)
    lines=${2:-50}
    sudo journalctl -u eclectique -n "$lines"
    ;;
  *)
    echo "Usage: $0 {app|nginx|search <terme>|tail <nombre_lignes>}"
    exit 1
    ;;
esac