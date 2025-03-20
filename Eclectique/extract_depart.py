import re
import argparse
from bs4 import BeautifulSoup

def extraire_joueurs_inscrits(fichier_html):
    """
    Extrait la liste des joueurs inscrits à partir d'un fichier HTML.
    
    Args:
        fichier_html (str): Chemin vers le fichier HTML
        
    Returns:
        list: Liste de tuples (nom_joueur, handicap)
    """
    # Lecture du fichier HTML
    try:
        with open(fichier_html, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except UnicodeDecodeError:
        # En cas d'erreur d'encodage, essayer avec latin-1
        with open(fichier_html, 'r', encoding='latin-1') as f:
            html_content = f.read()
            
    soup = BeautifulSoup(html_content, 'html.parser')
    
    joueurs = []
    
    # Chercher les liens qui contiennent les noms des joueurs
    links = soup.find_all('a', class_='buttonProfile')
    
    for link in links:
        texte = link.text.strip()
        
        # Extraction du nom et du handicap avec regex
        match = re.search(r'([^(]+)\s*\(([0-9,.]+)\)', texte)
        if match:
            nom = match.group(1).strip()
            handicap = match.group(2).strip()
            joueurs.append((nom, handicap))
    
    return joueurs

def main():
    # Définition des arguments
    parser = argparse.ArgumentParser(description='Extrait la liste des joueurs inscrits à partir d\'un fichier HTML.')
    parser.add_argument('fichier_html', help='Chemin vers le fichier HTML')
    parser.add_argument('-o', '--output', help='Fichier de sortie (optionnel)')
    
    args = parser.parse_args()
    
    # Extraction des joueurs
    joueurs = extraire_joueurs_inscrits(args.fichier_html)
    
    # Préparation de la sortie
    output = f"Nombre de joueurs inscrits: {len(joueurs)}\n"
    for i, (nom, handicap) in enumerate(joueurs, 1):
        output += f"{i}. {nom} - Handicap: {handicap}\n"
    
    # Affichage ou écriture dans un fichier
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"Résultats écrits dans {args.output}")
    else:
        print(output)
    
    return joueurs

if __name__ == "__main__":
    main()