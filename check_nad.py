import json, re

try:
    with open('edifact_rules.json', 'r', encoding='utf-8') as f:
        d = json.load(f)

    def find_all(nodes, tag):
        results = []
        for n in nodes:
            if n.get('tag') == tag:
                results.append(n)
            if 'children' in n:
                results += find_all(n['children'], tag)
        return results

    for tag in ['BGM', 'NAD']:
        items = find_all(d, tag)
        with open(f'{tag.lower()}_check.txt', 'w', encoding='utf-8') as f:
            f.write(f"{tag} count: {len(items)}\n")
            if items:
                elems = items[0].get('elements', [])
                f.write(f"elements count: {len(elems)}\n")
                for e in elems:
                    f.write(f"  pos={e.get('position')} id={e.get('id')} name={e.get('name')} type={e.get('type')}\n")
                    for s in e.get('sub_elements', []):
                        f.write(f"    sub: id={s.get('id')} name={s.get('name')}\n")

    # Verifier quel segments_def est charge
    with open('segments_def.txt', 'r', encoding='utf-8') as f:
        first_bgm = ''
        for line in f:
            if 'BGM' in line and 'BEGINNING' in line:
                first_bgm = line.strip()
                break
    with open('debug_source.txt', 'w', encoding='utf-8') as f:
        f.write(f"BGM line in segments_def: {first_bgm}\n")

    print("done")

except Exception as e:
    with open('check_error.txt', 'w', encoding='utf-8') as f:
        f.write(str(e))
    print("error:", e)
