import re

content = open('d95b/IFCSUM_D.95B', 'r', encoding='latin-1').read()
content_merged = re.sub(r'\r?\n[ \t]{20,}', '-', content)

out = open('grp_out.txt', 'w', encoding='utf-8')
for m in re.finditer(r'(\d{4})\s+Segment group (\d+):\s+([A-Z0-9-]+)', content_merged):
    grp_num = int(m.group(2))
    members = m.group(3)
    children = re.findall(r'SG(\d+)', members)
    out.write(f'SG{grp_num} -> children: {children}\n')
    out.write(f'  members: {members[:100]}\n')
out.close()
print('done')
