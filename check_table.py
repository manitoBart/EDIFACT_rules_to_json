import re

content = open('d95b/IFCSUM_D.95B', 'r', encoding='latin-1').read()
table_match = re.search(r'4\.3\.1.*?Segment table.*?\n(.*)', content, re.DOTALL)
table_content = table_match.group(1) if table_match else content

# Chercher SG4 dans table_content
idx = table_content.find('Segment group 4')
out = open('sg4_table.txt', 'w', encoding='utf-8')
out.write(f"Found at index: {idx}\n")
out.write(repr(table_content[max(0,idx-100):idx+200]))
out.close()
print("done")
