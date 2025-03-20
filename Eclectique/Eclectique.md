# Documentation du programme EclectiqueManager

## Présentation générale

`EclectiqueManager` est un programme Python qui permet de gérer une compétition de golf de type "Eclectique". Cette compétition se déroule en plusieurs manches sur un même parcours, et consiste à retenir le meilleur score réalisé par chaque joueur sur chaque trou au fil des manches.

Le programme gère:
- L'importation des résultats depuis des fichiers Excel
- L'importation des joueurs depuis des fichiers HTML
- Le stockage des données dans une base SQLite
- Le calcul du classement Eclectique
- La gestion des flights (groupes de départ)
- L'affichage formaté des résultats
- L'export des classements et flights aux formats PDF et HTML
- Une interface web interactive via Flask

## Base de données

Le programme utilise SQLite et crée plusieurs tables:

### Tables principales

1. **joueurs**: Stocke les informations des golfeurs
   - `id_national`: Identifiant fédéral du joueur (clé primaire)
   - `nom`: Nom complet du joueur
   - `genre`: Genre du joueur
   - `homeclub`: Club d'appartenance du joueur
   - `age`: Âge du joueur
   - `handicap`: Handicap du joueur

2. **manches**: Enregistre les informations de chaque compétition
   - `id`: Identifiant unique de la manche (clé primaire, auto-incrémenté)
   - `date`: Date de la manche
   - `nom_competition`: Nom de la compétition
   - `tee_depart`: Départ utilisé
   - `couleur_depart`: Couleur des départs
   - `nom_fichier`: Nom du fichier Excel source

3. **scores**: Contient les scores réalisés par les joueurs
   - `id_joueur`: Identifiant du joueur
   - `id_manche`: Identifiant de la manche
   - `trou`: Numéro du trou (1-18)
   - `score`: Nombre de coups réalisés
   - Clé primaire composée: (id_joueur, id_manche, trou)

4. **trous**: Définit les caractéristiques du parcours
   - `trou`: Numéro du trou (clé primaire)
   - `par`: Nombre de coups standard pour le trou
   - `handicap_index`: Index de difficulté du trou (non utilisé actuellement)

5. **corrections**: Stocke les corrections manuelles de scores
   - `id_joueur`: Identifiant du joueur
   - `trou`: Numéro du trou
   - `score`: Score corrigé
   - `note`: Justification de la correction
   - `date_correction`: Date de la correction
   - Clé primaire composée: (id_joueur, trou)

### Tables pour les flights

6. **flights_departs**: Informations générales sur un groupe de départs
   - `id`: Identifiant unique (clé primaire, auto-incrémenté)
   - `date`: Date des départs
   - `strategy`: Stratégie utilisée pour la répartition (simple, kmeans, mixed)
   - `random_factor`: Facteur d'aléatoire (pourcentage)

7. **flights**: Définit les groupes de départs
   - `id`: Identifiant unique (clé primaire, auto-incrémenté)
   - `id_depart`: Référence vers flights_departs
   - `nom`: Nom du flight (ex: A1, R2)
   - `type`: Type de parcours (aller ou retour)

8. **flights_joueurs**: Joueurs assignés à chaque flight
   - `id`: Identifiant unique (clé primaire, auto-incrémenté)
   - `id_flight`: Référence vers flights
   - `nom`: Nom du joueur
   - `handicap`: Handicap du joueur

## Fonctionnalités principales

### Importation des données

#### Importation de scores

Les scores sont importés depuis des fichiers Excel avec une structure spécifique:
- La première ligne contient les headers des colonnes: Tee de départ, Genre, Couleur, Date, Nom de la compétition, ID fédéral, Nom, Club, Handicap, Age
- Puis les scores pour chaque trou joué (colonnes 10 à 27)

Le programme:
- Analyse les fichiers Excel de manière robuste
- Détecte automatiquement les colonnes et leur signification
- Évite les doublons en vérifiant si un joueur a déjà des scores pour une date spécifique
- Gère les erreurs et les fichiers corrompus

#### Importation de joueurs

Le programme peut importer des joueurs depuis un fichier HTML de départ et les répartir automatiquement entre l'aller (trous 1-9) et le retour (trous 10-18). La répartition se fait selon:

- L'historique des manches du joueur (aller pour ceux qui ont joué le retour précédemment et vice-versa)
- Un équilibrage des groupes si aucun historique n'est disponible

### Gestion des flights

Le programme inclut un système complet de gestion des flights (groupes de départ) avec:

- Importation des joueurs depuis un fichier HTML
- Répartition des joueurs entre aller et retour
- Ajustement manuel des listes
- Génération automatique des flights selon trois stratégies:
  - Simple: Par ordre de handicap avec facteur aléatoire
  - K-means: Groupes par niveau avec facteur aléatoire
  - Mixte: Équilibrage des niveaux dans chaque flight
- Règles de validation (max 4 joueurs par flight, max 1 "rabbit" par flight, etc.)
- Export des flights en PDF pour affichage au club

### Calcul du classement

Le classement Eclectique consiste à:
- Pour chaque joueur, retenir son meilleur score sur chaque trou parmi toutes les manches jouées
- Additionner ces meilleurs scores pour obtenir le total Eclectique
- Trier les joueurs par score total (du plus petit au plus grand)
- Gérer les ex-aequo (si deux joueurs ont le même score, ils obtiennent le même classement)

Le programme gère également:
- Les classements par manche (aller, retour, 18 trous)
- Les classements par catégorie (hommes, femmes, rabbits)
- Les statistiques d'eagles et de birdies

### Corrections manuelles

Un système de corrections manuelles permet:
- Corriger les scores d'un joueur sur des trous spécifiques
- Ajouter une note explicative pour chaque correction
- Tracer les corrections avec horodatage
- Prendre en compte ces corrections dans le classement Eclectique

### Affichage des résultats

L'affichage des résultats est formaté sous forme de tableau comprenant:
- Les informations des joueurs (Nom, Handicap, Nombre de participations)
- La ligne des pars pour chaque trou
- Les meilleurs scores par trou pour chaque joueur (avec code couleur)
- Le total Eclectique

Les codes couleurs utilisés pour les scores sont:
- **Rouge** : Eagle ou mieux (2 coups ou plus sous le par)
- **Jaune** : Birdie (1 coup sous le par)
- **Bleu** : Par
- **Sans couleur** (noir) : Au-dessus du par

Un affichage détaillé par joueur est également disponible, montrant:
- Les meilleurs scores par trou et la date à laquelle ils ont été réalisés
- La liste de toutes les manches auxquelles le joueur a participé
- Le détail des scores pour chaque manche

### Export PDF

Le programme permet d'exporter au format PDF:
- Le classement Eclectique complet
- Le classement d'une manche spécifique
- Les feuilles de départ (flights)

Caractéristiques:
- Tableaux formatés avec les mêmes codes couleurs que l'affichage console
- Les participations supérieures à 5 sont mises en évidence avec un fond vert
- Format optimisé pour tenir sur une page A4
- Gestion automatique des sauts de page pour les longs classements
- Mise en évidence des "rabbits" (handicap > 36)

### Export HTML

Le programme peut également exporter le classement au format HTML interactif, offrant:
- Un affichage formaté avec les mêmes codes couleurs
- Des lignes cliquables pour afficher les détails de chaque joueur
- Compatibilité avec le format d'API JSON

## Interface Web

Le programme inclut une application web Flask qui permet:
- Affichage du classement Eclectique avec interface interactive
- Consultation des détails de chaque joueur via une API JSON
- Import de nouvelles manches via une interface d'administration
- Gestion des flights avec interface graphique
- Gestion des corrections de scores
- Affichage adapté pour mobile et desktop

### Endpoints API principaux

- `/` : Page d'accueil affichant le classement Eclectique
- `/details-joueur/<id_joueur>` : API JSON retournant les détails d'un joueur
- `/admin` : Interface d'administration
- `/import` : API pour importer un fichier Excel
- `/api/import-html` : API pour importer des joueurs depuis un fichier HTML
- `/api/save-flights` : API pour sauvegarder les flights générés
- `/flights` : Interface de gestion des flights
- `/flights/print/<id_depart>` : Affichage des flights pour impression
- `/flights/print/<id_depart>/pdf` : Export PDF des flights
- `/api/correction/<id_joueur>` : API pour gérer les corrections de scores
- `/manches` : Liste des manches disponibles
- `/manche/<id_manche>` : Affichage du classement d'une manche
- `/manche/<id_manche>/pdf` : Export PDF d'une manche

### Structure des templates

- `index.html` : Template pour l'affichage du classement Eclectique
- `admin.html` : Template pour l'interface d'administration
- `flights.html` : Template pour la gestion des flights
- `flights_print.html` : Template pour l'impression des flights
- `import_html.html` : Template pour l'import de joueurs depuis un fichier HTML
- `manche.html` : Template pour l'affichage du classement d'une manche
- `manches.html` : Template pour la liste des manches

### Lancement du serveur web

```bash
python app.py
```

Le serveur démarre par défaut sur le port 7001 (http://localhost:7001/).

## Variables d'environnement

- `ECLECTIQUE_DB` : Chemin vers la base de données SQLite (défaut: "eclectique.db")

## Utilisation du programme

### Options de ligne de commande

```
python eclectique_manager.py [options]
```

Options disponibles:
- `--db FICHIER`: Chemin vers la base de données (défaut: eclectique.db)
- `--dir DOSSIER`: Répertoire contenant les fichiers Excel à importer
- `--joueur ID`: Afficher le détail pour un joueur spécifique (ID national)
- `--verbose`, `-v`: Mode verbeux (affiche les détails de l'exécution)
- `--reset`: Supprimer et recréer la base de données
- `--pars VAL`: Configurer les pars des trous (format: 1=4,2=3,3=5,...)
- `--pdf FICHIER`: Exporter le classement au format PDF
- `--import-html FICHIER`: Importer les joueurs depuis un fichier HTML

### Exemples d'utilisation

1. **Configurer les pars du parcours**:
   ```bash
   python eclectique_manager.py --pars 1=4,2=3,3=5,4=4,5=3,6=4,7=5,8=4,9=4,10=4,11=4,12=3,13=5,14=4,15=3,16=5,17=5,18=4
   ```

2. **Importer des fichiers Excel**:
   ```bash
   python eclectique_manager.py --dir ./data
   ```

3. **Afficher le classement Eclectique**:
   ```bash
   python eclectique_manager.py
   ```

4. **Voir les détails d'un joueur**:
   ```bash
   python eclectique_manager.py --joueur 123456
   ```

5. **Réinitialiser la base de données**:
   ```bash
   python eclectique_manager.py --reset
   ```

6. **Exporter le classement en PDF**:
   ```bash
   python eclectique_manager.py --pdf classement.pdf
   ```

7. **Importer des joueurs depuis un fichier HTML**:
   ```bash
   python eclectique_manager.py --import-html departs.html
   ```

8. **Lancer l'interface web**:
   ```bash
   python app.py
   ```

## Structure du code

Le programme est organisé en deux modules principaux:

### eclectique_manager.py
Contient la classe `EclectiqueManager` avec toutes les méthodes nécessaires:

- `__init__`: Initialise la classe et la connexion à la base de données
- `init_db`: Crée les tables si elles n'existent pas
- `set_pars`: Configure les pars pour les trous
- `import_manche`: Importe une manche depuis un fichier Excel
- `import_directory`: Importe tous les fichiers Excel d'un répertoire
- `get_classement_eclectique`: Calcule le classement Eclectique
- `afficher_classement_formatte`: Affiche le classement sous forme de tableau
- `afficher_detail_joueur`: Affiche les détails d'un joueur spécifique
- `export_pdf`: Exporte le classement au format PDF
- `export_classement_html`: Exporte le classement au format HTML
- `get_classement_manche`: Calcule le classement d'une manche
- `get_manches_liste`: Récupère la liste des manches
- `export_classement_manche_pdf`: Exporte le classement d'une manche en PDF
- `importer_joueurs_html`: Importe les joueurs depuis un fichier HTML
- `export_flights_pdf`: Exporte les flights au format PDF
- `close`: Ferme la connexion à la base de données

Le module intègre également une classe `PDF` qui étend la classe `FPDF` pour personnaliser l'export PDF.

### app.py
Contient l'application web Flask:

- `index()`: Affiche la page d'accueil avec le classement
- `details_joueur(id_joueur)`: Fournit les détails d'un joueur en JSON
- `admin()`: Affiche l'interface d'administration
- `import_file()`: Gère l'importation de fichiers Excel
- `import_html()`: Gère l'importation de joueurs depuis un fichier HTML
- `classement_manche(id_manche)`: Affiche le classement d'une manche
- `flights_management()`: Affiche l'interface de gestion des flights
- `save_flights()`: Enregistre les flights générés
- `print_flights(id_depart)`: Affiche les flights pour impression
- `export_flights_pdf(id_depart)`: Exporte les flights en PDF
- `api_correction(id_joueur)`: Gère les corrections de scores

## Format des fichiers Excel

Le programme attend des fichiers Excel avec la structure suivante:
- Première ligne: En-têtes (Tee, Genre, Couleur, Date, Compétition)
- Lignes suivantes: Données des joueurs
  - Colonnes 0-9: Informations des joueurs
  - Colonnes 10+: Scores pour les trous (1 à 18)

## Dépendances

- Python 3.6 ou supérieur
- Bibliothèques:
  - pandas (pour la lecture des fichiers Excel)
  - sqlite3 (inclus dans Python standard)
  - fpdf2 (pour l'export PDF)
  - Flask (pour l'interface web)
  - Jinja2 (pour le templating)
  - beautifulsoup4 (pour le parsing HTML)
  - numpy (pour les calculs)

## Installation des dépendances

```bash
pip install -r requirements.txt
```

## Limitations actuelles et pistes d'amélioration

- Pas d'authentification pour l'interface d'administration
- Gestion limitée des erreurs dans les fichiers Excel
- Possibilité d'ajouter d'autres formats d'export
- Pas de gestion des handicaps pour calculer les scores nets
- Pas de statistiques avancées par joueur ou par trou
- Ajout d'un contrôle d'accès sur l'interface admin
- Création d'une API plus complète pour intégration avec d'autres applications
- Amélioration de la répartition automatique des joueurs entre aller et retour
- Gestion de plusieurs parcours différents