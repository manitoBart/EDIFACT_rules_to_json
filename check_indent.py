lines = open('structure_message.txt', 'r', encoding='utf-8').readlines()
out = open('indent_check.txt', 'w', encoding='utf-8')
import re
for line in lines:
    m = re.match(r'^(\s*)(\d{4})\s+(.{0,40})', line)
    if m:
        indent = len(m.group(1))
        pos = m.group(2)
        label = m.group(3).strip()
        out.write(f"indent={indent:2d} pos={pos} label={label}\n")
out.close()
print("done")
