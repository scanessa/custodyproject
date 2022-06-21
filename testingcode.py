import re 

address = '\nKärande\n\nMarie Åkesson, 670424-4042\nNordanväg 14 B -\n244 38 KÄVLINGE \nOmbud: .\n\nadvokaten Janet Hagbohm\nAdvokat Janet Hagbohm AB\nSödra Storgatan 23 =\n252 23 HELSINGBORG \nSvarande\n\nTommy Fröjd, 700829-4055\nOlstorpsvägen 16\n260 23 KÅGERÖD \nOmbud, tillika biträde enligt rättshjälpslagen:\nadvokaten Bertil Andersson\n\nAdvokatfirma Andersson & Sjöström\nParkgatan 2\n\n2061 31 LANDSKRONA \n vuOUOOj— —= QQ — "!/  S-FZnnnmo—=—=—===—=O ii\n'

split = '((.| |\t|\n)*?[0-9]{2}[ \t][A-ZÅÐÄÖÉÜÆØÞ][A-ZÅÐÄÖÉÜÆØÞa-zåäáïüóöéæøßþîčćžđšžůúýëçâêè]+)'
res = re.split(split, address)
res = [x for x in res if x if not x == " " if not 'saken' in x]
print(res)