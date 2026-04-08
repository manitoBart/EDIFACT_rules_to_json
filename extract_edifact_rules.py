import json
import re

import json
import re

def parse_segments_ultimate(segment_content, element_repo):
    segments_db = {}
    current_seg = None
    current_composite = None
    
    # Nettoyage des caractères spéciaux de l'UNECE (+, *, #, X) en début de ligne
    clean_content = re.sub(r'^[+\*#X-]\s+', '', segment_content, flags=re.MULTILINE)

    for line in clean_content.splitlines():
        line = line.rstrip()
        if not line.strip() or "Function:" in line or "Note:" in line:
            continue

        # 1. SEGMENT (ex:      ADR    ADDRESS) -> 3 lettres majuscules, potentiellement précédées d'espaces
        seg_m = re.match(r"^\s+([A-Z]{3})(?:\s+|$)(.*)", line)
        if seg_m:
            current_seg = seg_m.group(1)
            segments_db[current_seg] = []
            current_composite = None
            continue

        if not current_seg: continue

        # 2. COMPOSITE (ex: 010   C817  ADDRESS USAGE) -> ID commencant par C ou S suivi de 3 chiffres
        comp_m = re.match(r"^\s*(\d{3})\s+([CS][0-9]{3})\s+(.*?)\s+([MC])\s*$", line)
        if comp_m:
            c_pos, c_id, c_name, c_status = comp_m.groups()
            current_composite = {
                "id": c_id,
                "name": c_name.strip(),
                "type": "composite",
                "mandatory": c_status == 'M',
                "position": c_pos,
                "sub_elements": []
            }
            segments_db[current_seg].append(current_composite)
            continue

        # 3. SOUS-ÉLÉMENT ou ÉLÉMENT SIMPLE
        # Cas A : avec position (ex: "010   3164  CITY NAME  C  an..35")
        item_m = re.match(r"^(\d{3})\s+([0-9]{4})\s+(.*?)\s+([MC])(?:\s+([a-z0-9\.]+))?", line.strip())
        if item_m:
            i_pos, i_id, i_name, i_status, i_fmt = item_m.groups()
            current_composite = None  # un élément avec position est toujours au niveau segment
        else:
            # Cas B : sans position, indenté (ex: "      3299   Address purpose, coded  C  an..3")
            item_m2 = re.match(r"^\s{2,}([0-9]{4})\s+(.*?)\s+([MC])(?:\s+([a-z0-9\.]+))?", line)
            if item_m2:
                i_pos = None
                i_id, i_name, i_status, i_fmt = item_m2.groups()
            else:
                continue

        # Récupération du format (soit dans la ligne, soit dans EDED)
        final_fmt = i_fmt if i_fmt else element_repo.get(i_id, {}).get('format', 'unknown')
        
        item_data = {
            "id": i_id,
            "name": i_name.strip(),
            "mandatory": i_status == 'M',
            "format": final_fmt,
            "position": i_pos
        }

        # Si on est dans un composite, on l'ajoute dedans
        if current_composite is not None:
            current_composite["sub_elements"].append(item_data)
        else:
            # Sinon c'est un élément simple du segment
            item_data["type"] = "simple"
            segments_db[current_seg].append(item_data)

    return segments_db

def build_final_json(message_struct_path, segments_db):
    line_re = re.compile(r"^(\d{4})\s+(.+?)\s+([MC])\s+(\d+)")
    root = []
    stack = [(0, root)]

    with open(message_struct_path, 'r', encoding='utf-8') as f:
        for line in f:
            m = line_re.match(line.strip())
            if not m: continue
            
            pos_val = int(m.group(1))
            label = m.group(2).strip()
            status = m.group(3)
            max_occ = int(m.group(4))

            node = {"pos_msg": m.group(1), "mandatory": status == 'M', "max": max_occ}

            if "Segment group" in label:
                node.update({"type": "group", "id": label.split()[-1], "children": []})
                is_group = True
            else:
                parts = label.split(maxsplit=1) # Sépare "UNH Message header" en ["UNH", "Message header"]
                tag = parts[0]
                # Si parts[1] existe, c'est le nom, sinon on met le tag par défaut
                name = parts[1] if len(parts) > 1 else tag
                
                node.update({
                   "type": "segment", 
                   "tag": tag, 
                   "name": name,
                   "elements": segments_db.get(tag, [])})
                is_group = False

            while len(stack) > 1 and pos_val <= stack[-1][0]:
                stack.pop()
            stack[-1][1].append(node)
            if is_group:
                stack.append((pos_val, node["children"]))
    return root

try:
    # 1. Charger le dictionnaire des formats (EDED)
    element_repo = {}
    with open('elements_def.txt', 'r', encoding='utf-8') as f:
        el_re = re.compile(r"^(\d{4})\s+(.*?)\s+([MC])\s+([a-z]+\.?\d*)")
        for line in f:
            m = el_re.match(line.strip())
            if m:
                id_el, name, _, fmt = m.groups()
                element_repo[id_el] = {"name": name.strip(), "format": fmt}

    # 2. Charger les segments avec tes composites imbriqués (EDSD)
    with open('segments_def.txt', 'r', encoding='utf-8') as f:
        seg_content = f.read()
    
    # ATTENTION : On passe bien l'objet element_repo ici
    segments_db = parse_segments_ultimate(seg_content, element_repo)
    
    print(f"Segments analysés : {len(segments_db)}")

    # 3. Construire la structure finale du message
    data = build_final_json('structure_message.txt', segments_db)
    
    # 4. Sauvegarder
    with open('edifact_rules.json', 'w', encoding='utf-8') as jf:
        json.dump(data, jf, indent=2, ensure_ascii=False)
        
    print("Succès ! Le fichier edifact_rules.json a été créé avec les sub_elements.")

except FileNotFoundError as e:
    print(f"Erreur : Fichier introuvable -> {e.filename}")
except Exception as e:
    print(f"Une erreur est survenue : {e}")