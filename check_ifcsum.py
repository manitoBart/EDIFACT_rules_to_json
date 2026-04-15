lines = open('d95b/TRMD/IFCSUM_D.95B', 'r', encoding='latin-1').readlines()
out = open('ifcsum_raw.txt', 'w', encoding='utf-8')
for line in lines[:120]:
    out.write(repr(line) + '\n')
out.close()
print("done")
