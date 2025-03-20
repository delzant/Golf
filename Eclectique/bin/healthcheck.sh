#!/bin/bash
# bin/healthcheck.sh
# Vérification de l'état du système

echo "=== Vérification de l'état du service ==="
sudo systemctl status eclectique --no-pager

echo -e "\n=== Espace disque ==="
df -h /

echo -e "\n=== Utilisation mémoire ==="
free -m

echo -e "\n=== Processus Gunicorn ==="
ps aux | grep gunicorn

echo -e "\n=== Test de connectivité locale ==="
curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 || echo "Échec de connexion"