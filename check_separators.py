import re

lines = open('structure_message.txt', 'r', encoding='utf-8').readlines()
out = open('separators.txt', 'w', encoding='utf-8')

line_re = re.compile(r'^\s*(\d{4})\s+(.+?)\s+([MC])\s+(\d+)')

for i, line in enumerate(lines):
    m = line_re.match(line)
    if m:
        label = m.group(2).strip()
        if 'Segment group' in label:
            # Regarder la ligne precedente
            prev = lines[i-1] if i > 0 else ''
            prev2 = lines[i-2] if i > 1 else ''
            grp_num = label.split()[-1]
            out.write(f"SG{grp_num} at pos {m.group(1)}\n")
            out.write(f"  prev-1: {repr(prev)}\n")
            out.write(f"  prev-2: {repr(prev2)}\n")
            out.write(f"  prev is blank: {prev.strip() == ''}\n")
            out.write(f"  prev is spaces-only: {len(prev.strip()) == 0 and len(prev) > 1}\n\n")

out.close()
print("done")
