import json

d = json.load(open('edifact_rules.json', 'r', encoding='utf-8'))

def print_structure(nodes, depth=0):
    for n in nodes:
        indent = '  ' * depth
        if n.get('type') == 'group':
            print(f"{indent}GROUP {n['id']} (pos={n['pos_msg']})")
            print_structure(n.get('children', []), depth + 1)
        else:
            print(f"{indent}SEG {n.get('tag')} (pos={n['pos_msg']})")

with open('structure_check.txt', 'w', encoding='utf-8') as f:
    def write_structure(nodes, depth=0):
        for n in nodes:
            indent = '  ' * depth
            if n.get('type') == 'group':
                f.write(f"{indent}GROUP {n['id']} (pos={n['pos_msg']})\n")
                write_structure(n.get('children', []), depth + 1)
            else:
                f.write(f"{indent}SEG {n.get('tag')} (pos={n['pos_msg']})\n")
    write_structure(d)

print("done")
