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


judge_s = 'ANVISNING FÖR ÖVERKLAGANDE, se bilaga (Dv 401)\nÖverklagande ges in till tingsrätten senast den 25 juni 2007 och ställs till Hovrätten för\nför\n den\n juni\n ställs\n sverige.\n /\nges in till den 25 juni 2007 ställs till för\n\nvästra sverige.\n\ndh\n\nf\n\ndh\n\nmt\n\njell\n\n/\n\nilsson\n\n-\n'


digital_judges = pd.read_excel(JUDGE_LIST)
for _, row in digital_judges.iterrows():
    match = row['judge']
    comp_match = fuzz.partial_ratio(match, judge_s)
    
    if comp_match > 60:
        print(match, comp_match)


""" OLD

def get_judge_scans(judge1, judge2, judge3):
    
    Gets judges name from scanned documetn by going through different text
    parts, judge1 = judge_string, judge2 draws tight bounding boxes wiht 9x9
    kernal in OCR module around text and parses the text in those tight boxes,
    judge3 parses as much text as it can get from the whole page without any
    boxes.
    
    Code then takes list of digital judges generated with STATA, compares string
    in judge1/2/3 list with each name and at similarity CUTOFF = 70 AND 
    assigns judge_name = match
    
    alljudges = judge1.split(',') + judge2 + judge3 # THIS SPLITS TOO MUCH
    judge_title = 'N/A'
    found = 0
    cutoff = 70
    
    print("Judge String: ", alljudges)

    digital_judges = pd.read_excel(JUDGE_LIST)
    
    for _, row in digital_judges.iterrows():
        
        match = row['judge']
        match1 = process.extract(match, alljudges)
        highest_match = sorted(match1, key=lambda x: x[1], reverse = True)
        highest_match = highest_match[0] #isolate score of highest match
        
        if highest_match[1] > cutoff and len(highest_match[0]) > 5:
            comp_match = fuzz.partial_ratio(match, highest_match[0])
            if comp_match > cutoff:
                judge_name = match
                found = 1
                print(match, highest_match)

    if found == 0:
        try:
            print("try1")
            judge_name = ((dictloop(judgesearch, judge1, 1,
                                 exclude_judge)).split('\n'))[0]
            judge_name = judge_name.lower().strip()
        except:
            print("except1")
            judgepage = ' '.join(judge2)
            judge_name = judgepage.replace("\n", " ")

    print("Judge name: ", judge_name)
    return judge_name, judge_title


"""
