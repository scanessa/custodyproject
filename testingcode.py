

s = 'a b c d'

if any([x in s for x in ['f', 'ö']]):
    print('yes')