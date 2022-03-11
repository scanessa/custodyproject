# -*- coding: utf-8 -*-
"""
Created on Wed Mar  9 15:50:05 2022

@author: ifau-SteCa
"""
import re
ruling_og = '1. Vårdnaden om Nora Maria Slättberg, Tim Slättberg, och Mark Slättberg ska tillkomma Nicole Slättberg och Simon Zeybrandt gemensamt.' 
defend_full = 'nicole slättberg'
plaint_full = 'simon zeybrand'
childid_name = {}
year = 2010


def get_childnos(year):
    """
    Search for ID numbers in ruling (would only be given for kids) and return
    dict with ID as index, names for each index added in get_childname
    """
    childid_name = {}

    childnos = re.findall('\d{6,8}\s?.\s?\d{3,4}', ruling_og.lower())
    childnos = [x.replace(' ', '') for x in childnos]
    childnos = set(childnos)

    for num in childnos:
        if len(re.split('\D', num)[0]) == 8:
            childyear = num[:4]
        else:
            childyear = '19'+num[:2] if int(num[:2])>40 else '20'+num[:2]

        age = int(year) - int(childyear)

        childid_name[num] = '' if age < 18 else childid_name

    return childid_name
    
def get_childname(ruling_og,defend_full,plaint_full):
    """
    Extract child ID's first from ruling, if not found there from full text,
    otherwise get child's name and use that as ID
    """
    childid_name = get_childnos(year)
    names = []

    if childid_name:

        sentence_parts = re.split('(?=[.]{1}\s[A-ZÅÐÄÖÉÜ])..|\d\s*,|\s[a-z]', ruling_og)

        for i in childid_name:
            sentence = str([x for x in sentence_parts if i[:-1] in x])
            childid_name[i] = ''

            for word in sentence.split():

                if (
                    word[0].isupper()
                    and not any([x in word.lower() for x in defend_full.split()])
                    and not any([x in word.lower() for x in plaint_full.split()])
                    ):

                    names.append(word)

            child_first = [x for x in names if x[0:3].upper() == x[0:3]]

            if not child_first:
                child_first = names[0].lower()
            else:
                child_first = child_first[0].lower()

            childid_name[i] = child_first
            names.clear()

    if not childid_name:

        custody_sentences = []
        sentence_parts = re.split('(?=[.]{1}\s[A-ZÅÐÄÖÉÜ])..', ruling_og)

        for sentence in sentence_parts:
            if 'vård' in sentence or 'Vård' in sentence:
                custody_sentences.append(sentence)

        custody_sentences = ('.'.join(custody_sentences)).split(' ')[1:]
        custody_sentences = [x for x in custody_sentences if x]

        for word in custody_sentences:
            word = word.strip()

            if (
                word[0].isupper()
                and not any([x in word.lower() for x in defend_full.split()])
                and not any([x in word.lower() for x in plaint_full.split()])
                or word == 'och'
                ):
                names.append(word)

            elif word[-1] == ',':
                names.append(word.strip()[-1])

        names = re.split(',|och', ' '.join(names))
        names = [x for x in names if x.strip()]

        for name in names:
            name = name.split()[0]
            childid_name[name] = name

    childid_name = {'not found':'not found'} if not childid_name else childid_name

    return childid_name

print(get_childname(ruling_og, defend_full, plaint_full))
