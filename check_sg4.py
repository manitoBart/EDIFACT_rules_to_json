import re
content = open('d95b/IFCSUM_D.95B', 'r', encoding='latin-1').read()
merged = re.sub(r'\r?\n[ \t]{20,}', '-', content)
idx = merged.find('Segment group 4')
out = open('sg4_ctx.txt', 'w', encoding='utf-8')
out.write(repr(merged[idx-300:idx+300]))
out.close()
print("done")
