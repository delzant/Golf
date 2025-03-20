#!/bin/bash
# bin/service.sh
# Gestion du service Eclectique

case "$1" in
  start)
    sudo systemctl start eclectique
    echo "Service eclectique démarré"
    ;;
  stop)
    sudo systemctl stop eclectique
    echo "Service eclectique arrêté"
    ;;
  restart)
    sudo systemctl restart eclectique
    echo "Service eclectique redémarré"
    ;;
  status)
    sudo systemctl status eclectique
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 1
    ;;
esac