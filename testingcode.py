import re
from itertools import chain

def findterms(stringlist, part):
    sentenceRes = []
    split = re.split('(?=[.]{1}\s+\n*[A-ZÅÐÄÖÉÜ]|\s\d\s)', part)
    stringlist = [x.lower() for x in stringlist]
    for sentence in split:
        sentence = sentence.lower() + '.'
        if all([x in sentence for x in stringlist]):
            sentenceRes.append(sentence)
    sentenceString = '.'.join(sentenceRes)
    return sentenceString

before_plaint = 'vård om  hannis. Is gemensam'
plaint_first = ['stella','canessa']
defend_first = ['paula', 'banzhoff']

 
init_l_dict = {
    1: [
        ['vård', ' om ' , 'gemensam'],
        [ 'dom' ,'förordnades' ,'delad', 'vård', 'gemensam']
        ],
    2: [
        list(chain(*[['har','ensam','vårdnad','om'],plaint_first])),
        list(chain(*[['dom' ,'förordn' ,' ensam' ,'vård'],plaint_first])),
        ],
    3: [
        list(chain(*[['har','ensam','vårdnad','om'],defend_first])),
        list(chain(*[['dom' ,'förordn' ,' ensam' ,'vård'],defend_first])),
        ]
    }

init_l = 0
for key, val in init_l_dict.items():
    for item in val:
        target = findterms(item, before_plaint)
        if target:
            init_l = key

print(init_l)