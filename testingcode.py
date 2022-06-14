# -*- coding: utf-8 -*-
"""
Created on Mon Jun 13 16:52:23 2022

@author: ifau-SteCa
"""
import re
header = '\nKärande\n\nShukria HASSAN, 660101-5388\nRandersgatan 63\n\n164 48 KIST E\nSvarande\n\nSadik Salih, 560701-6853\nGinstvägen 6 A\n\n311 33 Falkenberg\nMANNER ENTRTTTROOEOONEEENEEETT KERO\n'


p1 = re.findall(r'((.| |\t|\n)*?[0-9]{2}[ \t][A-ZÅÐÄÖÉÜÆØÞ][ A-ZÅÐÄÖÉÜÆØÞa-zåäáïüóöéæøßþîčćžđšžůúýëçâêè]*)', header)

parties = [item for tpl in p1 for item in tpl if not item == " "]
print(parties)
plaint = ['Shukria', 'Hassan']

plaint_part = [part for part in parties if all(x.lower() in part.lower() for x in plaint)]
print(plaint_part)
