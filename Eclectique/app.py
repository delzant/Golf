from flask import Flask, render_template, jsonify, request
import os
from eclectique_manager import EclectiqueManager

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
    
    manager.close()
    return render_template('index.html', joueurs=joueurs_avec_scores, pars=pars)

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

if __name__ == '__main__':
    # Créer le dossier templates s'il n'existe pas
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Vous devez créer les fichiers templates/index.html et templates/admin.html
    app.run(debug=True, host='0.0.0.0', port=7001)