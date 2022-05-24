# -*- coding: utf-8 -*-
"""
Created on Tue May 24 17:37:30 2022

@author: ifau-SteCa
"""

from fuzzywuzzy import process
from fuzzywuzzy import fuzz
import pandas as pd
JUDGE_LIST = "P:/2020/14/Data/Judges/list_of_judges_cleaned.xls"
cutoff = 70


judge1 = ['2 juli 2010. Prövningstillstånd krävs', '\nCH a >\nVÄX | GAN\n\nOla Je onshammar\n']

judge2 = ['krävs,\n', 'juli\n', 'ite\nmag"\n', 'fn\n']

judge3 = ['ka', 'inkoramit', 'juli', '2010.', 'j', 'y\n\nnn\n\n7\n']

alljudges = judge1 + judge2 + judge3
print("all judges: " , alljudges)

digital_judges = pd.read_excel(JUDGE_LIST)

for _, row in digital_judges.iterrows():
    
    match = row['judge']
    match1 = process.extract(match,alljudges)
        
    highest_match = sorted(match1, key=lambda x: x[1], reverse = True)
    highest_match = highest_match[0] #isolate score of highest match
        
    if highest_match[1] >= cutoff and len(highest_match[0]) > 5:
        comp_match = fuzz.partial_ratio(match, highest_match[0])
        if comp_match > cutoff:
            judge_name = match
            found = 1
            print("MATCH: ", match, highest_match, comp_match)



print("Judge name: ", judge_name)