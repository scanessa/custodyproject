# -*- coding: utf-8 -*-
"""
Created on Mon Jun 13 16:52:23 2022

@author: ifau-SteCa
"""
from transformers import pipeline
import itertools
import re 

NLP = pipeline('ner', model='KB/bert-base-swedish-cased-ner', tokenizer='KB/bert-base-swedish-cased-ner')
plaint_name = ['Mikael']
defend_name = ['Emma']
ruling_og = "Vårdnad om Björn Blomqvist och Tim-Rob Gymnich skall tillkomma Mikael Gymnich och Emma Gymnich gemensamt. Hi."
year = 2010

def word_classify(text, entity_req):
    """
    Inputs:
        - text: string that should be classified (must pass with ORIGINAL CASING ie upper case for names)
        - entity_req: required entity, pass as string; options: PER (person), 
        LOC (location), score 0-1, word (string)
    
    Returns:
        - List with lists of entities with consecutive indices that fulfull the entity requirement
        (person strings, location strings) if found, if required entity not found, returns None
    """
    
    joined_text = []
    split_text = NLP(text)
    in_word=False

    # Filter out items of unwanted categories
    if not entity_req == '': 
        clean_list = [x for x in split_text if x['entity'] == entity_req]
    else:
        clean_list = split_text

    # Group consecutive items (words)
    grouped = [[v for k, v in g] for k, g in itertools.groupby(enumerate(clean_list), lambda v: v[0] - v[1]['index'])]

    # Join tokenized list
    for lst in grouped:
        
        joined = []
        
        for i,token in enumerate(lst):
            if token['entity'] == 'O':
                in_word = False
                continue
        
            if token['word'].startswith('##'):
                if not in_word:
                    joined += [ split_text[i-1] ]
                    joined[-1]['entity'] = token['entity']
                
                joined[-1]['word'] += token['word'][2:]
            else:
                joined += [ token ]
    
            in_word = True
            
        joined_text.append(joined)
    
    return joined_text

def get_childnos(ruling_og, year):
    """
    Search for ID numbers in ruling (would only be given for kids) and return
    dict with ID as index, names for each index added in get_childname
    """
    childid_name = {}

    childnos = re.findall('\d{6,8}\s?.\s?\d{3,4}', ruling_og.lower())
    childnos = [x.replace(' ', '') for x in childnos]
    childnos = [x for x in childnos if not (x in set() or set().add(x))]

    for num in childnos:
        if len(re.split('\D', num)[0]) == 8:
            childyear = num[:4]
        else:
            childyear = '19'+num[:2] if int(num[:2])>40 else '20'+num[:2]
        
        age = int(year) - int(childyear)
        
        if 0 < age < 18:
            childid_name[num] = ''

    return childid_name

def findfirst(stringlist, part):
    sentenceRes = []
    split = re.split('(?=[.]{1}\s[A-ZÅÐÄÖÉÜ1-9]|\s\d\s)', part)
    for sentence in split:
        if all([x in sentence.lower() for x in stringlist]):
            sentenceRes.append(sentence)
    if sentenceRes:
        sentenceString = sentenceRes[0]
    else:
        sentenceString = ''
    return sentenceString


def get_childname(ruling_og, plaint_name, defend_name):
    """
    Extract child ID's first from ruling, if not found there from full text,
    otherwise get child's name and use that as ID
    """
    childid_name = get_childnos(ruling_og, year)
    updated_ruling = ruling_og
    
    if childid_name:
        
        for i in childid_name:
    
            relev = updated_ruling.split(i)[0]
            p_name = word_classify(relev, "PER")[0]
            names = [x['word'] for x in p_name]
            
            child_first = [x for x in names if x[0:3].upper() == x[0:3]]
            
            if not child_first:
                child_first = names[0]
            else:
                child_first = child_first[0].capitalize()

            childid_name[i] = child_first
            
            # Remove used part of string from ruling to look for new names
            updated_ruling = ' '.join([x for x in updated_ruling.split(i) if not x == relev])

    else:
        for term in ["vård", "umgänge", "boende"]:
            relev = findfirst([term],ruling_og)
            if relev:
                break
            else:
                relev = ruling_og
        print(relev)
        p_name = word_classify(relev, "PER")
        pd_names = plaint_name + defend_name
        
        for x in p_name:
            name = [n['word'] for n in x]
            if set(name).isdisjoint(pd_names):
                joined = ' '.join(name)
                joined = joined.replace(' - ', '-')
                childid_name[joined] = joined

    return childid_name
    
    

res = get_childname(ruling_og, plaint_name, defend_name)
print("RES: ",res)
