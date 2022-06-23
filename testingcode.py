import re


defend_response = {
    'agree1': ['medge'],
    'agree2': ['medgav'],
    'agree3': ['bevilj'],
    'contest1': ['bestr'],
    'contest2': ['mots'],
    'contest3': ['inkommit','egna','yrkand'],
    'contest4': ['egen','del','yrkat'],
    'agree4': ['varken','medg','bestr'],
    'tvistat':['part','tvist ']
    }

full = 'Stella mag kühe bestr . Das ist der trennsatz. Jetzt kommt was dazwischen. Das ist der  medg richtige: varken und so. '
cust= 'Das ist der trennsatz'

def findterms(stringlist, part):
    sentenceRes = []
    split = re.split('(?=[.]{1}\s[A-ZÅÐÄÖÉÜ]|\s\d\s)', part)
    stringlist = [x.lower() for x in stringlist]
    for sentence in split:
        sentence = sentence.lower() + '.'
        if all([x in sentence for x in stringlist]):
            sentenceRes.append(sentence)
    sentenceString = '.'.join(sentenceRes)
    return sentenceString


def get_response(fulltext, custodybattle):
    """
    Gets the case type variable only for those cases where a custody battle was
    found. Variable depends on whether defendant agreed to plaint, contested,
    or tvistat (=joint application). The numbers (agree1, agree2) have no meaning,
    just for coding purposes. 
    
    Pass: fulltext capitalized, custodybattle capitalized
    Returns variable outcome as string

    """
    
    fulltext = fulltext.split(custodybattle)[1]
    result = 999
    
    for resp, keyword in defend_response.items():
        print(findterms(keyword, fulltext))
        if (
                findterms(keyword, fulltext)
                and not ' inte ' in findterms(keyword, fulltext)
                ):
            result = resp
            break
        
    return result
    
res = get_response(full, cust)

print(res)
