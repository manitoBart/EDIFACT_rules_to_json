import re

content = open('d95b/IFCSUM_D.95B', 'r', encoding='latin-1').read()

sections = ['4.1', '4.2', '4.3', '4.3.1']
for s in sections:
    idx = content.find(s)
    print(f"Section {s} at index {idx}: {repr(content[idx:idx+50])}")
