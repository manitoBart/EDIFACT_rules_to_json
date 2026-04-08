import json, re

def parse_test(content):
    segments_db = {}
    current_seg = None
    current_composite = None
    clean_content = re.sub(r'^[+\*#X-]\s+', '', content, flags=re.MULTILINE)
    for line in clean_content.splitlines():
        line = line.rstrip()
        if not line.strip() or 'Function:' in line or 'Note:' in line:
            continue
        seg_m = re.match(r'^\s+([A-Z]{3})(?:\s+|$)(.*)', line)
        if seg_m:
            current_seg = seg_m.group(1)
            segments_db[current_seg] = []
            current_composite = None
            continue
        if not current_seg:
            continue
        comp_m = re.search(r'^\s*(\d{3})?\s*([CS][0-9]{3})\s+(.*?)\s+([MC])(?:\s|$)', line)
        if comp_m:
            c_pos, c_id, c_name, c_status = comp_m.groups()
            current_composite = {'id': c_id, 'name': c_name.strip(), 'type': 'composite', 'mandatory': c_status=='M', 'position': c_pos, 'sub_elements': []}
            segments_db[current_seg].append(current_composite)
            continue
        item_m = re.match(r'^(\d{3})\s+([0-9]{4})\s+(.*?)\s+([MC])(?:\s+([a-z0-9\.]+))?', line.strip())
        if item_m:
            i_pos, i_id, i_name, i_status, i_fmt = item_m.groups()
            current_composite = None  # element avec position = niveau segment
        else:
            item_m2 = re.match(r'^\s{2,}([0-9]{4})\s+(.*?)\s+([MC])(?:\s+([a-z0-9\.]+))?', line)
            if item_m2:
                i_pos = None
                i_id, i_name, i_status, i_fmt = item_m2.groups()
            else:
                continue
        item_data = {'id': i_id, 'name': i_name.strip(), 'mandatory': i_status=='M', 'format': i_fmt or 'unknown', 'position': i_pos}
        if current_composite is not None:
            current_composite['sub_elements'].append(item_data)
        else:
            item_data['type'] = 'simple'
            segments_db[current_seg].append(item_data)
    return segments_db

with open('segments_def.txt', 'r', encoding='utf-8') as f:
    content = f.read()

db = parse_test(content)
print('Segments:', len(db))
print('ADR elements:')
print(json.dumps(db.get('ADR', []), indent=2, ensure_ascii=False))
print('EQD elements:')
print(json.dumps(db.get('EQD', []), indent=2, ensure_ascii=False))
