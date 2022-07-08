from fuzzywuzzy import fuzz
from Levenshtein import distance

name1 = ['Jane', 'Miller', '-','Smith']
name = ['Jane', '-', 'Marie','Miller', '-','Smith']


new_name = []

for cur, nxt in zip (name, name [1:]):
    print(cur,nxt)
    if cur == '-':
        hyph = cur+nxt
        new_name.append(hyph)
        print("hyph: ", hyph)
    else:
        new_name.append(cur)
        print("cur: ", cur)
print(new_name)

"""
counter = 0

for n in name:
    for text in text1:
        comp = distance(text.strip(','), n)
        #print(n, text, comp)
        if comp < 2:
            counter += 1
            #print(counter)
            break
        
"""