from flask import Flask, render_template, jsonify, request
import os
from eclectique_manager import EclectiqueManager
from datetime import datetime
app = Flask(__name__)
db_path = os.environ.get('ECLECTIQUE_DB', 'eclectique.db')

@app.route('/')
def index():
    """Page d'accueil avec le classement"""
    manager = EclectiqueManager(db_path)
    resultats = manager.get_classement_eclectique()
    
    # Récupérer les pars des trous
    cursor = manager.conn.cursor()
    cursor.execute("SELECT trou, par FROM trous")
    pars_data = cursor.fetchall()
    pars = {trou: par for trou, par in pars_data}
    
    # Filtrer les joueurs avec des scores
    joueurs_avec_scores = [r for r in resultats if r['nb_trous_joues'] > 0]
    
    # Ajouter le nombre de manches pour chaque joueur
    for joueur in joueurs_avec_scores:
        cursor.execute("""
        SELECT COUNT(DISTINCT id_manche) FROM scores WHERE id_joueur = ?
        """, (joueur['id_national'],))
        joueur['nb_manches'] = cursor.fetchone()[0]
    
    # Calculer les classements (en tenant compte des ex-aequo)
    classement = 1
    score_precedent = None
    position_reelle = 1
    
    for position_reelle, joueur in enumerate(joueurs_avec_scores, 1):
        if position_reelle > 1 and joueur['total'] == score_precedent:
            joueur['classement'] = classement  # Ex-aequo
        else:
            classement = position_reelle
            joueur['classement'] = classement
        
        score_precedent = joueur['total']
    
    # Calcul explicite du total_par
    total_par = sum(pars.get(t, 4) for t in range(1, 19))
    
    manager.close()
    return render_template('index.html', joueurs=joueurs_avec_scores, pars=pars, total_par=total_par)

@app.route('/aide')
def aide():
    """Page d'aide pour les utilisateurs"""
    return render_template('aide.html')

@app.route('/details-joueur/<id_joueur>')
def details_joueur(id_joueur):
    """API pour obtenir les détails d'un joueur en JSON"""
    manager = EclectiqueManager(db_path)
    cursor = manager.conn.cursor()
    
    # Infos du joueur
    cursor.execute("SELECT nom, handicap FROM joueurs WHERE id_national = ?", (id_joueur,))
    joueur_info = cursor.fetchone()
    
    if not joueur_info:
        manager.close()
        return jsonify({"error": f"Joueur {id_joueur} non trouvé"}), 404
    
    nom, handicap = joueur_info
    
    # Meilleurs scores par trou
    meilleurs_scores = []
    for trou in range(1, 19):
        # Vérifier d'abord s'il existe une correction
        cursor.execute('''
        SELECT score, note, date_correction 
        FROM corrections 
        WHERE id_joueur = ? AND trou = ?
        ''', (id_joueur, trou))
        
        correction = cursor.fetchone()
        
        if correction:
            # Si une correction existe, l'utiliser
            score, note, date_correction = correction
            meilleurs_scores.append({
                "trou": trou,
                "score": score,
                "date": date_correction,
                "competition": "Correction manuelle",
                "note": note,
                "est_correction": True
            })
        else:
            # Sinon, prendre le meilleur score des manches
            cursor.execute('''
            SELECT MIN(score), m.date, m.nom_competition
            FROM scores s 
            JOIN manches m ON s.id_manche = m.id
            WHERE s.id_joueur = ? AND s.trou = ?
            GROUP BY s.trou
            ''', (id_joueur, trou))
            
            result = cursor.fetchone()
            if result:
                score, date, nom_compet = result
                meilleurs_scores.append({
                    "trou": trou,
                    "score": score,
                    "date": date,
                    "competition": nom_compet
                })
    
    # Toutes les manches jouées
    cursor.execute('''
    SELECT DISTINCT m.id, m.date, m.nom_competition, 
           COUNT(s.trou) as trous_joues,
           SUM(s.score) as score_total
    FROM scores s
    JOIN manches m ON s.id_manche = m.id
    WHERE s.id_joueur = ?
    GROUP BY m.id
    ORDER BY m.date DESC
    ''', (id_joueur,))
    
    manches_raw = cursor.fetchall()
    manches = []
    
    for manche_id, date, nom_compet, trous_joues, score_total in manches_raw:
        # Récupérer les scores par trou pour cette manche
        cursor.execute('''
        SELECT trou, score FROM scores
        WHERE id_joueur = ? AND id_manche = ?
        ORDER BY trou
        ''', (id_joueur, manche_id))
        
        scores = {trou: score for trou, score in cursor.fetchall()}
        
        manches.append({
            "id": manche_id,
            "date": date,
            "nom": nom_compet,
            "trous_joues": trous_joues,
            "score_total": score_total,
            "scores": scores
        })
    
    # Statistiques générales
    stats = {
        "nb_manches": len(manches),
        "meilleur_score_total": min([m["score_total"] for m in manches]) if manches else 0,
        "nb_trous_complets": len(meilleurs_scores),
        "score_eclectique": sum([s["score"] for s in meilleurs_scores])
    }
    
    manager.close()
    
    return jsonify({
        "joueur": {
            "id": id_joueur,
            "nom": nom,
            "handicap": handicap
        },
        "meilleurs_scores": meilleurs_scores,
        "manches": manches,
        "stats": stats
    })

@app.route('/manches')
def liste_manches():
    """Page listant toutes les manches avec liens vers les classements"""
    manager = EclectiqueManager(db_path)
    manches = manager.get_manches_liste()
    manager.close()
    return render_template('manches.html', manches=manches)

@app.route('/manche/<int:id_manche>')
def classement_manche(id_manche):
    """Page affichant le classement d'une manche spécifique"""
    manager = EclectiqueManager(db_path)
    classement = manager.get_classement_manche(id_manche)
    
    # Récupérer les pars des trous
    cursor = manager.conn.cursor()
    cursor.execute("SELECT trou, par FROM trous")
    pars_data = cursor.fetchall()
    pars = {trou: par for trou, par in pars_data}
    
    manager.close()
    
    if not classement:
        return "Manche introuvable", 404
    
    return render_template('manche.html', classement=classement, pars=pars)

@app.route('/api/manche/<int:id_manche>')
def api_manche(id_manche):
    """API JSON pour le classement d'une manche"""
    manager = EclectiqueManager(db_path)
    classement = manager.get_classement_manche(id_manche)
    manager.close()
    
    if not classement:
        return jsonify({"error": "Manche introuvable"}), 404
    
    return jsonify(classement)

@app.route('/manche/<int:id_manche>/pdf')
def export_manche_pdf(id_manche):
    """Génère et télécharge le PDF du classement d'une manche"""
    manager = EclectiqueManager(db_path)
    
    # Générer le PDF dans un dossier temporaire
    import tempfile
    import os
    temp_dir = tempfile.gettempdir()
    filename = os.path.join(temp_dir, f"classement_manche_{id_manche}.pdf")
    
    success, result = manager.export_classement_manche_pdf(id_manche, filename)
    manager.close()
    
    if not success:
        return f"Erreur lors de la génération du PDF: {result}", 500
    
    # Renvoyer le fichier PDF
    from flask import send_file
    return send_file(filename, as_attachment=True, download_name=os.path.basename(filename))

@app.route('/manche/latest/pdf')
def export_latest_manche_pdf():
    """Génère et télécharge le PDF de la dernière manche"""
    manager = EclectiqueManager(db_path)
    cursor = manager.conn.cursor()
    
    # Récupérer l'ID de la dernière manche
    cursor.execute("SELECT id FROM manches ORDER BY date DESC LIMIT 1")
    result = cursor.fetchone()
    
    if not result:
        return "Aucune manche n'existe", 404
    
    latest_id = result[0]
    manager.close()
    
    # Rediriger vers l'export PDF de cette manche
    return export_manche_pdf(latest_id)

@app.route('/api/joueurs')
def api_joueurs_liste():
    """API pour obtenir la liste des joueurs en JSON"""
    manager = EclectiqueManager(db_path)
    cursor = manager.conn.cursor()
    cursor.execute("SELECT id_national, nom FROM joueurs ORDER BY nom")
    joueurs = [{"id": j[0], "nom": j[1]} for j in cursor.fetchall()]
    manager.close()
    return jsonify(joueurs)

@app.route('/api/correction/<id_joueur>', methods=['GET', 'POST'])
def api_correction(id_joueur):
    """API pour récupérer/enregistrer les corrections d'un joueur"""
    manager = EclectiqueManager(db_path)
    
    if request.method == 'POST':
        # Traitement de la sauvegarde des corrections
        corrections = request.json
        cursor = manager.conn.cursor()
        
        for trou, data in corrections.items():
            trou = int(trou)
            score = data.get('score')
            note = data.get('note', '')
            
            # Insérer/mettre à jour la correction
            cursor.execute("""
                INSERT OR REPLACE INTO corrections 
                (id_joueur, trou, score, note, date_correction) 
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (id_joueur, trou, score, note))
        
        manager.conn.commit()
        manager.close()
        return jsonify({"success": True})
    
    # Méthode GET - Récupérer les meilleures scores et corrections
    cursor = manager.conn.cursor()
    
    # Récupérer les infos du joueur
    cursor.execute("SELECT nom, handicap FROM joueurs WHERE id_national = ?", (id_joueur,))
    joueur_info = cursor.fetchone()
    
    if not joueur_info:
        manager.close()
        return jsonify({"error": f"Joueur {id_joueur} non trouvé"}), 404
    
    # Meilleurs scores par trou
    meilleurs_scores = []
    for trou in range(1, 19):
        cursor.execute('''
        SELECT MIN(score), m.date, m.nom_competition
        FROM scores s 
        JOIN manches m ON s.id_manche = m.id
        WHERE s.id_joueur = ? AND s.trou = ?
        GROUP BY s.trou
        ''', (id_joueur, trou))
        
        result = cursor.fetchone()
        score_data = {
            "trou": trou,
            "score": None,
            "date": None,
            "competition": None,
            "correction": None,
            "note_correction": None
        }
        
        if result:
            score, date, nom_compet = result
            score_data.update({
                "score": score,
                "date": date,
                "competition": nom_compet
            })
        
        # Vérifier s'il existe une correction
        cursor.execute('''
        SELECT score, note, date_correction
        FROM corrections
        WHERE id_joueur = ? AND trou = ?
        ''', (id_joueur, trou))
        
        correction = cursor.fetchone()
        if correction:
            score_data.update({
                "correction": correction[0],
                "note_correction": correction[1],
                "date_correction": correction[2]
            })
            
        meilleurs_scores.append(score_data)
    
    manager.close()
    return jsonify({
        "joueur": {
            "id": id_joueur,
            "nom": joueur_info[0],
            "handicap": joueur_info[1]
        },
        "scores": meilleurs_scores
    })
@app.route('/classement-eclectique/pdf')
def export_classement_pdf():
    """Génère et télécharge le PDF du classement éclectique avec date de dernière manche"""
    manager = EclectiqueManager(db_path)
    
    # Récupérer la date de la dernière manche
    cursor = manager.conn.cursor()
    cursor.execute("SELECT date FROM manches ORDER BY date DESC LIMIT 1")
    result = cursor.fetchone()
    date_str = result[0].replace('-', '') if result else datetime.now().strftime("%Y%m%d")
    
    # Générer le PDF dans un dossier temporaire
    import tempfile
    import os
    temp_dir = tempfile.gettempdir()
    filename = os.path.join(temp_dir, f"classement_eclectique.pdf")
    
    success, result = manager.export_pdf(filename=filename)
    manager.close()
    
    if not success:
        return f"Erreur lors de la génération du PDF: {result}", 500
    
    # Renvoyer le fichier PDF avec nom personnalisé
    from flask import send_file
    download_name = f"classement_eclectique_{date_str}.pdf"
    return send_file(filename, as_attachment=True, download_name=download_name)
    
@app.route('/admin')
def admin():
    """Interface d'administration"""
    return render_template('admin.html')

@app.route('/import', methods=['POST'])
def import_file():
    """API pour importer un fichier Excel"""
    if 'file' not in request.files:
        return jsonify({"error": "Aucun fichier fourni"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nom de fichier vide"}), 400
    
    # Sauvegarder temporairement le fichier
    temp_path = os.path.join('/tmp', file.filename)
    file.save(temp_path)
    
    manager = EclectiqueManager(db_path)
    success, result = manager.import_manche(temp_path)
    manager.close()
    
    # Supprimer le fichier temporaire
    os.remove(temp_path)
    
    if success:
        return jsonify({"success": True, "manche_id": result})
    else:
        return jsonify({"success": False, "error": result})
    

@app.route('/import-html', methods=['GET', 'POST'])
def import_html():
    """Interface pour importer les joueurs à partir d'un fichier HTML"""
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({"error": "Aucun fichier fourni"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Nom de fichier vide"}), 400
        
        # Sauvegarder temporairement le fichier
        temp_path = os.path.join('/tmp', file.filename)
        file.save(temp_path)
        
        manager = EclectiqueManager(db_path)
        joueurs_aller, joueurs_retour, tous_joueurs = manager.importer_joueurs_html(temp_path)
        manager.close()
        
        # Supprimer le fichier temporaire
        os.remove(temp_path)
        
        return jsonify({
            "success": True, 
            "total_joueurs": len(tous_joueurs),
            "joueurs_aller": len(joueurs_aller),
            "joueurs_retour": len(joueurs_retour),
            "data": {
                "aller": [{"nom": nom, "handicap": hcp} for nom, hcp in joueurs_aller],
                "retour": [{"nom": nom, "handicap": hcp} for nom, hcp in joueurs_retour]
            }
        })
    
    return render_template('import_html.html')    

@app.route('/api/import-html', methods=['POST'])
def api_import_html():
    """API pour importer les joueurs à partir d'un fichier HTML"""
    if 'file' not in request.files:
        return jsonify({"error": "Aucun fichier fourni"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nom de fichier vide"}), 400
    
    # Sauvegarder temporairement le fichier
    temp_path = os.path.join('/tmp', file.filename)
    file.save(temp_path)
    
    manager = EclectiqueManager(db_path)
    joueurs_aller, joueurs_retour, tous_joueurs = manager.importer_joueurs_html(temp_path)
    manager.close()
    
    # Supprimer le fichier temporaire
    os.remove(temp_path)
    
    return jsonify({
        "success": True, 
        "total_joueurs": len(tous_joueurs),
        "joueurs_aller": len(joueurs_aller),
        "joueurs_retour": len(joueurs_retour),
        "data": {
            "aller": [{"nom": nom, "handicap": hcp} for nom, hcp in joueurs_aller],
            "retour": [{"nom": nom, "handicap": hcp} for nom, hcp in joueurs_retour]
        }
    })
    
# Routes à ajouter à app.py

@app.route('/flights')
def flights_management():
    """Interface de gestion des flights"""
    return render_template('flights.html')

@app.route('/api/save-flights', methods=['POST'])
def save_flights():
    """API pour sauvegarder les flights générés"""
    try:
        # Récupération des données
        data = request.json
        
        # Connexion à la base de données
        manager = EclectiqueManager(db_path)
        cursor = manager.conn.cursor()
        
        # Créer une entrée dans la table des départs
        cursor.execute("""
            INSERT INTO flights_departs (date, strategy, random_factor) 
            VALUES (?, ?, ?)
        """, (data.get('date'), data.get('strategy'), data.get('randomFactor')))
        
        depart_id = cursor.lastrowid
        
        # Sauvegarder les flights aller
        for i, flight in enumerate(data.get('aller', [])):
            flight_name = f"A{i+1}"
            
            # Enregistrer le flight
            cursor.execute("""
                INSERT INTO flights (id_depart, nom, type) 
                VALUES (?, ?, ?)
            """, (depart_id, flight_name, 'aller'))
            
            flight_id = cursor.lastrowid
            
            # Enregistrer les joueurs du flight
            for joueur in flight:
                cursor.execute("""
                    INSERT INTO flights_joueurs (id_flight, nom, handicap) 
                    VALUES (?, ?, ?)
                """, (flight_id, joueur['nom'], joueur['handicap']))
        
        # Sauvegarder les flights retour
        for i, flight in enumerate(data.get('retour', [])):
            flight_name = f"R{i+1}"
            
            # Enregistrer le flight
            cursor.execute("""
                INSERT INTO flights (id_depart, nom, type) 
                VALUES (?, ?, ?)
            """, (depart_id, flight_name, 'retour'))
            
            flight_id = cursor.lastrowid
            
            # Enregistrer les joueurs du flight
            for joueur in flight:
                cursor.execute("""
                    INSERT INTO flights_joueurs (id_flight, nom, handicap) 
                    VALUES (?, ?, ?)
                """, (flight_id, joueur['nom'], joueur['handicap']))
        
        manager.conn.commit()
        manager.close()
        
        return jsonify({"success": True, "id": depart_id})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/flights/print/<int:id_depart>')
def print_flights(id_depart):
    """Page d'impression des flights"""
    manager = EclectiqueManager(db_path)
    cursor = manager.conn.cursor()
    
    # Récupérer les informations du départ
    cursor.execute("SELECT date, strategy FROM flights_departs WHERE id = ?", (id_depart,))
    depart_info = cursor.fetchone()
    
    if not depart_info:
        manager.close()
        return "Départ introuvable", 404
    
    date, strategy = depart_info
    
    # Récupérer les flights aller
    cursor.execute("""
        SELECT id, nom FROM flights 
        WHERE id_depart = ? AND type = 'aller'
        ORDER BY nom
    """, (id_depart,))
    
    flights_aller = []
    for flight_id, flight_nom in cursor.fetchall():
        # Récupérer les joueurs de ce flight
        cursor.execute("""
            SELECT nom, handicap FROM flights_joueurs 
            WHERE id_flight = ?
            ORDER BY handicap
        """, (flight_id,))
        
        joueurs = [{"nom": nom, "handicap": handicap} for nom, handicap in cursor.fetchall()]
        
        flights_aller.append({
            "id": flight_id,
            "nom": flight_nom,
            "joueurs": joueurs
        })
    
    # Récupérer les flights retour
    cursor.execute("""
        SELECT id, nom FROM flights 
        WHERE id_depart = ? AND type = 'retour'
        ORDER BY nom
    """, (id_depart,))
    
    flights_retour = []
    for flight_id, flight_nom in cursor.fetchall():
        # Récupérer les joueurs de ce flight
        cursor.execute("""
            SELECT nom, handicap FROM flights_joueurs 
            WHERE id_flight = ?
            ORDER BY handicap
        """, (flight_id,))
        
        joueurs = [{"nom": nom, "handicap": handicap} for nom, handicap in cursor.fetchall()]
        
        flights_retour.append({
            "id": flight_id,
            "nom": flight_nom,
            "joueurs": joueurs
        })
    
    manager.close()
    
    return render_template('flights_print.html', 
                      id_depart=id_depart,  # Ajouter cette ligne
                      date=date, 
                      flights_aller=flights_aller, 
                      flights_retour=flights_retour)

@app.route('/flights/print/<int:id_depart>/pdf')
def export_flights_pdf(id_depart):
    """Génère et télécharge le PDF des flights"""
    manager = EclectiqueManager(db_path)
    cursor = manager.conn.cursor()
    
    # Récupérer les informations du départ
    cursor.execute("SELECT date FROM flights_departs WHERE id = ?", (id_depart,))
    result = cursor.fetchone()
    
    if not result:
        manager.close()
        return "Départ introuvable", 404
    
    date_str = result[0].replace("-", "")
    
    # Générer le PDF dans un dossier temporaire
    import tempfile
    import os
    temp_dir = tempfile.gettempdir()
    filename = os.path.join(temp_dir, f"flights_{date_str}.pdf")
    
    # Utiliser une fonction d'export PDF (à implémenter dans le manager)
    success, result = manager.export_flights_pdf(id_depart, filename)
    manager.close()
    
    if not success:
        return f"Erreur lors de la génération du PDF: {result}", 500
    
    # Renvoyer le fichier PDF
    from flask import send_file
    return send_file(filename, as_attachment=True, download_name=f"flights_{date_str}.pdf")    
    
if __name__ == '__main__':
    # Créer le dossier templates s'il n'existe pas
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Vous devez créer les fichiers templates/index.html et templates/admin.html
    app.run(debug=True, host='0.0.0.0', port=7001)