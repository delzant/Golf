# Documentation Technique EclectiqueManager

## 1. Présentation générale

`EclectiqueManager` est un programme Python qui permet de gérer une compétition de golf de type "Eclectique". Cette compétition se déroule en plusieurs manches sur un même parcours, et consiste à retenir le meilleur score réalisé par chaque joueur sur chaque trou au fil des manches.

### Fonctionnalités principales
- Importation des résultats depuis des fichiers Excel
- Importation des joueurs depuis des fichiers HTML
- Stockage des données dans une base SQLite
- Calcul du classement Eclectique
- Gestion des flights (groupes de départ)
- Affichage formaté des résultats
- Export des classements et flights aux formats PDF et HTML
- Interface web interactive via Flask

## 2. Architecture technique

### 2.1 Structure de la base de données

#### Tables principales
1. **joueurs**: Informations des golfeurs
   - `id_national`: Identifiant fédéral (clé primaire)
   - `nom`: Nom complet du joueur
   - `genre`: Genre du joueur
   - `homeclub`: Club d'appartenance
   - `age`: Âge du joueur
   - `handicap`: Handicap du joueur

2. **manches**: Informations des compétitions
   - `id`: Identifiant unique (clé primaire, auto-incrémenté)
   - `date`: Date de la manche
   - `nom_competition`: Nom de la compétition
   - `tee_depart`: Départ utilisé
   - `couleur_depart`: Couleur des départs
   - `nom_fichier`: Nom du fichier Excel source

3. **scores**: Scores des joueurs
   - `id_joueur`: Identifiant du joueur
   - `id_manche`: Identifiant de la manche
   - `trou`: Numéro du trou (1-18)
   - `score`: Nombre de coups réalisés
   - Clé primaire composée: (id_joueur, id_manche, trou)

4. **trous**: Caractéristiques du parcours
   - `trou`: Numéro du trou (clé primaire)
   - `par`: Nombre de coups standard pour le trou
   - `handicap_index`: Index de difficulté du trou

5. **corrections**: Corrections manuelles de scores
   - `id_joueur`: Identifiant du joueur
   - `trou`: Numéro du trou
   - `score`: Score corrigé
   - `note`: Justification de la correction
   - `date_correction`: Date de la correction
   - Clé primaire composée: (id_joueur, trou)

#### Tables pour les flights
6. **flights_departs**: Groupes de départs
   - `id`: Identifiant unique (clé primaire, auto-incrémenté)
   - `date`: Date des départs
   - `strategy`: Stratégie de répartition
   - `random_factor`: Facteur d'aléatoire (%)

7. **flights**: Groupes de départs
   - `id`: Identifiant unique (clé primaire, auto-incrémenté)
   - `id_depart`: Référence vers flights_departs
   - `nom`: Nom du flight (ex: A1, R2)
   - `type`: Type de parcours (aller/retour)

8. **flights_joueurs**: Joueurs par flight
   - `id`: Identifiant unique (clé primaire, auto-incrémenté)
   - `id_flight`: Référence vers flights
   - `nom`: Nom du joueur
   - `handicap`: Handicap du joueur

### 2.2 Dépendances logicielles

- Python 3.6 ou supérieur
- Bibliothèques:
  - pandas (lecture des fichiers Excel)
  - sqlite3 (gestion de la BDD)
  - fpdf2 (export PDF)
  - Flask (interface web)
  - Jinja2 (templating)
  - beautifulsoup4 (parsing HTML)
  - numpy (calculs)

## 3. Utilisation locale

### 3.1 Installation et configuration

```bash
# Cloner le dépôt
git clone <URL-du-repo>
cd Golf

# Installer les dépendances
pip install -r requirements.txt
```

### 3.2 Variables d'environnement

- `ECLECTIQUE_DB`: Chemin vers la base de données SQLite (défaut: "eclectique.db")

### 3.3 Options de ligne de commande

```
python eclectique_manager.py [options]
```

Options disponibles:
- `--db FICHIER`: Chemin vers la base de données
- `--dir DOSSIER`: Répertoire contenant les fichiers Excel à importer
- `--joueur ID`: Afficher le détail pour un joueur spécifique
- `--verbose`, `-v`: Mode verbeux
- `--reset`: Supprimer et recréer la base de données
- `--pars VAL`: Configurer les pars des trous (format: 1=4,2=3,3=5,...)
- `--pdf FICHIER`: Exporter le classement au format PDF
- `--import-html FICHIER`: Importer les joueurs depuis un fichier HTML

### 3.4 Exemples d'utilisation

```bash
# Configurer les pars du parcours
python eclectique_manager.py --pars 1=4,2=3,3=5,4=4,5=3,6=4,7=5,8=4,9=4,10=4,11=4,12=3,13=5,14=4,15=3,16=5,17=5,18=4

# Importer des fichiers Excel
python eclectique_manager.py --dir ./data

# Afficher le classement Eclectique
python eclectique_manager.py

# Voir les détails d'un joueur
python eclectique_manager.py --joueur 123456

# Lancer l'interface web
python app.py
```

## 4. Déploiement sur AWS

### 4.1 Architecture de déploiement

- Instance EC2 (Amazon Linux 2023)
- Nginx comme serveur proxy inverse
- Gunicorn comme serveur WSGI
- DNS configuré pour un sous-domaine

### 4.2 Installation sur EC2

```bash
# Mise à jour du système
sudo dnf update -y
sudo dnf install -y python3 python3-pip git nginx

# Cloner le dépôt
git clone <URL-du-repo> /home/ec2-user/Golf
cd /home/ec2-user/Golf

# Installer les dépendances
pip install -r requirements.txt
pip install gunicorn
```

### 4.3 Configuration de Gunicorn comme service

```bash
# Créer le fichier de service
sudo nano /etc/systemd/system/eclectique.service
```

Contenu du fichier service:
```ini
[Unit]
Description=Gunicorn service for Eclectique
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=/home/ec2-user/Golf/Eclectique
Environment="PATH=/home/ec2-user/Golf/venv/bin"
ExecStart=/home/ec2-user/.local/bin/gunicorn --workers 2 --bind 127.0.0.1:5000 app:app

[Install]
WantedBy=multi-user.target
```

Activer et démarrer le service:
```bash
sudo systemctl enable eclectique
sudo systemctl start eclectique
```

### 4.4 Configuration de Nginx

```bash
sudo nano /etc/nginx/conf.d/eclectique.conf
```

Contenu:
```nginx
server {
    listen 80;
    server_name eclectique.it-xpert.be;
    
    location / {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

Redémarrer Nginx:
```bash
sudo systemctl enable nginx
sudo systemctl restart nginx
```

### 4.5 Configuration HTTPS (optionnel)

```bash
sudo dnf install -y certbot python3-certbot-nginx
sudo certbot --nginx -d eclectique.it-xpert.be
```

## 5. Maintenance et exploitation

### 5.1 Scripts de maintenance

Des scripts utilitaires sont disponibles dans le répertoire `bin/`:

```bash
# Gestion du service
./bin/service.sh {start|stop|restart|status}

# Visualisation des logs
./bin/logs.sh {app|nginx|search <terme>|tail <nombre_lignes>}

# Sauvegarde de la base de données
./bin/backup.sh

# Mise à jour de l'application
./bin/update.sh

# Vérification de l'état du système
./bin/healthcheck.sh
```

Rendre les scripts exécutables:
```bash
chmod +x /home/ec2-user/Golf/Eclectique/bin/*.sh
```

### 5.2 Surveillance des logs

Pour visualiser les logs de l'application:

```bash
# Afficher les logs en temps réel
sudo journalctl -u eclectique -f

# Afficher les dernières entrées (50 lignes)
sudo journalctl -u eclectique -n 50

# Rechercher des messages spécifiques
sudo journalctl -u eclectique | grep "mot-clé"

# Utiliser le script de logs
./bin/logs.sh app
```

Les logs contiennent toutes les informations générées par la méthode `self.log()` utilisée dans le code, ainsi que les erreurs et messages produits par Gunicorn.

Logs Nginx:
```bash
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### 5.3 Backups et restauration

#### Backup manuel
```bash
# Sauvegarder la BDD
cp /home/ec2-user/Golf/Eclectique/eclectique.db /home/ec2-user/backups/eclectique_$(date +%Y%m%d).db

# Utiliser le script de backup
./bin/backup.sh
```

#### Backup automatique
Configurer une tâche cron:
```bash
crontab -e
# Ajouter la ligne:
0 2 * * * /home/ec2-user/Golf/Eclectique/bin/backup.sh
```

#### Restauration
```bash
cp /home/ec2-user/backups/eclectique_20240320.db /home/ec2-user/Golf/Eclectique/eclectique.db
sudo systemctl restart eclectique
```

### 5.4 Mise à jour de l'application

```bash
cd /home/ec2-user/Golf
git pull
pip install -r requirements.txt
sudo systemctl restart eclectique

# Ou utiliser le script:
./bin/update.sh
```

### 5.5 Résolution des problèmes courants

#### L'application ne démarre pas
```bash
sudo systemctl status eclectique
sudo journalctl -u eclectique -n 50
./bin/logs.sh tail 100
```

#### Erreur 502 Bad Gateway
```bash
# Vérifier que Gunicorn fonctionne
ps aux | grep gunicorn
curl http://127.0.0.1:5000

# Vérifier les logs Nginx
sudo tail -f /var/log/nginx/error.log
```

#### Problèmes de permission
```bash
sudo chown -R ec2-user:ec2-user /home/ec2-user/Golf
```

#### Erreurs de fonction SQL dans SQLite
Si vous rencontrez des erreurs comme "no such function: CONCAT":
- Vérifiez que les requêtes SQL utilisent la syntaxe SQLite correcte
- Remplacez les fonctions MySQL/PostgreSQL par des équivalents SQLite
- Exemple: remplacer `CONCAT(a, b)` par `a || b`

## 6. Structure du code

### 6.1 eclectique_manager.py
Classe principale avec toutes les méthodes nécessaires:
- `__init__`: Initialisation et connexion BDD
- `init_db`: Création des tables
- `import_manche`: Import d'une manche Excel
- `get_classement_eclectique`: Calcul du classement
- `importer_joueurs_html`: Import des joueurs HTML
- Etc.

### 6.2 app.py
Application web Flask:
- `index()`: Page d'accueil avec classement
- `details_joueur(id_joueur)`: API JSON détails
- `admin()`: Interface d'administration
- `flights_management()`: Interface flights
- Etc.

### 6.3 Templates HTML
- `index.html`: Classement Eclectique
- `admin.html`: Administration
- `flights.html`: Gestion flights
- `manche.html`: Classement par manche
- Etc.

## 7. Interface Web

### 7.1 Endpoints principaux
- `/`: Classement Eclectique
- `/details-joueur/<id_joueur>`: API JSON détails
- `/admin`: Administration
- `/flights`: Gestion des flights
- `/manches`: Liste des manches
- `/manche/<id_manche>`: Classement d'une manche

### 7.2 Endpoints API
- `/api/joueurs`: Liste des joueurs
- `/api/correction/<id_joueur>`: Gestion corrections
- `/api/import-html`: Import joueurs HTML
- `/api/save-flights`: Sauvegarde des flights

## 8. Limitations et améliorations possibles

- Pas d'authentification pour l'interface admin
- Gestion limitée des erreurs dans les fichiers Excel
- Possibilité d'ajouter d'autres formats d'export
- Pas de gestion des handicaps pour scores nets
- Pas de statistiques avancées par joueur/trou
- Ajout d'un contrôle d'accès admin
- API plus complète pour intégration externe
- Gestion de plusieurs parcours différents