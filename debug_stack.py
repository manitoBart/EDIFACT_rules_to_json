import re, json

content = open('d95b/IFCSUM_D.95B', 'r', encoding='latin-1').read()
content_merged = re.sub(r'\r?\n[ \t]{20,}', '-', content)

grp_children = {}
for m in re.finditer(r'(\d{4})\s+Segment group (\d+):\s+([A-Z0-9-]+)', content_merged):
    grp_num = int(m.group(2))
    members = m.group(3)
    children = set(int(x) for x in re.findall(r'SG(\d+)', members))
    grp_children[grp_num] = children

child_to_parent = {}
for parent, children in grp_children.items():
    for child in children:
        child_to_parent[child] = parent

line_re = re.compile(r'^\s*(\d{4})\s+(.+?)\s+([MC])\s+([\d]+)')
root = []
stack = [(0, root)]
out = open('debug_stack.txt', 'w', encoding='utf-8')

for line in content_merged.splitlines(keepends=True):
    m = line_re.match(line)
    if not m:
        continue
    label = m.group(2).strip()
    label = re.sub(r'^[*|\-+#]+\s*', '', label).strip()
    label = label.replace('\u013f', '').replace('\u0673', '').strip()

    if 'Segment group' in label:
        try:
            grp_num = int(label.split()[-1])
        except:
            continue
        parent_num = child_to_parent.get(grp_num, 0)
        stack_before = [s[0] for s in stack]

        while len(stack) > 1 and stack[-1][0] != parent_num:
            stack.pop()
        if stack[-1][0] != parent_num:
            while len(stack) > 1:
                stack.pop()
        if stack[-1][0] != parent_num:
            while len(stack) > 1:
                stack.pop()

        out.write(f"SG{grp_num}: parent={parent_num}, stack_before={stack_before}, stack_after={[s[0] for s in stack]}, added_to={stack[-1][0]}\n")

        node = {"type": "group", "id": str(grp_num), "children": []}
        stack[-1][1].append(node)
        stack.append((grp_num, node["children"]))

out.close()
print("done")
