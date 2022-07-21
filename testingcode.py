# -*- coding: utf-8 -*-
"""
Created on Wed Jul 20 16:50:34 2022

@author: ifau-SteCa
"""
import re
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

def searchkey(string, part, g):
    """
    Takes a searchstring and part, uses regex to search for string in part
    Returns string of search result group

    """
    finder = re.compile(string)
    match = finder.search(part)
    if match is not None:
        searchResult = match.group(g)
    else:
        searchResult = None
    return searchResult


part = '\nkär ande Dan Tykesson, .680131-4078\nDomar egatan I A\n256 59 HELSINGBORG\nOmbud:\nidvokat Christina Sebelius-Frost\nAdvokatfirman Sebelius-Frost\nBOXx 1133\n51 II HELSINGBORG\nva.ramde\nEvamari Eriksson, 700312-3903\nSkaragatan 26\n232 63 HELSINGBORG\nOmbud:\nadvokat Stefan Rosell\nAdvokataktiebolaget Stefan Rosell\nBox 1323\n231 13 HELSINGBORG\n'
part1 = re.sub('[\n:./,!?()|]','',part)

a = searchkey("[a-z](\s)[a-z]", string, 1)
string = string.replace(a,"")

regex = re.compile("[a-z](\s)[a-z]", re.S)
part1 = regex.sub(lambda x: x.group(1).replace(" ", ""), part1)

part1 = 'x' + part1.lower() + 'xx'
part2 = part.split()

party_headings = ['mannen', 'hustrun', 'kärande', 'svarande', 'sökande']
#print(part1)

for p in party_headings:
    comp1 = fuzz.partial_ratio(p,part1)
    comp2 = fuzz.partial_ratio(p,part)
    if comp1 > 60 and comp2 < 100:
        match = process.extract(p, part2)
        #print(p, match)


