import json
import re


def parse_segments_ultimate(segment_content, element_repo):
    segments_db = {}
    current_seg = None
    current_composite = None

    # Fusionner les lignes de continuation avec la ligne precedente
    merged_lines = []
    for line in segment_content.splitlines():
        # Ligne de continuation : tres indentee, pas de chiffres en debut
        if re.match(r'^\s{12,}[a-zA-Z]', line) and merged_lines:
            merged_lines[-1] = merged_lines[-1].rstrip() + ' ' + line.strip()
        else:
            merged_lines.append(line)

    for line in merged_lines:
        line = line.rstrip()
        if not line.strip() or "Function:" in line or "Note:" in line:
            continue

        # 1. SEGMENT (ex: "     ADR    ADDRESS" ou "    | NAD    NAME AND ADDRESS")
        seg_m = re.match(r"^[\s|+*#X-]*([A-Z]{3})(?:\s+|$)(.*)", line)
        if seg_m:
            current_seg = seg_m.group(1)
            segments_db[current_seg] = []
            current_composite = None
            continue

        if not current_seg:
            continue

        # 2. COMPOSITE (ex: "020    C082 NAME   C    1" ou "020   C082  NAME   C  ")
        comp_m = re.match(r"^\s*(\d{3})\s+([CS][0-9]{3})\s+(.*?)\s+([MC])(?:\s+\d+)?\s*$", line)
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

        # 3. ELEMENT SIMPLE avec position (ex: "010    3035 NAME   M    1 an..3" ou "010   3035  NAME   M  an..3")
        item_m = re.match(r"^(\d{3})\s+([0-9]{4})\s+(.*?)\s+([MC])(?:\s+\d+)?(?:\s+([a-z][a-z0-9\.]+))?", line.strip())
        if item_m:
            i_pos, i_id, i_name, i_status, i_fmt = item_m.groups()
            current_composite = None  # element avec position = niveau segment
        else:
            # 4. SOUS-ELEMENT sans position, indenté (ex: "       3039  Party id.   M      an..35")
            item_m2 = re.match(r"^\s{2,}([0-9]{4})\s+(.*?)\s+([MC])\s+(?:[a-z][a-z0-9\.]+)?", line)
            if item_m2:
                i_pos = None
                i_id, i_name, i_status = item_m2.group(1), item_m2.group(2), item_m2.group(3)
                # format est après le statut et les espaces
                fmt_m = re.search(r'[MC]\s+([a-z][a-z0-9\.]+)', line)
                i_fmt = fmt_m.group(1) if fmt_m else None
            else:
                continue

        final_fmt = i_fmt if i_fmt else element_repo.get(i_id, {}).get('format', 'unknown')
        item_data = {
            "id": i_id,
            "name": i_name.strip(),
            "mandatory": i_status == 'M',
            "format": final_fmt,
            "position": i_pos
        }

        if current_composite is not None:
            current_composite["sub_elements"].append(item_data)
        else:
            item_data["type"] = "simple"
            segments_db[current_seg].append(item_data)

    return segments_db


def build_final_json(message_struct_path, segments_db):
    line_re = re.compile(r"^\s*(\d{4})\s+(.+?)\s+([MC])\s+([\d]+)")
    # Extraire la hierarchie depuis les descriptions de groupes (ex: "Segment group 2:  GOR-...-SG3")
    grp_children = {}  # grp_num -> set of child grp nums
    # Les descriptions peuvent s'etendre sur plusieurs lignes (continuation indentee)
    grp_desc_re = re.compile(r'(\d{4})\s+Segment group (\d+):\s+((?:[A-Z0-9-]+\n?\s*)+)', re.MULTILINE)

    content = open(message_struct_path, 'r', encoding='latin-1').read()
    # Fusionner toutes les lignes de continuation (tres indentees) avec la ligne precedente
    content_merged = re.sub(r'\r?\n[ \t]{20,}', '-', content)

    for m in re.finditer(r'(\d{4})\s+Segment group (\d+):\s+([A-Z0-9-]+)', content_merged):
        grp_num = int(m.group(2))
        members = m.group(3)
        children = set(int(x) for x in re.findall(r'SG(\d+)', members))
        grp_children[grp_num] = children

    # Construire un mapping enfant -> parent
    child_to_parent = {}
    for parent, children in grp_children.items():
        for child in children:
            child_to_parent[child] = parent

    root = []
    stack = [(0, root)]  # (grp_num, liste_enfants)
    grp_nodes = {}  # grp_num -> node

    # Parser uniquement la section 4.3.1 (segment table) - chercher l'en-tete du tableau
    table_match = re.search(r'Pos\s+Tag Name.*?\n(.*)', content, re.DOTALL)
    table_content = table_match.group(1) if table_match else content
    lines = table_content.splitlines(keepends=True)
    for line in lines:
        m = line_re.match(line)
        if not m:
            continue

        label = m.group(2).strip()
        status = m.group(3)
        max_occ_str = re.sub(r'[^\d]', '', m.group(4))
        if not max_occ_str:
            continue
        max_occ = int(max_occ_str)
        pos_str = m.group(1)

        node = {"pos_msg": pos_str, "mandatory": status == 'M', "max": max_occ}
        label = re.sub(r'^[*|\-+#]+\s*', '', label).strip()
        label = label.replace('\u013f', '').replace('\u0673', '').strip()

        if "Segment group" in label:
            grp_match = re.search(r'Segment group\s+(\d+)', label)
            if not grp_match:
                continue
            grp_num = int(grp_match.group(1))
            node.update({"type": "group", "id": str(grp_num), "children": []})
            grp_nodes[grp_num] = node

            # Trouver le parent de ce groupe
            parent_num = child_to_parent.get(grp_num, 0)

            # Remonter la pile jusqu'au parent
            while len(stack) > 1 and stack[-1][0] != parent_num:
                stack.pop()
            # Si le parent n'est pas dans la pile, remonter a la racine
            if stack[-1][0] != parent_num:
                while len(stack) > 1:
                    stack.pop()

            stack[-1][1].append(node)
            stack.append((grp_num, node["children"]))
        else:
            parts = label.split(maxsplit=1)
            tag = parts[0]
            name = parts[1] if len(parts) > 1 else tag
            node.update({
                "type": "segment",
                "tag": tag,
                "name": name,
                "elements": segments_db.get(tag, [])
            })
            stack[-1][1].append(node)

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

    # 2. Charger les segments (EDSD)
    with open('segments_def.txt', 'r', encoding='utf-8') as f:
        seg_content = f.read()

    segments_db = parse_segments_ultimate(seg_content, element_repo)
    print(f"Segments analysés : {len(segments_db)}")

    # 3. Construire la structure finale du message
    data = build_final_json('d00b/COPARN_D.00B', segments_db)

    # 4. Sauvegarder
    with open('edifact_rules.json', 'w', encoding='utf-8') as jf:
        json.dump(data, jf, indent=2, ensure_ascii=False)

    print("Succès ! Le fichier edifact_rules.json a été créé.")

except FileNotFoundError as e:
    print(f"Erreur : Fichier introuvable -> {e.filename}")
except Exception as e:
    print(f"Une erreur est survenue : {e}")
