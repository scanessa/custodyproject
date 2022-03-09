# -*- coding: utf-8 -*-
"""
Created on Wed Mar  9 15:50:05 2022

@author: ifau-SteCa
"""
import re
ruling_og = 'Vårdnaden om Emil MÉXI-TOM Tom Sjursen, 1234567-000, Ida-Maria Maja Sjursen-Lila, 2234567-123, och Isak Sjursen ska tillkomma Patrik Kågebrand och Annette Sjursen gemensamt. Emil Sjursen, Ida Sjursen och Isak Sjursen ska ha sitt stadigvarande boende hos Stella Kågebrand.'
defend_full = 'patrik kågebrand'
plaint_full = 'annette sjursen'
ids = ['1234567-000','2234567-123']



sentence_parts = re.split('(?=[.]{1}\s[A-ZÅÐÄÖÉÜ])..|\d\s*,|\s[a-z]', ruling_og) 
for sentence in sentence_parts:
    for idchild in ids:
        if idchild[:-1] in sentence:
            names = []
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
            
            
                    
            print(idchild, child_first)

