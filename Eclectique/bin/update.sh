#!/bin/bash
# bin/update.sh
# Mise à jour de l'application

cd /home/ec2-user/Golf || exit 1
echo "Récupération des dernières modifications..."
git pull

echo "Installation des dépendances..."
pip install -r requirements.txt

echo "Redémarrage du service..."
sudo systemctl restart eclectique

echo "Mise à jour terminée avec succès"