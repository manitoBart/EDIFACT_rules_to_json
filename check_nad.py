import json, sys

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

    nads = find_all(d, 'NAD')

    with open('nad_check.json', 'w', encoding='utf-8') as f:
        json.dump({
            'count': len(nads),
            'first_elements': nads[0].get('elements', []) if nads else []
        }, f, indent=2, ensure_ascii=False)

    with open('nad_check.txt', 'w', encoding='utf-8') as f:
        f.write(f"NAD count: {len(nads)}\n")
        if nads:
            elems = nads[0].get('elements', [])
            f.write(f"elements count: {len(elems)}\n")
            for e in elems:
                f.write(f"  pos={e.get('position')} id={e.get('id')} name={e.get('name')} type={e.get('type')}\n")
                for s in e.get('sub_elements', []):
                    f.write(f"    sub: id={s.get('id')} name={s.get('name')}\n")

    print("done")

except Exception as e:
    with open('nad_error.txt', 'w', encoding='utf-8') as f:
        f.write(str(e))
    print("error:", e)
