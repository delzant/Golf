import pandas as pd
import sqlite3
import os
from datetime import datetime
import glob
import sys
import traceback
from fpdf import FPDF
import copy

class PDF(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.set_auto_page_break(auto=True, margin=10)
        # Définir des marges plus petites
        self.set_margins(5, 10, 5)  # Gauche, Haut, Droite
        
    def header(self):
        # Polices et couleurs
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'CLASSEMENT ECLECTIQUE', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def export_classement_pdf(manager, filename="classement_eclectique.pdf"):
    """
    Exporte le classement eclectique au format PDF avec mise en forme des couleurs
    """
    # Récupérer les données nécessaires
    cursor = manager.conn.cursor()
    resultats = manager.get_classement_eclectique()
    joueurs_avec_scores = [r for r in resultats if r['nb_trous_joues'] > 0]
    
    # Récupérer les pars
    cursor.execute("SELECT trou, par FROM trous")
    pars_data = cursor.fetchall()
    pars = {trou: par for trou, par in pars_data}
    
    # Créer le PDF
    pdf = PDF()
    pdf.add_page()
    
    # Paramètres (très condensés)
    col_height = 5  # Hauteur de ligne réduite
    col_width_idx = 6
    col_width_nom = 32
    col_width_hcp = 8
    col_width_part = 8
    col_width_trou = 7  # Largeur colonne trou très réduite
    col_width_tot = 8  # Largeur colonne total
    
    # Modification des marges pour optimiser l'espace
    pdf.set_margins(5, 10, 5)  # Gauche, Haut, Droite
    
    # Couleurs de fond pour les scores
    colors = {
        'eagle': (255, 0, 0),       # Rouge pour Eagle ou mieux
        'birdie': (255, 255, 0),    # Jaune pour Birdie
        'par': (173, 216, 230),     # Bleu clair pour Par
        'bogey': (255, 255, 255)    # Blanc pour Bogey ou pire
    }
    
    # Entête - Ligne PAR
    pdf.set_font('Arial', 'B', 7)
    pdf.set_fill_color(220, 220, 220)  # Gris clair
    
    pdf.cell(col_width_idx, col_height, 'POS', 1, 0, 'C', True)
    pdf.cell(col_width_nom, col_height, 'Player', 1, 0, 'C', True)
    pdf.cell(col_width_hcp, col_height, 'Hcp', 1, 0, 'C', True)
    pdf.cell(col_width_part, col_height, 'Part.', 1, 0, 'C', True)
    
    # Numéros des trous
    for t in range(1, 19):
        pdf.cell(col_width_trou, col_height, str(t), 1, 0, 'C', True)
    
    pdf.cell(col_width_tot, col_height, 'TOT', 1, 1, 'C', True)
    
    # Ligne PAR
    pdf.set_font('Arial', 'B', 9)
    pdf.set_fill_color(220, 220, 220)  # Gris clair
    
    pdf.cell(col_width_idx, col_height, 'PAR', 1, 0, 'C', True)
    pdf.cell(col_width_nom, col_height, '', 1, 0, 'C', True)
    pdf.cell(col_width_hcp, col_height, '', 1, 0, 'C', True)
    pdf.cell(col_width_part, col_height, '', 1, 0, 'C', True)
    
    total_par = 0
    for t in range(1, 19):
        par = pars.get(t, 4)
        total_par += par
        pdf.cell(col_width_trou, col_height, str(par), 1, 0, 'C', True)
    
    pdf.cell(col_width_tot, col_height, str(total_par), 1, 1, 'C', True)
    
    # Gestion des ex-aequo
    classement = 1
    score_precedent = None
    position_reelle = 1
    
    # Lignes des joueurs
    pdf.set_font('Arial', '', 6)
    
    for position_reelle, r in enumerate(joueurs_avec_scores, 1):
        # Nombre de manches jouées
        cursor.execute("""
        SELECT COUNT(DISTINCT id_manche) FROM scores WHERE id_joueur = ?
        """, (r['id_national'],))
        nb_manches = cursor.fetchone()[0]
        
        # Vérifier si même score que le précédent (ex-aequo)
        if position_reelle > 1 and r['total'] == score_precedent:
            # Garder le même classement (ex-aequo)
            pass
        else:
            # Nouveau classement
            classement = position_reelle
        
        score_precedent = r['total']
        
        # Cellules classement, nom, handicap et participations
        pdf.cell(col_width_idx, col_height, str(classement), 1, 0, 'C')
        pdf.cell(col_width_nom, col_height, r['nom'], 1, 0, 'L')
        pdf.cell(col_width_hcp, col_height, f"{r['handicap']:.1f}", 1, 0, 'C')
        # Coloration verte pour les participations > 5
        if nb_manches > 5:
            pdf.set_fill_color(144, 238, 144)  # Vert clair
            pdf.cell(col_width_part, col_height, str(nb_manches), 1, 0, 'C', True)
        else:
            pdf.cell(col_width_part, col_height, str(nb_manches), 1, 0, 'C')
        
        # Scores par trou
        scores_dict = dict(r['scores_par_trou'])
        
        for t in range(1, 19):
            if t in scores_dict:
                score = scores_dict[t]
                par = pars.get(t, 4)
                
                # Déterminer la couleur de fond
                if score <= par - 2:  # Eagle ou mieux
                    pdf.set_fill_color(*colors['eagle'])
                elif score == par - 1:  # Birdie
                    pdf.set_fill_color(*colors['birdie'])
                elif score == par:  # Par
                    pdf.set_fill_color(*colors['par'])
                else:  # Bogey ou pire
                    pdf.set_fill_color(*colors['bogey'])
                
                pdf.cell(col_width_trou, col_height, str(score), 1, 0, 'C', True)
            else:
                # Trou non joué
                pdf.cell(col_width_trou, col_height, '--', 1, 0, 'C')
        
        # Total
        pdf.cell(col_width_tot, col_height, str(r['total']), 1, 1, 'C')
    
    # Sauvegarder le PDF
    try:
        pdf.output(filename)
        return True, filename
    except Exception as e:
        return False, str(e)
        
class EclectiqueManager:
    def __init__(self, db_path="eclectique.db", verbose=False):
        self.db_path = db_path
        self.conn = None
        self.verbose = verbose
        self.init_db()
        
    def log(self, message):
        if self.verbose:
            print(message)
    
    def init_db(self):
        """Initialise la base de données"""
        self.log(f"Initialisation de la base de données: {self.db_path}")
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # Table joueurs
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS joueurs (
            id_national TEXT PRIMARY KEY,
            nom TEXT,
            genre TEXT,
            homeclub TEXT,
            age INTEGER,
            handicap REAL
        )
        ''')
        
        # Table manches
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS manches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            nom_competition TEXT,
            tee_depart TEXT,
            couleur_depart TEXT,
            nom_fichier TEXT
        )
        ''')
        
        # Table scores
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            id_joueur TEXT,
            id_manche INTEGER,
            trou INTEGER,
            score INTEGER,
            PRIMARY KEY (id_joueur, id_manche, trou),
            FOREIGN KEY (id_joueur) REFERENCES joueurs(id_national),
            FOREIGN KEY (id_manche) REFERENCES manches(id)
        )
        ''')
        
        # Table trous (pars)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS trous (
            trou INTEGER PRIMARY KEY,
            par INTEGER,
            handicap_index INTEGER
        )
        ''')
        
        # Table corrections
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS corrections (
            id_joueur TEXT,
            trou INTEGER,
            score INTEGER,
            note TEXT,
            date_correction TEXT,
            PRIMARY KEY (id_joueur, trou),
            FOREIGN KEY (id_joueur) REFERENCES joueurs(id_national)
        )
        ''')

        # Valeurs par défaut pour les pars (à ajuster selon votre parcours)
        # Vérifier d'abord si la table est vide
        cursor.execute("SELECT COUNT(*) FROM trous")
        if cursor.fetchone()[0] == 0:
            # Initialiser avec les pars spécifiques
            pars_values = {
                1: 4, 2: 3, 3: 5, 4: 4, 5: 3, 6: 4, 7: 5, 8: 4, 9: 4,
                10: 4, 11: 4, 12: 3, 13: 5, 14: 4, 15: 3, 16: 5, 17: 5, 18: 4
            }
            
            for trou, par in pars_values.items():
                cursor.execute("INSERT INTO trous (trou, par) VALUES (?, ?)", (trou, par))
            
            self.log("Pars initialisés avec les valeurs spécifiées")
        
        self.conn.commit()
    
    def set_pars(self, pars_values):
        """Configure les pars pour les trous"""
        cursor = self.conn.cursor()
        
        for trou, par in pars_values.items():
            cursor.execute("UPDATE trous SET par = ? WHERE trou = ?", (par, trou))
        
        self.conn.commit()
        print(f"Pars mis à jour pour {len(pars_values)} trous")
    
    def import_manche(self, excel_path):
        """Importe une manche depuis un fichier Excel de manière robuste"""
        self.log(f"Tentative d'importation de: {excel_path}")
        try:
            fichier_nom = os.path.basename(excel_path)
            
            # Extraction de la date du nom du fichier
            date_from_filename = None
            try:
                date_str = fichier_nom.split()[0]
                date_from_filename = datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")
            except (ValueError, IndexError):
                date_from_filename = datetime.now().strftime("%Y-%m-%d")
            
            # Lecture du fichier Excel avec des options robustes
            try:
                df = pd.read_excel(excel_path, header=None)
            except Exception as e:
                return False, f"Erreur de lecture du fichier: {str(e)}"
            
            self.log(f"Dimensions du dataframe: {df.shape}")
            
            if df.empty or len(df) <= 1:
                return False, "Fichier vide ou sans données suffisantes"
            
            # Analyse de la structure des données pour déterminer les colonnes
            row0 = df.iloc[0].fillna("")  # Première ligne (en-tête)
            
            # Informations de la manche (prendre les premières valeurs de la première ligne)
            tee_depart = str(row0.iloc[0]) if 0 < len(row0) else ""
            gender_standard = str(row0.iloc[1]) if 1 < len(row0) else ""
            couleur_depart = str(row0.iloc[2]) if 2 < len(row0) else ""
            date_str = str(row0.iloc[3]) if 3 < len(row0) else ""
            nom_competition = str(row0.iloc[4]) if 4 < len(row0) else "Eclectique"
            
            # Essayer de parser la date du fichier Excel, sinon utiliser celle du nom de fichier
            date_compet = date_from_filename
            if date_str and date_str != "nan":
                for date_format in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"]:
                    try:
                        date_compet = datetime.strptime(date_str, date_format).strftime("%Y-%m-%d")
                        break
                    except ValueError:
                        continue
            
            # Création de la manche
            cursor = self.conn.cursor()
            cursor.execute("""
            INSERT INTO manches (date, nom_competition, tee_depart, couleur_depart, nom_fichier)
            VALUES (?, ?, ?, ?, ?)
            """, (date_compet, nom_competition, tee_depart, couleur_depart, fichier_nom))
            
            id_manche = cursor.lastrowid
            self.log(f"Manche créée: {nom_competition} - {date_compet} (ID: {id_manche})")
            
            # Déterminer l'index de début des trous
            # On cherche la première colonne numérique après les infos joueur (min. colonne 10)
            trou_start_idx = 10
            max_col = min(28, df.shape[1])  # 18 trous + 10 colonnes d'info = 28 max
            
            # Vérifier la présence de scores pour détecter les 9 ou 18 trous
            nb_trous = max_col - trou_start_idx
            self.log(f"Détection de {nb_trous} trous potentiels (colonnes {trou_start_idx} à {max_col-1})")
            
            # Traitement des données joueurs et scores
            joueurs_importes = 0
            scores_importes = 0
            
            # Parcourir les lignes à partir de la seconde (index 1)
            for idx, row in df.iloc[1:].iterrows():
                row = row.fillna("")  # Remplacer NaN par chaîne vide
                
                # Récupérer l'identifiant du joueur (colonne 5)
                id_national = ""
                if 5 < len(row):
                    id_national = str(row.iloc[5])
                    # Nettoyer l'ID (certains fichiers peuvent avoir des formats différents)
                    id_national = ''.join(c for c in id_national if c.isdigit())
                
                if not id_national:
                    self.log(f"Ignoré ligne {idx+1}: pas d'ID national")
                    continue
                
                # Récupérer les autres infos du joueur
                nom = str(row.iloc[6]) if 6 < len(row) else ""
                homeclub = str(row.iloc[7]) if 7 < len(row) else ""
                
                handicap = 0.0
                if 8 < len(row) and str(row.iloc[8]) != "":
                    try:
                        handicap = float(row.iloc[8])
                    except (ValueError, TypeError):
                        pass
                
                age = 0
                if 9 < len(row) and str(row.iloc[9]) != "":
                    try:
                        age = int(float(row.iloc[9]))
                    except (ValueError, TypeError):
                        pass
                
                genre = str(row.iloc[1]) if 1 < len(row) else ""
                
                self.log(f"Traitement joueur: {id_national} - {nom}")
                
                # Vérifier si le joueur a déjà des scores pour cette date
                cursor.execute("""
                SELECT s.id_manche FROM scores s
                JOIN manches m ON s.id_manche = m.id
                WHERE s.id_joueur = ? AND m.date = ? AND m.id != ?
                LIMIT 1
                """, (id_national, date_compet, id_manche))
                
                if cursor.fetchone():
                    self.log(f"Joueur {id_national} déjà importé pour cette date")
                    continue
                
                # Mise à jour ou insertion du joueur
                cursor.execute('''
                INSERT OR REPLACE INTO joueurs (id_national, nom, genre, homeclub, age, handicap)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (id_national, nom, genre, homeclub, age, handicap))
                joueurs_importes += 1
                
                # Traitement des scores pour les trous
                for i in range(nb_trous):
                    col_idx = trou_start_idx + i
                    trou = i + 1
                    
                    if col_idx < len(row) and str(row.iloc[col_idx]) != "":
                        try:
                            score = int(float(row.iloc[col_idx]))
                            if 0 < score < 20:  # Valider le score (éviter les valeurs aberrantes)
                                cursor.execute('''
                                INSERT INTO scores (id_joueur, id_manche, trou, score)
                                VALUES (?, ?, ?, ?)
                                ''', (id_national, id_manche, trou, score))
                                scores_importes += 1
                        except (ValueError, TypeError):
                            self.log(f"Score invalide pour le trou {trou}: {row.iloc[col_idx]}")
            
            if joueurs_importes == 0:
                # Si aucun joueur n'a été importé, supprimer la manche
                cursor.execute("DELETE FROM manches WHERE id = ?", (id_manche,))
                self.conn.commit()
                return False, "Aucun joueur importé"
            
            self.log(f"Importé: {joueurs_importes} joueurs, {scores_importes} scores")
            self.conn.commit()
            return True, id_manche
        
        except Exception as e:
            self.conn.rollback()
            error_msg = str(e)
            self.log(f"ERREUR lors de l'importation: {error_msg}")
            self.log(traceback.format_exc())
            return False, error_msg
    
    def import_directory(self, directory_path):
        """Importe tous les fichiers Excel d'un répertoire en ignorant les fichiers corrompus"""
        self.log(f"Recherche de fichiers Excel dans: {directory_path}")
        excel_files = glob.glob(os.path.join(directory_path, "*.xlsx"))
        self.log(f"Fichiers trouvés: {len(excel_files)}")
        
        results = []
        for file_path in excel_files:
            fichier_nom = os.path.basename(file_path)
            
            # Vérifier d'abord si le fichier est valide
            try:
                # Vérification rapide du fichier
                with pd.ExcelFile(file_path) as xls:
                    if len(xls.sheet_names) == 0:
                        results.append((fichier_nom, False, "Fichier Excel sans feuilles de calcul"))
                        continue
            except Exception as e:
                results.append((fichier_nom, False, f"Fichier corrompu: {str(e)}"))
                continue
                
            # Si on arrive ici, le fichier est valide
            success, result = self.import_manche(file_path)
            results.append((fichier_nom, success, result))
        
        return results
    
    def get_classement_eclectique(self):
        """Calcule le classement eclectique (meilleur score sur chaque trou)"""
        self.log("Calcul du classement eclectique")
        cursor = self.conn.cursor()
        
        # Récupère tous les joueurs
        cursor.execute("SELECT id_national, nom, handicap FROM joueurs")
        joueurs = cursor.fetchall()
        self.log(f"Nombre de joueurs: {len(joueurs)}")
        
        resultats = []
        
        for id_joueur, nom, handicap in joueurs:
            total = 0
            scores_par_trou = []
            nb_trous_joues = 0
            
            # Pour chaque trou, trouve le meilleur score du joueur
            for trou in range(1, 19):
                cursor.execute('''
                SELECT MIN(score) FROM scores 
                WHERE id_joueur = ? AND trou = ?
                ''', (id_joueur, trou))
                
                meilleur_score = cursor.fetchone()[0]
                
                # Vérifier s'il existe une correction pour ce trou
                cursor.execute('''
                SELECT score FROM corrections
                WHERE id_joueur = ? AND trou = ?
                ''', (id_joueur, trou))
                
                correction = cursor.fetchone()
                
                # Utiliser la correction si elle existe
                if correction is not None:
                    meilleur_score = correction[0]
        
                if meilleur_score is not None:
                    total += meilleur_score
                    scores_par_trou.append((trou, meilleur_score))
                    nb_trous_joues += 1
            
            resultats.append({
                'id_national': id_joueur,
                'nom': nom,
                'handicap': handicap,
                'total': total,
                'nb_trous_joues': nb_trous_joues,
                'scores_par_trou': scores_par_trou
            })
        
        # Tri par score total (croissant) pour les joueurs avec des scores
        resultats.sort(key=lambda x: (x['total'] if x['nb_trous_joues'] > 0 else float('inf')))
        return resultats
    
    def afficher_classement_formatte(self):
        """Affiche le classement Eclectique dans un format tabulaire avec alignement correct"""
        cursor = self.conn.cursor()
        
        # Récupérer les pars des trous
        pars = {}
        try:
            cursor.execute("SELECT trou, par FROM trous")
            pars_data = cursor.fetchall()
            for trou, par in pars_data:
                pars[trou] = par
        except:
            # Valeurs par défaut
            for i in range(1, 19):
                pars[i] = 4
        
        # Récupérer le classement
        resultats = self.get_classement_eclectique()
        joueurs_avec_scores = [r for r in resultats if r['nb_trous_joues'] > 0]
        
        if not joueurs_avec_scores:
            print("Aucun score importé pour l'instant.")
            return
        
        # Calculer la largeur maximale pour les noms
        max_nom_width = max(len(r['nom']) for r in joueurs_avec_scores)
        max_nom_width = max(max_nom_width, 25)  # Minimum 25 caractères
        
        # Déterminer la largeur des colonnes d'index
        max_idx = len(joueurs_avec_scores)
        idx_width = len(str(max_idx))
        idx_width = max(idx_width, 3)  # Minimum 3 caractères
        
        # Entête du tableau
        print("\nCLASSEMENT ECLECTIQUE:")
        print(f"{'':{idx_width}} | {'':^{max_nom_width}} | {'HCP':^5} | {'PART':^4} |", end="")
        for t in range(1, 19):
            print(f" {t:2} |", end="")
        print(" TOT |")
        
        # Ligne PAR
        print(f"{'':{idx_width}} | {'PAR':^{max_nom_width}} | {'':^5} | {'':^4} |", end="")
        total_par = 0
        for t in range(1, 19):
            par = pars.get(t, 4)
            total_par += par
            print(f" {par:2} |", end="")
        print(f" {total_par:3} |")
        
        # Ligne de séparation
        sep_line = "-" * (idx_width + 3 + max_nom_width + 2 + 6 + 2 + 5 + 2 + (4 * 18) + 6)
        print(sep_line)
        
        # Gestion des ex-aequo
        classement = 1
        score_precedent = None
        position_reelle = 1
        
        # Lignes des joueurs
        for position_reelle, r in enumerate(joueurs_avec_scores, 1):
            # Nombre de manches jouées
            cursor.execute("""
            SELECT COUNT(DISTINCT id_manche) FROM scores WHERE id_joueur = ?
            """, (r['id_national'],))
            nb_manches = cursor.fetchone()[0]
            
            # Vérifier si même score que le précédent (ex-aequo)
            if position_reelle > 1 and r['total'] == score_precedent:
                # Garder le même classement (ex-aequo)
                pass
            else:
                # Nouveau classement
                classement = position_reelle
            
            score_precedent = r['total']
            
            # Format l'index pour assurer l'alignement (avec padding à droite)
            idx_str = f"{classement:{idx_width}}"
            
            # Ligne du joueur
            print(f"{idx_str} | {r['nom']:<{max_nom_width}} | {r['handicap']:5.1f} | {nb_manches:4} |", end="")
            
            # Scores par trou
            scores_dict = dict(r['scores_par_trou'])
            for t in range(1, 19):
                if t in scores_dict:
                    score = scores_dict[t]
                    par = pars.get(t, 4)
                    
                    # Couleur en fonction du score vs par
                    if score <= par - 2:
                        # Eagle ou mieux (rouge)
                        print(f" \033[91m{score:2}\033[0m |", end="")
                    elif score == par - 1:
                        # Birdie (jaune)
                        print(f" \033[93m{score:2}\033[0m |", end="")
                    elif score == par:
                        # Par (bleu)
                        print(f" \033[94m{score:2}\033[0m |", end="")
                    else:
                        # Plus que le par (noir)
                        print(f" {score:2} |", end="")
                else:
                    # Trou non joué
                    print(f" -- |", end="")
            
            # Total
            print(f" {r['total']:3} |")
        
        print(sep_line)
        
    def afficher_detail_joueur(self, id_joueur):
        """Affiche le détail des scores d'un joueur pour toutes les manches"""
        cursor = self.conn.cursor()
        
        # Info du joueur
        cursor.execute("SELECT nom, handicap FROM joueurs WHERE id_national = ?", (id_joueur,))
        joueur_info = cursor.fetchone()
        
        if not joueur_info:
            print(f"Joueur avec ID {id_joueur} non trouvé")
            return
        
        nom, handicap = joueur_info
        print(f"\nDétail pour {nom} (Handicap: {handicap}):")
        
        # Meilleurs scores par trou
        print("\nMeilleurs scores par trou:")
        for trou in range(1, 19):
            cursor.execute('''
            SELECT MIN(score), m.date 
            FROM scores s 
            JOIN manches m ON s.id_manche = m.id
            WHERE s.id_joueur = ? AND s.trou = ?
            GROUP BY s.trou
            ''', (id_joueur, trou))
            
            result = cursor.fetchone()
            if result:
                score, date = result
                print(f"Trou {trou}: {score} ({date})")
            else:
                print(f"Trou {trou}: Non joué")
        
        # Toutes les manches jouées
        print("\nToutes les manches:")
        cursor.execute('''
        SELECT DISTINCT m.id, m.date, m.nom_competition, 
               COUNT(s.trou) as trous_joues,
               SUM(s.score) as score_total
        FROM scores s
        JOIN manches m ON s.id_manche = m.id
        WHERE s.id_joueur = ?
        GROUP BY m.id
        ORDER BY m.date
        ''', (id_joueur,))
        
        manches = cursor.fetchall()
        for manche_id, date, nom_compet, trous_joues, score_total in manches:
            print(f"{date} - {nom_compet}: {score_total} coups sur {trous_joues} trous")
            
            # Détail par trou pour cette manche
            cursor.execute('''
            SELECT trou, score FROM scores
            WHERE id_joueur = ? AND id_manche = ?
            ORDER BY trou
            ''', (id_joueur, manche_id))
            
            trou_scores = cursor.fetchall()
            trou_details = ", ".join([f"T{trou}:{score}" for trou, score in trou_scores])
            print(f"  Détail: {trou_details}")
    
    def close(self):
        """Ferme la connexion à la base de données"""
        if self.conn:
            self.conn.close()
            self.log("Connexion à la base de données fermée")

    def export_pdf(self, filename="classement_eclectique.pdf"):
        """Exporte le classement en PDF"""
        try:
            import fpdf
        except ImportError:
            print("Module fpdf non installé. Installation avec pip install fpdf2")
            return False, "Module fpdf non installé"
        
        return export_classement_pdf(self, filename)
    
    def export_classement_html(manager, filename="classement.html"):
        """Exporte le classement eclectique au format HTML interactif"""
        cursor = manager.conn.cursor()
        resultats = manager.get_classement_eclectique()
        joueurs_avec_scores = [r for r in resultats if r['nb_trous_joues'] > 0]
        
        # Récupérer les pars
        cursor.execute("SELECT trou, par FROM trous")
        pars_data = cursor.fetchall()
        pars = {trou: par for trou, par in pars_data}
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Classement Eclectique</title>
            <style>
                body { font-family: Arial, sans-serif; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 4px; text-align: center; }
                tr:nth-child(even) { background-color: #f2f2f2; }
                th { background-color: #4CAF50; color: white; }
                .eagle { background-color: #ff0000; color: white; }
                .birdie { background-color: #ffff00; }
                .par { background-color: #add8e6; }
                .joueur-row { cursor: pointer; }
                .details { display: none; }
                .details-visible { display: table-row; }
                .participations-high { background-color: #90EE90; }
            </style>
            <script>
                function toggleDetails(id) {
                    var details = document.getElementById('details-' + id);
                    if (details.classList.contains('details-visible')) {
                        details.classList.remove('details-visible');
                    } else {
                        // Fermer tous les autres détails
                        var allDetails = document.getElementsByClassName('details-visible');
                        for (var i = 0; i < allDetails.length; i++) {
                            allDetails[i].classList.remove('details-visible');
                        }
                        details.classList.add('details-visible');
                        
                        // Charger les détails via AJAX si nécessaire
                        fetch('/details-joueur/' + id)
                            .then(response => response.json())
                            .then(data => {
                                var detailsHTML = '<h4>Manches jouées</h4><ul>';
                                data.manches.forEach(function(manche) {
                                    detailsHTML += '<li>' + manche.date + ' - ' + manche.nom + ' : ' + manche.score + '</li>';
                                });
                                detailsHTML += '</ul><h4>Statistiques</h4><table>...</table>';
                                document.getElementById('details-content-' + id).innerHTML = detailsHTML;
                            });
                    }
                }
            </script>
        </head>
        <body>
            <h1>Classement Eclectique</h1>
            <table>
                <tr>
                    <th>POS</th>
                    <th>Joueur</th>
                    <th>Hcp</th>
                    <th>Part.</th>
        """
        
        # Ajouter les entêtes des trous
        for t in range(1, 19):
            html += f"<th>{t}</th>"
        html += "<th>TOT</th></tr>"
        
        # Ligne PAR
        html += "<tr><td></td><td>PAR</td><td></td><td></td>"
        total_par = 0
        for t in range(1, 19):
            par = pars.get(t, 4)
            total_par += par
            html += f"<td>{par}</td>"
        html += f"<td>{total_par}</td></tr>"
        
        # Gestion des ex-aequo
        classement = 1
        score_precedent = None
        position_reelle = 1
        
        # Lignes des joueurs
        for position_reelle, r in enumerate(joueurs_avec_scores, 1):
            # Nombre de manches jouées
            cursor.execute("""
            SELECT COUNT(DISTINCT id_manche) FROM scores WHERE id_joueur = ?
            """, (r['id_national'],))
            nb_manches = cursor.fetchone()[0]
            
            # Vérifier si même score que le précédent (ex-aequo)
            if position_reelle > 1 and r['total'] == score_precedent:
                pass  # Garder le même classement (ex-aequo)
            else:
                classement = position_reelle
            
            score_precedent = r['total']
            
            # Ligne du joueur (cliquable)
            html += f"""<tr class="joueur-row" onclick="toggleDetails('{r['id_national']}')">
                <td>{classement}</td>
                <td>{r['nom']}</td>
                <td>{r['handicap']:.1f}</td>"""
            
            # Coloration pour participations > 5
            if nb_manches > 5:
                html += f"<td class='participations-high'>{nb_manches}</td>"
            else:
                html += f"<td>{nb_manches}</td>"
            
            # Scores par trou
            scores_dict = dict(r['scores_par_trou'])
            for t in range(1, 19):
                if t in scores_dict:
                    score = scores_dict[t]
                    par = pars.get(t, 4)
                    
                    # Déterminer la classe CSS
                    css_class = ""
                    if score <= par - 2:  # Eagle ou mieux
                        css_class = "eagle"
                    elif score == par - 1:  # Birdie
                        css_class = "birdie"
                    elif score == par:  # Par
                        css_class = "par"
                    
                    html += f"<td class='{css_class}'>{score}</td>"
                else:
                    # Trou non joué
                    html += "<td>--</td>"
            
            # Total
            html += f"<td>{r['total']}</td></tr>"
            
            # Ligne de détails (initialement cachée)
            html += f"""
            <tr id="details-{r['id_national']}" class="details">
                <td colspan="23">
                    <div id="details-content-{r['id_national']}">
                        Chargement des détails...
                    </div>
                </td>
            </tr>
            """
        
        html += """
            </table>
        </body>
        </html>
        """
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
        
        return True, filename

    def get_classement_manche(self, id_manche):
        """Calcule le classement brut pour une manche spécifique"""
        cursor = self.conn.cursor()
        
        # Récupérer les informations de la manche
        cursor.execute("SELECT date, nom_competition FROM manches WHERE id = ?", (id_manche,))
        info_manche = cursor.fetchone()
        
        if not info_manche:
            return None
        
        date_manche, nom_competition = info_manche
        
        # Récupérer tous les joueurs ayant participé à cette manche
        cursor.execute("""
            SELECT DISTINCT j.id_national, j.nom, j.handicap, j.genre 
            FROM scores s
            JOIN joueurs j ON s.id_joueur = j.id_national
            WHERE s.id_manche = ?
        """, (id_manche,))
        
        joueurs = cursor.fetchall()
        
        # Préparation des listes pour chaque classement
        joueurs_aller = []
        joueurs_retour = []
        joueurs_18trous = []
        categories = {
            'homme_9': [],    # Hommes ayant joué 9 trous
            'homme_18': [],   # Hommes ayant joué 18 trous
            'femme_9': [],    # Femmes ayant joué 9 trous
            'femme_18': [],   # Femmes ayant joué 18 trous
            'rabit_9': [],    # Rabit ayant joué 9 trous
            'rabit_18': []    # Rabit ayant joué 18 trous
        }
        
        # Analyser les scores de chaque joueur
        for id_joueur, nom, handicap, genre in joueurs:
            # Récupérer les scores du joueur pour cette manche
            cursor.execute("""
                SELECT trou, score FROM scores
                WHERE id_joueur = ? AND id_manche = ?
                ORDER BY trou
            """, (id_joueur, id_manche))
            
            scores = cursor.fetchall()
            scores_dict = dict(scores)
            
            # Déterminer quels trous ont été joués (score < 11)
            trous_aller = [t for t in range(1, 10) if t in scores_dict and scores_dict[t] < 11]
            trous_retour = [t for t in range(10, 19) if t in scores_dict and scores_dict[t] < 11]
            
            # Calculer les scores totaux
            score_aller = sum(scores_dict.get(t, 0) for t in trous_aller)
            score_retour = sum(scores_dict.get(t, 0) for t in trous_retour)
            
            nb_trous_aller = len(trous_aller)
            nb_trous_retour = len(trous_retour)
            
            # Données du joueur
            joueur_data = {
                'id_national': id_joueur,
                'nom': nom,
                'handicap': handicap,
                'genre': genre,
                'scores': scores_dict,
                'nb_trous_aller': nb_trous_aller,
                'nb_trous_retour': nb_trous_retour,
                'score_aller': score_aller,
                'score_retour': score_retour,
                'score_total': score_aller + score_retour
            }
            
            # Ajouter le joueur aux classements appropriés
            if nb_trous_aller >= 7 and nb_trous_retour < 3:  # A joué principalement l'aller
                joueurs_aller.append(copy.deepcopy(joueur_data))
            elif nb_trous_retour >= 7 and nb_trous_aller < 3:  # A joué principalement le retour
                joueurs_retour.append(copy.deepcopy(joueur_data))
            elif nb_trous_aller >= 7 and nb_trous_retour >= 7:  # A joué les 18 trous
                joueurs_18trous.append(copy.deepcopy(joueur_data))
            
            # Ajouter le joueur au classement par catégorie
            if nb_trous_aller >= 7 and nb_trous_retour >= 7:  # A joué les 18 trous
                if handicap > 36:
                    categories['rabit_18'].append(copy.deepcopy(joueur_data))
                elif genre.lower() == 'men' or genre.lower() == 'homme':
                    categories['homme_18'].append(copy.deepcopy(joueur_data))
                else:
                    categories['femme_18'].append(copy.deepcopy(joueur_data))
            else:  # A joué seulement 9 trous
                if handicap > 36:
                    categories['rabit_9'].append(copy.deepcopy(joueur_data))
                elif genre.lower() == 'men' or genre.lower() == 'homme':
                    categories['homme_9'].append(copy.deepcopy(joueur_data))
                else:
                    categories['femme_9'].append(copy.deepcopy(joueur_data))
        
        # CLASSEMENT ALLER
        joueurs_aller.sort(key=lambda x: x['score_aller'])
        position_reelle = 1
        classement = 1
        prev_score = None
        for i, joueur in enumerate(joueurs_aller):
            if i > 0 and joueur['score_aller'] == prev_score:
                # Ex-aequo, même position que le précédent
                joueur['pos'] = classement
            else:
                classement = position_reelle
                joueur['pos'] = classement
            
            prev_score = joueur['score_aller']
            position_reelle += 1
        
        # CLASSEMENT RETOUR: trier par score_retour croissant
        joueurs_retour.sort(key=lambda x: x['score_retour'])
        position_reelle = 1
        classement = 1
        prev_score = None
        for i, joueur in enumerate(joueurs_retour):
            if i > 0 and joueur['score_retour'] == prev_score:
                # Ex-aequo, même position que le précédent
                joueur['pos'] = classement
            else:
                classement = position_reelle
                joueur['pos'] = classement
 
            prev_score = joueur['score_retour']
            position_reelle += 1
        
        # CLASSEMENT 18 TROUS: trier par score_total croissant
        joueurs_18trous.sort(key=lambda x: x['score_total'])
        # Attribuer les positions, en commençant par 1
        position_reelle = 1
        classement = 1
        prev_score = None
        for i, joueur in enumerate(joueurs_18trous):
            if i > 0 and joueur['score_total'] == prev_score:
                # Ex-aequo, même position que le précédent
                joueur['pos'] = classement
            else:
                classement = position_reelle
                joueur['pos'] = classement
                
            prev_score = joueur['score_total']
            position_reelle += 1
        
        # CLASSEMENT PAR CATÉGORIES: trier chaque catégorie par score_total
        for cat, joueurs in categories.items():
            joueurs.sort(key=lambda x: x['score_total'])
            # Attribuer les positions, en commençant par 1
            position_reelle = 1
            classement = 1
            prev_score = None
            for i, joueur in enumerate(joueurs):
                if i > 0 and joueur['score_total'] == prev_score:
                    # Ex-aequo, même position que le précédent
                    joueur['pos'] = classement
                else:
                    classement = position_reelle
                    joueur['pos'] = classement
                
                prev_score = joueur['score_total']
                position_reelle += 1
        
        # Assembler tous les résultats
        resultats = {
            'info': {'id': id_manche, 'date': date_manche, 'nom': nom_competition},
            'joueurs_aller': joueurs_aller,
            'joueurs_retour': joueurs_retour,
            'joueurs_18trous': joueurs_18trous,
            'categories': categories
        }
        
        return resultats

    def get_manches_liste(self):
        """Récupère la liste des manches disponibles"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, date, nom_competition, 
                (SELECT COUNT(DISTINCT id_joueur) FROM scores WHERE id_manche = m.id) as nb_joueurs
            FROM manches m
            ORDER BY date DESC
        """)
        return cursor.fetchall()

    def export_classement_manche_pdf(self, id_manche, filename=None):
        """Exporte le classement d'une manche en PDF"""
        classement = self.get_classement_manche(id_manche)
        
        if not classement:
            return False, "Manche introuvable"
        
        if not filename:
            date_str = classement['info']['date'].replace('-', '')
            nom_fichier = f"classement_{date_str}_{id_manche}.pdf"
            filename = nom_fichier
        
        # Récupérer les pars
        cursor = self.conn.cursor()
        cursor.execute("SELECT trou, par FROM trous")
        pars_data = cursor.fetchall()
        pars = {trou: par for trou, par in pars_data}
        
        # Créer le PDF
        pdf = PDF()
        pdf.add_page()
        
        # Titre
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, f"Classement {classement['info']['nom']}", 0, 1, 'C')
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 8, f"Date: {classement['info']['date']}", 0, 1, 'C')
        pdf.ln(5)
        
        # Paramètres
        col_width_idx = 10
        col_width_nom = 40
        col_width_hcp = 15
        col_width_score = 15
        
        # Fonction pour dessiner un tableau de classement
        def dessiner_classement(titre, joueurs, score_key):
            if not joueurs:
                return
            
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, titre, 0, 1, 'L')
            
            # Entête
            pdf.set_font('Arial', 'B', 9)
            pdf.set_fill_color(220, 220, 220)
            pdf.cell(col_width_idx, 7, 'POS', 1, 0, 'C', True)
            pdf.cell(col_width_nom, 7, 'Joueur', 1, 0, 'L', True)
            pdf.cell(col_width_hcp, 7, 'HCP', 1, 0, 'C', True)
            pdf.cell(col_width_score, 7, 'Score', 1, 1, 'C', True)
            
            # Lignes des joueurs
            pdf.set_font('Arial', '', 9)
            for joueur in joueurs:
                pdf.cell(col_width_idx, 7, str(joueur['classement']), 1, 0, 'C')
                pdf.cell(col_width_nom, 7, joueur['nom'], 1, 0, 'L')
                pdf.cell(col_width_hcp, 7, f"{joueur['handicap']:.1f}", 1, 0, 'C')
                pdf.cell(col_width_score, 7, str(joueur[score_key]), 1, 1, 'C')
            
            pdf.ln(5)
        
        # Dessiner les classements
        dessiner_classement("Classement Aller (Trous 1-9)", classement['joueurs_aller'], 'score_aller')
        dessiner_classement("Classement Retour (Trous 10-18)", classement['joueurs_retour'], 'score_retour')
        dessiner_classement("Classement 18 Trous", classement['joueurs_18trous'], 'score_total')
        
        # Nouvelle page pour les catégories
        if any(len(classement['categories'][cat]) > 0 for cat in classement['categories']):
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, "Classements par catégorie", 0, 1, 'C')
            pdf.ln(5)
            
            dessiner_classement("Hommes", classement['categories']['homme'], 'score_total')
            dessiner_classement("Femmes", classement['categories']['femme'], 'score_total')
            dessiner_classement("Rabit (HCP > 36)", classement['categories']['rabit'], 'score_total')
        
        # Sauvegarder le PDF
        try:
            pdf.output(filename)
            return True, filename
        except Exception as e:
            return False, str(e)
    
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Gestionnaire de compétition Eclectique')
    parser.add_argument('--db', default='eclectique.db', help='Chemin vers la base de données')
    parser.add_argument('--dir', help='Répertoire contenant les fichiers Excel à importer')
    parser.add_argument('--joueur', help='Afficher le détail pour un joueur (ID national)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Mode verbeux')
    parser.add_argument('--reset', action='store_true', help='Supprimer la base de données existante et recommencer')
    parser.add_argument('--pars', help='Configurer les pars (format: 1=4,2=3,3=5,...)')
    parser.add_argument('--pdf', help='Exporter le classement en PDF (spécifier le nom du fichier)')
    
    args = parser.parse_args()
    
    print(f"Gestionnaire Eclectique v1.0")
    
    # Supprimer la base de données si demandé
    if args.reset and os.path.exists(args.db):
        os.remove(args.db)
        print(f"Base de données {args.db} supprimée")
    
    manager = EclectiqueManager(db_path=args.db, verbose=args.verbose)
    
    # Configurer les pars si demandé
    if args.pars:
        pars_values = {}
        try:
            for pair in args.pars.split(','):
                trou, par = pair.split('=')
                pars_values[int(trou)] = int(par)
            manager.set_pars(pars_values)
        except Exception as e:
            print(f"Erreur lors de la configuration des pars: {e}")
    
    if args.dir:
        print(f"Importation des fichiers depuis: {args.dir}")
        
        if not os.path.exists(args.dir):
            print(f"ERREUR: Le répertoire {args.dir} n'existe pas!")
            sys.exit(1)
        
        results = manager.import_directory(args.dir)
        
        # Affichage des résultats d'importation
        print("\nRésultats d'importation:")
        if not results:
            print("Aucun fichier Excel (.xlsx) trouvé dans le répertoire spécifié.")
        
        for file, success, result in results:
            if success:
                print(f"✓ {file} - Importé avec succès (ID: {result})")
            else:
                if isinstance(result, int):
                    print(f"- {file} - Déjà importé (ID: {result})")
                else:
                    print(f"✗ {file} - Erreur: {result}")
    
    # Export PDF si demandé
    if args.pdf:
        print(f"Exportation du classement en PDF: {args.pdf}")
        success, result = manager.export_pdf(filename=args.pdf)
        if success:
            print(f"Le classement a été exporté avec succès dans {result}")
        else:
            print(f"Erreur lors de l'exportation: {result}")
    
    if args.joueur:
        manager.afficher_detail_joueur(args.joueur)
    else:
        # Affichage du classement formaté
        manager.afficher_classement_formatte()
    
    manager.close()

if __name__ == "__main__":
    main()