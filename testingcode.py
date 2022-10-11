import re

part_test = '.\nParterna ingick äktenskap den 27 december 1989 och har i äktenskapet sonen Artur,\nfödd den 17 oktober 1992)\nEfter gemensam ansökan av parterna med yrkande om äktenskapsskillnad m.m. har\ntingsrätten beslutat om betänketid, som löpt sedan den 28 juli 1994) Vidare har\ntingsrätten, i enlighet med vad parterna överenskommit, i interimistiskt beslut den 29\njuli 1994 förordnat att Anahid Baghomian Sangbarani skall bo kvar i parternas gemensamma bostad till dess bodelning skett samt att Jirayer Moussakanian till Anahid\nBaghomian Sangbarani skall utge månatligt underhållsbidrag för Artur med 1040 kr.\nAnahid Baghomian Sangbarani har nu yrkat att tingsrätten skall\n1) döma till äktenskapsskillnad mellan parterna;\n2) berättiga henne att bo kvar i parternas gemensamma bostad till dess att bodelning\nskett;\n3) tillerkänna henne vårdnaden om Artur;\n4) förplikta Jirayer Moussakanian att till henne utge underhållsbidrag för Artur med\n1040 kr i månaden för tiden från den.\nJirayer Moussakanian har-med förbehållet att han önskade att äktenskapet skulle\nbestå-medgett yrkandena om äktenskapsskillnad, kvarboende och vårdnad. Han har\nmedgett att betala underhållsbidrag för Artur i enlighet med vad som yrkats för för-\nfluten tid men har motsatt sig att för tid framöver bidraga till sonens underhåll med\nhögre belopp än vad han nu faktiskt utger eller 1050 kr i månaden.\nAnahid Baghomian Sangbarani har gjort gällande att sonen har behov av och Jirayer\nMoussakanian förmåga att utge yrkat underhållsbidrag.\nDOMSKÄL\nFöreskriven betänketid har löpt och förutsättning föreligger därmed att bifalla yrkandet\nom äktenskapsskillnad. Motsvarande gäller yrkandena om kvarboende och vårdnad.\n\n\n[ underhållsfrågan har parterna uppgett följande. Barnet har behov av yrkat underhåll och Anahid\nBaghomian Sangbarani saknar förmåga att bidra till detta'
#'(?=[.]{1}\s+\n*[A-ZÅÐÄÖÉÜ]|\s\d\s)'
def findterms_upper(stringlist, part):
    sentenceRes = []
    split = re.split('(?=[.]{1}\s*\n[A-ZÅÐÄÖÉÜ])', part)
    
    print(split)
    
    for sentence in split:
        if all([x in sentence for x in stringlist]):
            sentenceRes.append(sentence)
    sentenceString = ''.join(sentenceRes)
    
    print("OUTPUT:\n",sentenceString)
    
    return sentenceString

out = findterms_upper(['yrka'], part_test)
#print(out)
