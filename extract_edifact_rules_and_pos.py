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
    line_re = re.compile(r"^(\d{4})\s+(.+?)\s+([MC])\s+(\d+)")
    root = []
    stack = [(0, root)]

    with open(message_struct_path, 'r', encoding='utf-8') as f:
        for line in f:
            m = line_re.match(line.strip())
            if not m:
                continue

            pos_val = int(m.group(1))
            label = m.group(2).strip()
            status = m.group(3)
            max_occ = int(m.group(4))

            node = {"pos_msg": m.group(1), "mandatory": status == 'M', "max": max_occ}

            # Supprimer les marqueurs EDIFACT (* | -) en debut de label
            label = re.sub(r'^[*|\-+#]+\s*', '', label).strip()

            if "Segment group" in label:
                node.update({"type": "group", "id": label.split()[-1], "children": []})
                is_group = True
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

    # 2. Charger les segments (EDSD)
    with open('segments_def.txt', 'r', encoding='utf-8') as f:
        seg_content = f.read()

    segments_db = parse_segments_ultimate(seg_content, element_repo)
    print(f"Segments analysés : {len(segments_db)}")

    # 3. Construire la structure finale du message
    data = build_final_json('structure_message.txt', segments_db)

    # 4. Sauvegarder
    with open('edifact_rules.json', 'w', encoding='utf-8') as jf:
        json.dump(data, jf, indent=2, ensure_ascii=False)

    print("Succès ! Le fichier edifact_rules.json a été créé.")

except FileNotFoundError as e:
    print(f"Erreur : Fichier introuvable -> {e.filename}")
except Exception as e:
    print(f"Une erreur est survenue : {e}")
