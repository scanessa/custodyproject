# initialize lists
test_list = ['gfg', 'is the', 'best', 'and', 'is so', 'popular']
indices = [0]

firsts = [x for x in test_list if 'is' in x]

for f in firsts:
    temp = test_list.index(f)
    indices.append(temp)

print(indices)

for i in indices:
    new = test_list[:i]
    print(new)



