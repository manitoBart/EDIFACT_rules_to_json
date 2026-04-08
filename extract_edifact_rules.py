import json
import re

def parse_advanced_edifact(file_path):
    # Expression régulière adaptée aux fichiers UNECE (Position, Tag, Nom, Statut, Max)
    # Exemple : 0120   Segment group 1  -  -  -  -  -  -  -  -  -  -  - C  99
    line_pattern = re.compile(r"^(\d{4})\s+(.+?)\s+([MC])\s+(\d+)")

    root = []
    stack = [(0, root)] # (Niveau d'indentation/position, liste_cible)

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            clean_line = line.strip()
            match = line_pattern.match(clean_line)
            
            if not match:
                continue

            pos = int(match.group(1))
            label = match.group(2).strip()
            status = match.group(3)
            max_occ = int(match.group(4))

            # Création de l'objet
            node = {
                "pos": pos,
                "mandatory": (status == 'M'),
                "max_occurrence": max_occ
            }

            # Détection : Est-ce un Segment Group ou un Segment simple ?
            if "Segment group" in label:
                node["type"] = "group"
                node["id"] = label.split()[-1] # Récupère le numéro (ex: 1)
                node["children"] = []
                is_group = True
            else:
                node["type"] = "segment"
                node["tag"] = label.split()[0] # Récupère le tag (ex: BGM)
                node["description"] = " ".join(label.split()[1:])
                is_group = False

            # GESTION DE LA HIÉRARCHIE
            # On remonte la pile tant que la position actuelle est <= à la position du parent
            # Sauf pour le premier élément
            while len(stack) > 1 and pos <= stack[-1][0]:
                stack.pop()

            # On ajoute le nœud au parent actuel
            stack[-1][1].append(node)

            # Si c'est un groupe, il devient le nouveau parent pour les lignes suivantes
            if is_group:
                stack.append((pos, node["children"]))

    return root

# --- Exécution ---
# data = parse_advanced_edifact('votre_fichier.txt')
# print(json.dumps(data, indent=2))

# --- Utilisation ---
# 1. Copiez le contenu de la table "Message Structure" d'un message UNECE dans 'structure.txt'
# 2. Lancez le script
try:
    data = parse_advanced_edifact('structure.txt')
    with open('edifact_rules.json', 'w', encoding='utf-8') as jf:
        json.dump(data, jf, indent=2)
    print("Fichier JSON généré avec succès : edifact_rules.json")
except FileNotFoundError:
    print("Erreur : Créez d'abord un fichier 'structure.txt' avec le contenu de l'UNECE.")