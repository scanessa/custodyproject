# -*- coding: utf-8 -*-
"""
Created on Mon Oct 18 17:50:55 2021

@author: ifau-SteCa


Purpose of the code is to read in all pdfs from a specified folder path, extract information (child ID, case ID, etc.),
save the extracted info as a dictionary and output it as a dataframe/csv file

Note: For uncertain cases a variable is set to 999 (eg. if it is not clear whether the plaintiff or defendant was granted physical custody, Stadigvarande boende = 999)

Outcome overview:
    1: joint
    2: sole with plaintiff (karande)
    3: sole with defendant (svarande)
    4: dismissed
    
Notes:
    Sometimes judge name is mistakenly read in after domskal heading, try to capture this maybe with strict restriction of 
    paragraph between? otherwise the code will always find 'something' after domskal
    
    
"""

import re, shutil, glob, PyPDF2, pandas as pd

#Define Paths
pdf_dir = "P:/2020/14/Kodning/Test-round-2/check_cases"
output_path = 'P:/2020/14/Kodning/Test-round-3/custody_data_test3.csv'

#Define key functions
def findSentence(string, part):
    sentenceRes = [sentence + '.' for sentence in part.split('.') if string in sentence]
    sentenceString = ''.join(sentenceRes)
    return sentenceString

def findTwoWords(string1, string2, part):
    sentenceRes = [sentence + '.' for sentence in part.split('.') if string1 in sentence and string2 in sentence]
    sentenceString = ''.join(sentenceRes)
    return sentenceString

def findThreeWords(string1, string2, string3, part):
    sentenceRes = [sentence + '.' for sentence in part.split('.') if string1 in sentence and string2 in sentence and string3 in sentence]
    sentenceString = ''.join(sentenceRes)
    return sentenceString

def searchKey(string, part, g):
    finder = re.compile(string)
    match = finder.search(part)
    if match is not None:
        searchResult = match.group(g)
    else:
        searchResult = None
    return searchResult
        
def searchLoop(searchDict, part, g):
    for i in searchDict:
        result = searchKey(searchDict[i], part, g)
        if result is None:
            continue
        else: 
            break
    return result

def termLoop(termList, part):
    for term in termList:
        sentence = findSentence(term, part)
        if term in part and not any([x in sentence for x in rejectKey]):
            dummy = 1
            break
        else:
            dummy = 0
            continue
    return dummy

def city(string,i):
    stringList = (string.strip()).split(" ")
    return stringList[-i]

"""
sample_files = ["P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alings+s TR T 957-13 Aktbil 12, DOM - Stadsdelsn+mnden +stra G.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 1823-11 Aktbil 38, DOM - Liselotte Björnberg, Dam.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 1845-17 Dom 2018-07-10.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 220-10 Dom 2010-05-11.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 544-15 Aktbil 100, DOM (DELDOM) - angående vårdna.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 75-18 Deldom 2018-08-17.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 2769-12 Dom 2013-10-21.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 2794-18 Dom 2018-12-10.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 2810-15 Dom 2015-07-24.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 2847-19 Deldom 2019-12-11.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 4015-16 Dom 2016-11-17.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 4336-14 Deldom 2014-07-30.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 519-11 Dom 2012-03-27.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 584-18 Dom 2018-10-15.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 5988-13 Dom 2014-05-08.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 8586-19 Deldom 2020-05-05.pdf",	"P:/2020/14/Tingsrätter/Blekinge/Domar/all_cases/Blekinge TR T 1661-17 Aktbil 57, DOM (DELDOM) - Ali Beool, Ingr.pdf",	"P:/2020/14/Tingsrätter/Blekinge/Domar/all_cases/Blekinge TR T 1857-18 Aktbil 65, DOM - Leandra Johansson, Vikto.pdf",	"P:/2020/14/Tingsrätter/Blekinge/Domar/all_cases/Blekinge TR T 1892-14 Aktbil 19, DOM (DELDOM) - Yaa Fosuah, Mik.pdf",	"P:/2020/14/Tingsrätter/Blekinge/Domar/all_cases/Blekinge TR T 2761-19 Aktbil 37, DOM - Arifka Memedi, Mahir Mem.pdf",	"P:/2020/14/Tingsrätter/Blekinge/Domar/all_cases/Blekinge TR T 2820-19 Aktbil 107, DOM - Reza Mirzai, Sekretess K.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 1461-12 2012-09-27 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 1806-07 2009-11-12 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 2069-13 2014-05-28 Deldom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 2116-09 2010-01-25 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 2212-15 2016-03-30 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 2456-09 2009-09-16 Deldom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 2978-18 2019-09-16 Deldom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 3452-14 2015-09-30 Dom.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 1115-15 Deldom 2016-03-23.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 1165-20 Dom 2021-02-12.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 1463-14 Dom 2015-10-27.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 508-17 Dom 2017-05-16.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 756-10 Dom 2010-12-22.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 1619-16 Dom 2016-11-15.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 2178-19 Dom 2020-03-02.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 2761-17 Deldom 2018-05-07.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 3033-12 Deldom 2013-08-22.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 3593-19 Dom 2021-02-10.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 643-16 Deldom 2016-10-13.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 976-10 Dom 2011-02-10.pdf",	"P:/2020/14/Tingsrätter/Gotlands/Domar/all_cases/Gotlands TR T 1001-16 Dom 2017-02-06.pdf",	"P:/2020/14/Tingsrätter/Gotlands/Domar/all_cases/Gotlands TR T 18-16 Deldom 2016-09-14.pdf",	"P:/2020/14/Tingsrätter/Gotlands/Domar/all_cases/Gotlands TR T 424-18 Dom 2018-10-12.pdf",	"P:/2020/14/Tingsrätter/Gotlands/Domar/all_cases/Gotlands TR T 543-17 Dom 2018-10-05.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/G+llivare TR T 285-16 Aktbil 8, DOM - Eija Kivilahti, Marko Ki.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/G+llivare TR T 436-16 Aktbil 18, DOM - Tesfay Mehari, Nigisti T.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/G+llivare TR T 719-18 Aktbil 20, DOM - Niaz Mohammad Mohammad K.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 1162-10 Deldom 2011-01-27.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 1627-08 Deldom 2009-07-02.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 2864-09 Dom 2010-08-13.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 3425-17 Dom 2020-10-22.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 514-17 Dom 2017-04-25.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 596-17 Dom 2017-06-02.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 827-17 Dom 2017-07-27.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 13391-19 Dom 2019-11-05.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 14325-16 Dom 2017-07-26.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 14674-19 Dom 2021-04-27.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 14767-17 Dom 2018-02-27.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 15699-20 Dom 2020-12-22.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 16027-15 Deldom 2016-05-12.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 16855-19 Dom 2021-01-18.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 4325-17 Deldom 2017-10-03.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 4684-16 Dom 2016-06-03.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 7655-18 Deldom 2019-02-25.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 9339-18 Dom 2019-04-15.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 1664-18 Dom 2019-10-25.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 1918-19 Deldom 2020-01-15.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 2020-13 Deldom 2014-02-18.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 2061-19 Dom 2020-03-24.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 2144-08 Dom 2009-06-18.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 716-18 Dom 2018-06-07.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 719-18 Deldom 2019-01-23.pdf",	"P:/2020/14/Tingsrätter/Haparanda/Domar/all_cases/Haparanda TR T 280-17 Dom 2017-05-11.pdf",	"P:/2020/14/Tingsrätter/Haparanda/Domar/all_cases/Haparanda TR T 713-15 Dom 2016-12-08.pdf",	"P:/2020/14/Tingsrätter/Haparanda/Domar/all_cases/Haparanda TR T 915-18 Dom 2019-02-15.pdf",	"P:/2020/14/Tingsrätter/Hässleholms/Domar/all_cases/Hässleholms TR T 1167-13 Dom 2014-11-20.pdf",	"P:/2020/14/Tingsrätter/Hässleholms/Domar/all_cases/Hässleholms TR T 578-19 Dom 2019-11-05.pdf",	"P:/2020/14/Tingsrätter/Hässleholms/Domar/all_cases/Hässleholms TR T 717-17 Dom 2018-05-17.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 3543-19 Dom 2020-01-09.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 3564-08 Deldom 2009-12-28.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 3865-17 Dom 2018-02-06.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 4034-07 Deldom 2008-07-03.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 4421-17 Dom 2018-04-19.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 542-17 Dom 2017-04-13.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 546-09 Dom 2010-05-04.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 873-12 Deldom 2012-09-24.pdf",	"P:/2020/14/Tingsrätter/Linköpings/Domar/all_cases/Linköpings TR T 157-18 Dom 2018-04-05.pdf",	"P:/2020/14/Tingsrätter/Linköpings/Domar/all_cases/Linköpings TR T 3035-16 Dom 2017-07-21.pdf",	"P:/2020/14/Tingsrätter/Linköpings/Domar/all_cases/Linköpings TR T 3352-13 Dom 2014-12-04.pdf",	"P:/2020/14/Tingsrätter/Linköpings/Domar/all_cases/Linköpings TR T 3360-14 Deldom 2015-04-10.pdf",	"P:/2020/14/Tingsrätter/Linköpings/Domar/all_cases/Linköpings TR T 3399-19 Deldom 2020-01-23.pdf",	"P:/2020/14/Tingsrätter/Linköpings/Domar/all_cases/Linköpings TR T 3707-17 Deldom 2018-05-22.pdf",	"P:/2020/14/Tingsrätter/Linköpings/Domar/all_cases/Linköpings TR T 441-18 Dom 2019-02-11.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 1198-15 Deldom 2017-12-13.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 1215-19 Dom 2020-05-22.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 299-15 Dom 2015-12-07.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 346-19 Dom 2019-08-19.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 710-14 Dom 2014-04-11.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 2088-13 2013-06-17 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 2244-18 2018-09-04 Deldom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 2525-09 2010-03-11 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 4340-08 2009-09-02 Deldom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 5227-09 2010-06-10 Deldom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 553-15 2015-03-20 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 5758-19 2020-09-02 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 5929-12 2013-02-04 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 6235-13 2014-01-27 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 10858-13 2014-10-24 Deldom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 1818-15 2015-11-04 Deldom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 2191-12 2012-05-25 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 4428-11 2012-10-25 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 4673-19 2020-05-06 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 498-11 2012-11-30 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 5209-14 2014-10-08 Deldom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 6746-17 2017-11-30 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 787-18 2019-06-04 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 7957-08 2009-01-09 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 8159-12 2013-01-11 Dom.pdf",	"P:/2020/14/Tingsrätter/Mora/Domar/all_cases/Mora TR T 1323-19 Aktbil 40, DOM - Elina Eriksson, Christof.pdf",	"P:/2020/14/Tingsrätter/Mora/Domar/all_cases/Mora TR T 1537-12 Aktbil 168, DOM - Alfred Hollenberger, Sof.pdf",	"P:/2020/14/Tingsrätter/Mora/Domar/all_cases/Mora TR T 744-19 Aktbil 30, DOM (DELDOM) - Joakim Cecen, M.pdf",	"P:/2020/14/Tingsrätter/Mora/Domar/all_cases/Mora TR T 858-08 Dom 2009-03-19.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 1840-12 Dom 2013-05-15.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 272-11 Dom 2012-04-05.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 2986-10 Deldom 2011-08-11.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 3813-19 Dom 2020-10-02.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 4223-11 Dom 2011-12-21.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 58-10 Deldom 2010-07-09.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 5960-09 Deldom 2010-07-21.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/dagboken 6359-19.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 1508-18 Deldom 2018-10-05.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 1799-10 Dom 2010-08-12.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 2149-10 Deldom 2010-08-27.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 2547-19 Aktbil 99, DOM - Ann Flyckt Bergschöld, S.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 3689-18 Dom 2019-09-18.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 3811-08 Deldom 2009-04-16.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 3894-18 Dom 2019-05-06.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 423-18 Dom 2018-08-21.pdf",	"P:/2020/14/Tingsrätter/Norrtälje/Domar/all_cases/Norrtälje TR T 774-11 Dom 2012-01-12.pdf",	"P:/2020/14/Tingsrätter/Norrtälje/Domar/all_cases/Norrtälje TR T 866-12 Dom 2013-03-11.pdf",	"P:/2020/14/Tingsrätter/Norrtälje/Domar/all_cases/Norrtälje TR T 921-17 Dom 2019-05-09.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 1262-12 Dom 2012-12-05.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 1375-14 Dom 2015-04-20.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 1495-11 Aktbil 35, DOM (DELDOM) - Tesalonica Lagu.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 227-20 Dom 2020-02-21.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 2271-11 Aktbil 24, DOM (DELDOM) - Frederik Anders.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 2703-11 Deldom 2012-04-24.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 565-17 Dom 2017-06-19.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/Skaraborgs TR T 2431-13 Dom 2014-02-27.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/Skaraborgs TR T 3324-14 Deldom 2015-07-07.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/Skaraborgs TR T 3681-17 Deldom 2018-08-08.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/Skaraborgs TR T 3799-15 Deldom 2016-01-18.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/Skaraborgs TR T 3900-16 Dom 2018-02-26.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/T 470-01.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 1074-09 Deldom 2010-02-16.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 973-17 Deldom 2017-11-02.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 1039-11 Dom 2011-08-03.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 291-15 Dom 2015-04-20.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 575-20 Dom 2021-05-20.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 715-14 Dom 2014-09-16.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 2122-07 Dom 2008-10-06.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 271-17 Dom 2019-03-12.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 324-14 Dom 2015-03-04.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 3507-13 Dom 2013-10-02.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 4723-09 Dom 2009-11-30.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 5195-11 Dom 2012-03-19.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 5620-11 Deldom 2012-10-15.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 803-16 Dom 2016-12-13.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 8063-08 Dom 2010-10-11.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 8463-17 Deldom 2018-02-05.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 9754-11 Deldom 2012-09-05.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 9857-13 Dom 2014-08-22.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 11111-15 Deldom 2016-09-09.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 11194-14 Deldom 2015-03-27.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 13776-18 Dom 2019-05-31.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 2578-17 Dom 2017-09-22.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 3051-19 Dom 2020-03-16.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 7058-17 Deldom 2017-12-12.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 7445-18 Dom 2019-11-14.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 8127-17 Dom 2018-10-26.pdf",	"P:/2020/14/Tingsrätter/Sundsvalls/Domar/all_cases/Sundsvalls TR T 1013-16 Dom 2017-02-21.pdf",	"P:/2020/14/Tingsrätter/Sundsvalls/Domar/all_cases/Sundsvalls TR T 1885-18 Deldom 2019-04-30.pdf",	"P:/2020/14/Tingsrätter/Sundsvalls/Domar/all_cases/Sundsvalls TR T 2022-19 Dom 2019-10-09.pdf",	"P:/2020/14/Tingsrätter/Sundsvalls/Domar/all_cases/Sundsvalls TR T 2306-14 Deldom 2015-11-27.pdf",	"P:/2020/14/Tingsrätter/Sundsvalls/Domar/all_cases/Sundsvalls TR T 2390-15 Deldom 2016-11-17.pdf",	"P:/2020/14/Tingsrätter/Sundsvalls/Domar/all_cases/Sundsvalls TR T 856-20 Dom 2020-05-25.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 1261-19 Dom 2020-03-17.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 2159-18 Dom 2018-12-04.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 2882-18 Dom 2019-09-05.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 11362-14 2015-03-12 Deldom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 12739-19 2020-04-24 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 13472-17 2018-06-13 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 14215-20 2020-11-03 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 14829-12 2013-05-30 Deldom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 16163-18 2019-02-12 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 16336-12 2013-05-02 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 17047-15 2016-04-04 Deldom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 17315-19 2020-11-19 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 2861-12 2012-09-27 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 2876-11 2013-01-22 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 4381-18 2018-06-21 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 6473-09 2010-05-17 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 7586-15 2017-05-16 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 8845-18 2018-08-14 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 9194-07 2008-11-17 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 9795-15 2016-03-15 Dom.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1283-19 Aktbil 16, DOM - Loise Alexandersson, Rog.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 3582-19 Aktbil 98, DOM - Emma Lundgren, Bram Van .pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 661-17 Aktbil 14, DOM - Sabri Belal, Daleen Raha.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 966-15 Aktbil 13, DOM - Thomas Bergstrand, Gerda.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 223-02.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1684-13 Dom 2014-03-03.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1833-07 Deldom 2009-01-21.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1897-06 Deldom 2008-05-14.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1931-12 Dom 2013-06-27.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2376-11 Dom 2012-01-19.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 306-10 Deldom 2010-10-04.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 3775-19 Dom 2021-01-12.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 2034-17 Dom 2017-05-08.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 2277-08 Dom 2010-02-04.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 3265-09 Deldom 2009-12-04.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 4162-14 Deldom 2014-12-18.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 4289-16 Deldom 2017-02-27.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 4618-15 Dom 2015-10-06.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 5509-19 Dom 2019-09-18.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 5644-06 Dom 2008-12-04.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 6458-18 Dom 2020-09-24.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 1783-08 Deldom 2009-03-11.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 2385-17 Dom 2018-05-25.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 3031-18 Deldom 2019-04-09.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 4111-16 Dom 2016-12-27.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 4278-13 Dom 2014-06-24.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 4379-14 Deldom 2015-12-28.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 4855-17 Dom 2019-03-19.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 500-11 Dom 2012-02-13.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 1186-13 Dom 2013-11-26.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 2173-11 Deldom 2014-01-16.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 3419-12 Deldom 2013-07-04.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 3797-08 Dom 2009-02-19.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 3898-09 Dom 2010-12-16.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 4300-13 Dom 2014-01-14.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 4948-14 Dom 2015-12-11.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 5623-17 Dom 2018-03-09.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 5706-13 Deldom 2015-05-13.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 158-19 Deldom 2019-11-12.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 254-19 Dom 2019-02-11.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 3548-12 Deldom 2013-06-12.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 3567-13 Dom 2014-08-22.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 3668-17 Deldom 2018-04-18.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 3919-16 Dom 2017-05-09.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 4587-18 Dom 2019-08-20.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 987-14 Dom 2015-06-01.pdf",	"P:/2020/14/Tingsrätter/Ystads/Domar/all_cases/Ystads TR T 2416-17 Deldom 2018-03-19.pdf",	"P:/2020/14/Tingsrätter/Ystads/Domar/all_cases/Ystads TR T 2900-17 Deldom 2018-09-26.pdf",	"P:/2020/14/Tingsrätter/Ystads/Domar/all_cases/Ystads TR T 2915-18 Dom 2019-10-09.pdf",	"P:/2020/14/Tingsrätter/Ystads/Domar/all_cases/Ystads TR T 446-19 Deldom 2019-08-23.pdf",	"P:/2020/14/Tingsrätter/Ystads/Domar/all_cases/Ystads TR T 446-19 Dom 2020-04-21.pdf",	"P:/2020/14/Tingsrätter/Ystads/Domar/all_cases/Ystads TR T 819-17 Dom 2018-06-26.pdf",	"P:/2020/14/Tingsrätter/Ångermanlands/Domar/all_cases/Ångermanlands TR T 2169-21 Dom 2021-11-03.pdf",	"P:/2020/14/Tingsrätter/Ångermanlands/Domar/all_cases/Ångermanlands TR T 2275-18 Dom 2019-02-25.pdf",	"P:/2020/14/Tingsrätter/Ångermanlands/Domar/all_cases/Ångermanlands TR T 2334-19 Dom 2020-10-06.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1729-05.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1766-05.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/863-07.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 3917-15 Deldom 2016-04-18.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 4065-17 Dom 2019-03-07.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 4571-20 Dom 2021-05-19.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 6240-14 Dom 2015-03-17.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 6593-11 Dom 2012-03-14.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 822-11 Dom 2011-10-31.pdf",	"P:/2020/14/Tingsrätter/Östersunds/Domar/all_cases/Östersunds TR T 1640-14 Dom 2014-09-03.pdf",	"P:/2020/14/Tingsrätter/Östersunds/Domar/all_cases/Östersunds TR T 2027-12 Dom 2012-10-29.pdf",	"P:/2020/14/Tingsrätter/Östersunds/Domar/all_cases/Östersunds TR T 2032-14 Dom 2014-10-09.pdf",	"P:/2020/14/Tingsrätter/Östersunds/Domar/all_cases/Östersunds TR T 2408-07 Dom 2010-06-04.pdf"]

for file in sample_files:
    shutil.copy(file,pdf_dir)
"""
    
#Read in PDFs
pdf_files = glob.glob("%s/*.pdf" % pdf_dir)
print(pdf_files)

#Initialize variables
noOfFiles = 0
noUnreadable = 0
countries = ['saknas', 'okänd', 'adress', 'u.s.a.', 'u.s.a', 'usa', 'sekretess', 'afghanistan', 'albanien', 'algeriet', 'andorra', 'angola', 'antigua och barbuda', 'argentina', 'armenien', 'australien', 'azerbajdzjan', 'bahamas', 'bahrain', 'bangladesh', 'barbados', 'belgien', 'belize', 'benin', 'bhutan', 'bolivia', 'bosnien och hercegovina', 'botswana', 'brasilien', 'brunei', 'bulgarien', 'burkina faso', 'burundi', 'centralafrikanska republiken', 'chile', 'colombia', 'costa rica', 'cypern', 'danmark', 'djibouti', 'dominica', 'dominikanska republiken', 'ecuador', 'egypten', 'ekvatorialguinea', 'elfenbenskusten', 'el salvador', 'eritrea', 'estland', 'etiopien', 'fiji', 'filippinerna', 'finland', 'frankrike', 'förenade arabemiraten', 'gabon', 'gambia', 'georgien', 'ghana', 'grekland', 'grenada', 'guatemala', 'guinea', 'guinea-bissau', 'guyana', 'haiti', 'honduras', 'indien', 'indonesien', 'irak', 'iran', 'irland', 'island', 'israel', 'italien', 'jamaica', 'japan', 'jemen', 'jordanien', 'kambodja', 'kamerun', 'kanada', 'kap verde', 'kazakstan', 'kenya', 'kina', 'kirgizistan', 'kiribati', 'komorerna', 'kongo-brazzaville', 'kongo-kinshasa', 'kroatien', 'kuba', 'kuwait', 'laos', 'lesotho', 'lettland', 'libanon', 'liberia', 'libyen', 'liechtenstein', 'litauen', 'luxemburg', 'madagaskar', 'malawi', 'malaysia', 'maldiverna', 'mali', 'malta', 'marocko', 'marshallöarna', 'mauretanien', 'mauritius', 'mexiko', 'mikronesiska federationen', 'moçambique', 'moldavien', 'monaco', 'montenegro', 'mongoliet', 'myanmar', 'namibia', 'nauru', 'nederländerna', 'nepal', 'nicaragua', 'niger', 'nigeria', 'nordkorea', 'nordmakedonien', 'norge', 'nya zeeland', 'oman', 'pakistan', 'palau', 'panama', 'papua nya guinea', 'paraguay', 'peru', 'polen', 'portugal', 'qatar', 'rumänien', 'rwanda', 'ryssland', 'saint kitts och nevis', 'saint lucia', 'saint vincent och grenadinerna', 'salo-monöarna', 'samoa', 'san marino', 'são tomé och príncipe', 'saudiarabien', 'schweiz', 'senegal', 'seychellerna', 'serbien', 'sierra leone', 'singapore', 'slovakien', 'slovenien', 'somalia', 'spanien', 'sri lanka', 'storbritannien', 'sudan', 'surinam', 'sverige', 'swaziland', 'sydafrika', 'sydkorea', 'sydsudan', 'syrien', 'tadzjikistan', 'tanzania', 'tchad', 'thailand', 'tjeckien', 'togo', 'tonga', 'trinidad och tobago', 'tunisien', 'turkiet', 'turkmenistan', 'tuvalu', 'tyskland', 'uganda', 'ukraina', 'ungern', 'uruguay', 'usa', 'uzbekistan', 'vanuatu', 'vatikanstaten', 'venezuela', 'vietnam', 'vitryssland', 'zambia', 'zimbabwe', 'österrike', 'östtimor']

emptyString = ''
                
#Define search terms
svarandeSearch = ' Svarande|SVARANDE|Motpart|MOTPART|SVARANDE och KÄRANDE '
defendantNationality = 'medborgare i (\w+ )+sekretess'
party ='((\w+\s?-?(\w+\s?-?)+?){1}((\w+\s?-?)*\w+))\s*[,]\s*(\d{6,10}\s*.?\s*(\d{4})?[,]?\s)?' 
nameCaps = '[A-ZÅÄÖ]{3,}'
idNo ='((\d{6,10}\s*.?.?\s*(\d{4})?)[,]?\s)'
appendixStart = '((?<!se )Bilaga [1-9]|(?<!se )Bilaga A|sida\s+1\s+av|ANVISNING FÖR ÖVERKLAG)'
searchCaseNo = 'mål\s*(nr)?[.]?\s*t\s*(\d*\s*.?.?\s*\d*)'
namePlaceHolder = '(?i)((\w+\s?-?(\w+\s?-?)+?){1}((\w+\s?-?)*\w+))'
yearSearch = '\s(\d{4})\s?,?[.]?'
word = '(\w+ )+'

dateSearch = {
    '1' : 'dom\s+(\d*\s*-\s*\d*\s*-\s*\d*)',
    '2' : 'dom\s+sid\s*1\s*[(][0-9]*[)]\s*(\d*\s*-\s*\d*\s*-\s*\d*)',
    '3' : '(\d*\s*-\s*\d*\s*-\s*\d*)'
    }
courtSearch = {
    '1' : '((\w+ ){1})tingsr?.?ätt',
    '2' : '((\w+){1})[.]?.?tingsratt'
    }
judgeSearch = {
    '1': '\n\s*\n\s*(([A-ZÅÄÖ][a-zåäöé]+\s+){2,4})\n\s*\n', #normal names
    '2': '\n\s*\n\s*([A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ][a-zåäöé]+\s+)\n\s*\n', #first name hyphenated
    '3': '\n\s*\n\s*([A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s+)\n\s*\n', #last name hypthenated
    '4': '\n\s*\n\s*([A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s+)\n\s*\n', #first and last name hyphenated
    '5': '\n\s*\n\s*([A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ]\s[A-ZÅÄÖ][a-zåäöé]+\s+)\n\s*\n', #name with initial as second name
    #if there is a note in the line following the judge's name
    '6': '\n\s*\n\s*(([A-ZÅÄÖ][a-zåäöé]+\s+){2,4})\n', #normal names
    '7': '\n\s*\n\s*([A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ][a-zåäöé]+\s+)\n', #first name hyphenated
    '8': '\n\s*\n\s*([A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s+)\n', #last name hypthenated
    '9': '\n\s*\n\s*([A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s+)\n', #first and last name hyphenated
    '10': '\n\s*\n\s*([A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ]\s[A-ZÅÄÖ][a-zåäöé]+\s+)\n', #name with initial as second name
    #For documents where judge didnt sign
    '11': 'rådmannen\s*(([A-ZÅÄÖ][a-zåäöé]+\s+){2,4})',
    '12': 'rådmannen\s*([A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ][a-zåäöé]+\s+)', #first name hyphenated
    '13': 'rådmannen\s*([A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s+)', #last name hypthenated
    '14': 'rådmannen\s*([A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s+)', #first and last name hyphenated
    '15': 'rådmannen\s*([A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ]\s[A-ZÅÄÖ][a-zåäöé]+\s+)', #name with initial as second name
    '16': 'tingsfiskalen\s*(([A-ZÅÄÖ][a-zåäöé]+\s+){2,4})',
    '17': 'tingsfiskalen\s*([A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ][a-zåäöé]+\s+)', #first name hyphenated
    '18': 'tingsfiskalen\s*([A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s+)', #last name hypthenated
    '19': 'tingsfiskalen\s*([A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s+)', #first and last name hyphenated
    '20': 'tingsfiskalen\s*([A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ]\s[A-ZÅÄÖ][a-zåäöé]+\s+)', #name with initial as second name
    #when judge's name ends with . 
    '21': '\n\n(([A-ZÅÄÖ][a-zåäöé]+\s+){1,3}[A-ZÅÄÖ][a-zåäöé]+).\s*\n\n', #normal names
    '22': '\n\s*\n\s*([A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ][a-zåäöé]+).\s*\n', #first name hyphenated
    '23': '\n\s*\n\s*([A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+).\s*\n', #last name hypthenated
    '24': '\n\s*\n\s*([A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]).\s*\n', #first and last name hyphenated
    '25': '\n\s*\n\s*([A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ]\s[A-ZÅÄÖ][a-zåäöé]+).\s*\n' #name with initial as second name
    }

#Define keys for simple word search
fastInfoKey = ['snabbupplysning', 'upplysning', 'snabbyttrande']
corpTalksKey = ['samarbetssamtal','medlingssamtal','medling', 'medlare']
mainHearingKey = ['huvudförhandling' , ' rättegång ' , 'sakframställning' , 'förhör' ]
lawyerKey = ["ombud:", 'god man:',  'advokat:', "ombud", 'god man',  'advokat']
investigationKey = ['vårdnadsutredning','boendeutredning','umgängesutredning']
investigationHelper = ["vårdn", "umgänge", "boende"]
agreementKey = ['samförståndslösning',  'överens', 'medger', 'medgett']
agreementAdd = ['parterna' ,'framgår' ,'enlighet' ,'följer','fastställa', 'kommit','barnets','bästa']
agreementHelper = ['umgänge', 'boende']
socialOffice = ['social', 'nämnden', 'kommun', 'familjerätt']
umgangeKey = ['umgänge', 'umgås']
rejectKey = ['avskriv','käromalet ogillas','lämnas utan bifall','avslå',' inte ','skrivs', 'kvarstå']  

#Intiialize lists and dictionary to fill
data = {'Barn':[], 'Målnr':[], 'Tingsrätt':[], 'År avslutat':[], 'Deldom':[], 'Kärande förälder':[], 'Svarande förälder':[], 'Kär advokat':[], 'Sv advokat':[], 'Sv utlandet':[], 'Sv okontaktbar':[], 'Utfall':[], 'Umgänge':[], 'Stadigvarande boende':[], 'Underhåll':[], 'Enl överenskommelse':[], 'Snabbupplysning':[], 'Samarbetssamtal':[], 'Utredning':[], 'Huvudförhandling':[], 'Domare':[], "Page Count": [], 'Rättelse': [], "File Path": []}

pages_text = []

#Loop over files and extract data
for file in pdf_files:
    print("Currently Reading: ")
    print(file)
    # creating a pdf file object
    pdfFileObj = open(file, 'rb')
     
    # creating a pdf reader object
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
     
    # printing number of pages in pdf file
    pageCount = pdfReader.numPages
     
    # creating a page object
    for i in range(0, pageCount):
        pageObj = pdfReader.getPage(i)
        pages_text.append(pageObj.extractText())

    # closing the pdf file object
    pdfFileObj.close()
 
    #Convert full text to clean string
    firstPage = pages_text[0]

    if "Rättelse" in firstPage:
        fullTextOG = ' '.join(''.join(pages_text[1:]).split())
        firstPage = ' '.join(''.join(pages_text[1]).split())
        fullTextFormatted = ''.join(pages_text[1:])
        dummyRat = 1
    else:
        firstPage = ' '.join(''.join(pages_text[0]).split())
        fullTextOG = ' '.join(''.join(pages_text).split())
        fullTextFormatted = ''.join(pages_text)
        dummyRat = 0

    splitTextOG = re.split('_{10,40}', fullTextOG)
    headerOG = re.split('_{10,40}', firstPage)[0]   
    header = headerOG.lower()    
    appendixPage = [i for i, item in enumerate(pages_text) if re.search(appendixStart, item)]
    if not appendixPage:
        appendixPageNo = len(pages_text)
    else:
        appendixPageNo = appendixPage[0]
    lastPageFormatted = '.'.join((pages_text[appendixPageNo-1]).split(".")) + '.'.join((pages_text[appendixPageNo-2]).split("."))
    lastPageFormatted3 = pages_text[appendixPageNo-1]
    lastPageOG = pages_text[appendixPageNo-1]
    lastPage = lastPageOG.lower()                       
    fullTextOG = (re.split(appendixStart, fullTextOG)[0])  
    fullText = fullTextOG.lower()
    try:
        rulingString = ''.join(re.split('DOMSLUT',fullTextOG)[1:])
        rulingStringFormatted = ''.join(re.split('DOMSLUT', fullTextFormatted)[1:])
    except:
        rulingString = ''.join(re.split('_{10,40}\s*',fullTextOG)[1:])
        rulingStringFormatted = ''.join(re.split('_{10,40}\s*', fullTextFormatted)[1:])
            
    try:
        rulingOnly = re.split('\n\s*\n\s*[A-ZÅÄÖ.,]{4,}\s{0,1}[A-ZÅÄÖ.,]{0,4}\s*\n\s*\n\s*', rulingStringFormatted)[0].lower()
        rulingOnly = ' '.join(''.join(rulingOnly).split())
    except AttributeError:
        rulingOnly = re.split('(YRKANDEN)', rulingStringFormatted)[0].lower() 
        rulingOnly = ' '.join(''.join(rulingOnly).split())
    fullTextList = fullText.split(".")  
    
    print(lastPageFormatted3)
    
    try:
        svarandeStringOG = re.split(svarandeSearch, headerOG)[1] 
        kärandeStringOG = re.split('Kärande|KÄRANDE', (re.split(svarandeSearch, headerOG)[0]))[1]
        if svarandeStringOG == "":
            svarandeStringOG = re.split(svarandeSearch, headerOG)[2] 
        elif len(kärandeStringOG.split()) < 4:
            svarandeStringOG = re.split("(?i)SVARANDE och KÄRANDE|SVARANDE OCH GENKÄRANDE ", headerOG)[1]
            kärandeStringOG = re.split('(?i)KÄRANDE och SVARANDE|KÄRANDE OCH GENSVARANDE', (re.split("SVARANDE och KÄRANDE|SVARANDE OCH GENKÄRANDE ", headerOG)[0]))[1]
    except IndexError:
        try:
            svarandeStringOG = re.split('_{10,40}', (re.split('2[.]\s*', (re.split('1[.]\s*', (re.split('PARTER|Parter', headerOG)[1]))[1]))[1]))[0]
            kärandeStringOG = re.split('2[.]\s*', (re.split('1[.]\s*', (re.split('PARTER|Parter', headerOG)[1]))[1]))[0]
        except IndexError:
            svarandeStringOG = re.split("Hustrun|HUSTRUN", headerOG)[1] 
            kärandeStringOG = re.split('Mannen|MANNEN', (re.split("Hustrun|HUSTRUN", headerOG)[0]))[1]
    svarandeString = svarandeStringOG.lower()
    kärandeString = kärandeStringOG.lower()

    #List of children's numbers
    childNoRes = []
    childNo = set(re.findall('\d{6,8}\s*-\s*\d{4}', rulingString))   
    for i in childNo:
        mistakeChilNos = searchKey("\A197|\A198|\A5|\A6|\A7|\A8", i, 0)
        if mistakeChilNos is None: # child ID should not start with 197 or 198, or 5,6,7,8  
            childNoRes.append(i)   
    
    #Loop to create dictionary with one row per child
    for i in childNoRes:  
        
        #Name of judge
        try:
            judgeName = ((searchLoop(judgeSearch, lastPageFormatted, 1)).split('\n'))[0]
            fullText = (re.split(judgeName, fullTextOG)[0]).lower()
        except:
            judgeName = 'Not found'
            fullText = (re.split(appendixStart, fullTextOG)[0]).lower()

        #Get child's name
        childNameKey = ('([A-ZÅÄÖ][a-zåäöé]+)[,]?\s*[(]?\s*' + i )
        childNameFirst = searchKey(childNameKey, fullTextOG, 1)
        if childNameFirst is not None:
            childKey1 = re.compile("(([A-ZÅÄÖÉ][a-zåäöéA-ZÅÄÖÉ-]+\s*){1,4})"+ childNameFirst + '[,]?[)]?\s*' + i)
            childNameFull = childKey1.search(fullTextOG)
            if childNameFull is not None:
                childNameFull = childNameFull.group(1)
                childKey2 = re.compile('[A-ZÅÄÖÉ][A-ZÅÄÖÉ]+')
                childNameCaps = childKey2.search(childNameFull)
                if childNameCaps is None:
                    childKey3 = re.compile('[A-ZÅÄÖÉ][a-zåäöé]+')
                    childNameFirst = childKey3.search(childNameFull).group(0).lower()
                else:
                    childNameFirst = childNameCaps.group(0).lower()
        else:
            childName = 'not found'
            childNameFirst = 'not found'
        childNameFirst = childNameFirst.lower()
        
        #Case ID for child i
        caseNo = ''.join((searchKey(searchCaseNo, header, 2)).split())
        
        #District Court
        courtName = searchLoop(courtSearch, fullText, 0)

        #Year Closed
        date = searchLoop(dateSearch, header, 1)
        year = date.split('-')[0]
        
        #Deldom
        if 'deldom' in file or 'deldom' in header:
            dummyDel = 1
        else:
            dummyDel = 0
        
        #Plaintiff
        plaintNameFull = kärandeStringOG.split(",")[0]
        try:
            plaintNameFirst = searchKey(nameCaps, plaintNameFull, 0).lower()
        except AttributeError:
            plaintNameFirst = plaintNameFull.split()[0].lower()
        try:
            plaintNo = ''.join(searchKey(idNo, kärandeString, 2).split())
        except AttributeError:
            plaintNo = "-"

        # Defendant
        svNameFull = svarandeStringOG.split(",")[0]
        try:
            svNameFirst = searchKey(nameCaps, svNameFull, 0).lower()
        except AttributeError:
            svNameFirst = svNameFull.split()[0].lower()
        try:
            svNo = ''.join(searchKey(idNo, svarandeString, 2).split())
        except AttributeError:
            svNo = "-"         
         
        #Plaintiff representative (Kär advokat)
        if 'ombud' in kärandeString or "god man" in kärandeString or "advokat" in kärandeString:
            dummyOmbPlaint = 1
        else:
            dummyOmbPlaint = 0 

        #Dummy defendant representative
        for term in lawyerKey:
            if term in svarandeString:
                if 'god man' in term:
                    svGodMan = 1
                else:
                    svGodMan = 0
                defOmbud = 1 
                defAddress = re.split(term, svarandeString)[0]
                cityString = ''.join(city(defAddress, 1))
                break
            else:
                defOmbud = 0
                cityString = ''.join(city(svarandeString, 1))
                svGodMan = 0
                continue

        #Defendant abroad 
        print('Defendant city string: ' + cityString)
        if any([x in cityString for x in countries]):
            dummyAbroad = 1
        elif cityString.isdecimal():
            dummyAbroad = 1
        else:
            dummyAbroad = 0
        
        #Defendant unreachable
        svUnreach1 = (re.compile(('(han|hon) har inte kunnat få kontakt med ' + svNameFirst))).search(fullText)
        svUnreach2 = (re.compile(('(han|hon) har inte lyckats etablera kontakt med ' + svNameFirst))).search(fullText)
        if 'okontaktbar' in fullText or 'förordnat god man' in fullText:
            if svNameFirst in findSentence('förordnat god man', fullText):
                print('unreach1')
                dummyUnreach = 1
            else:
                print('unreach2')
                dummyUnreach = 0
        elif svUnreach1 is not None or svUnreach2 is not None:
            print('unreach3')
            dummyUnreach = 1
        elif 'varken kan bestrida eller medge' in fullText:
            print('unreach6')
            dummyUnreach = 1
        elif 'inte fått någon kontakt' in fullText:
            if 'huvudman' in findSentence('någon kontakt', fullText) or svNameFirst in findSentence('någon kontakt', fullText):
                dummyUnreach = 1
                print('unreach7')
            else:
                dummyUnreach = 999
        elif svNameFirst in findTwoWords('okän', 'befinn', fullText):
            print('unreach8a')
            dummyUnreach = 1
        elif svGodMan == 1 and not findTwoWords(svNameFirst, 'genom', findTwoWords('sin', 'gode man', fullText)):
            dummyUnreach = 1
            print('unreach8')
        else:
            print('unreach9')
            dummyUnreach = 0

        #Outcome
        try:
            findGemensam = findSentence(searchKey('(gemensam)[^m]',rulingOnly,1), rulingOnly)
        except TypeError:
            findGemensam = findSentence('gemen-', rulingOnly)
        vardnInGemensam = 'vårdn' in findGemensam
        findEnsam = findSentence('ensam', rulingOnly)
        findVardn = findSentence('vårdn', rulingOnly)
        findEnsamVardn = findTwoWords('ensam','vårdn',rulingOnly)
        findGemensamVardn = findTwoWords('vårdn', 'gemensam', rulingOnly)
        findVardnBarn = findTwoWords('vårdn', 'barn', rulingOnly)
        transferToDef = 'till ' + svNameFirst
        transferToPlaint = 'till ' + plaintNameFirst
        vardnInRuling = 'vårdn' in rulingOnly
        
        print(findVardn)       
                
        if 'vårdn' not in rulingOnly or vardnInRuling and 'påminn' in findVardn or vardnInRuling and 'erinra' in findVardn or vardnInRuling and 'upply' in findVardn:
            #No custody ruling in this court record
            print("out1")
            dummyOut = 0
        elif 'ska' in findGemensam and 'om' in findGemensam and vardnInGemensam and not any([x in findGemensamVardn for x in rejectKey]):
            dummyOut = 1
            print("out2")
        elif 'vårdn' in rulingOnly and 'fortsätt' in findGemensam and 'ska' in findGemensam and not any([x in findGemensamVardn for x in rejectKey]):
            dummyOut = 1
            print("out3")
        elif vardnInGemensam and findTwoWords('alltjämt','ska' , findGemensam) and not any([x in findGemensamVardn for x in rejectKey]):
            dummyOut = 1
            print("out4")
        elif vardnInGemensam and findTwoWords('alltjämt', 'är', rulingOnly) and not any([x in findGemensamVardn for x in rejectKey]):
            dummyOut = 1
            print("out5")
        elif vardnInGemensam and 'skall tillkomma' in rulingOnly and not any([x in findGemensamVardn for x in rejectKey]): 
            dummyOut = 1
            print("out6")
        elif 'vårdn' in findEnsam and plaintNameFirst in findEnsam and 'utan' not in findEnsamVardn and not any([x in findEnsamVardn for x in rejectKey]):
            dummyOut = 2
            print("out7")
        elif 'vårdn' in findEnsam and svNameFirst in findEnsam and 'utan' not in findEnsamVardn and not any([x in findEnsamVardn for x in rejectKey]):
            dummyOut = 3
            print("out8")
        elif 'ensam' in rulingOnly and vardnInRuling and plaintNameFirst in findVardn and not any([x in findEnsamVardn for x in rejectKey]):
            dummyOut = 2
            print("out10a")
        elif plaintNameFirst in findEnsam and not any([x in findEnsamVardn for x in rejectKey]):
            dummyOut = 2
            print("out10")
        elif 'ensam' in rulingOnly and vardnInRuling and  svNameFirst in findVardn and not any([x in findEnsamVardn for x in rejectKey]):
            dummyOut = 3
            print("out11a")    
        elif svNameFirst in findEnsam and not any([x in findEnsamVardn for x in rejectKey]):
            dummyOut = 3
            print("out11")
        elif vardnInRuling and 'överflytt' in rulingOnly and transferToDef in findVardn and not any([x in findVardn for x in rejectKey]):
            dummyOut = 3
            print("out12")
        elif vardnInRuling and 'överflytt' in rulingOnly and transferToPlaint in findVardn and not any([x in findVardn for x in rejectKey]):
            dummyOut = 2
            print("out13")
        elif vardnInRuling and 'tillerkänn' in findVardn and svNameFirst in findSentence('tillerkänn', rulingOnly) and not any([x in findVardn for x in rejectKey]):
            dummyOut = 3
            print("out14")
        elif vardnInRuling and 'tillerkänn' in findVardn and plaintNameFirst in findSentence('tillerkänn', rulingOnly) and not any([x in findVardn for x in rejectKey]):
            dummyOut = 2
            print("out15")
        elif vardnInRuling and 'anförtro' in findVardn and svNameFirst in findSentence('anförtro', rulingOnly) and not any([x in findVardn for x in rejectKey]):
            dummyOut = 3
            print("out14")
        elif vardnInRuling and 'anförtro' in findVardn and plaintNameFirst in findSentence('anförtro', rulingOnly) and not any([x in findVardn for x in rejectKey]):
            dummyOut = 2
            print("out15")
        elif 'käromalet ogillas' in rulingOnly or "lämnas utan bifall" in findVardn or 'avskriv' in findVardn:
            #"lämnas utan bifall" in findVard because if I search in ruling only it picks up when umgange claims or so are dismissed
            dummyOut = 4  
            print("out9")
        elif findTwoWords('avslås', 'vårdn', rulingOnly):
            dummyOut = 4
            print("out9a")
        elif 'bilaga' in rulingOnly and 'överens' in findSentence('bilaga', rulingOnly):
            dummyOut = 999
            print("out16")
        else: 
            dummyOut = 999
            print("out17")
        
        #Visitation rights        
        for key in umgangeKey:
            findUmg = findTwoWords(key, childNameFirst, rulingOnly)
            if childNameFirst == 'not found':
                dummyVisit = 999
                print('umg1')
                break
            elif findUmg and not any([x in findUmg for x in rejectKey]):  
                print('umg2')
                dummyVisit = 1
                break 
            elif findTwoWords('semester', childNameFirst, rulingOnly):
                print('umg3')
                dummyVisit = 0
                break
            elif findTwoWords('bilaga', 'sidorna', rulingOnly):
                print('umg4')
                dummyVisit = 999
                break
            else:
                print('umg5')
                dummyVisit = 0
                continue

        #N. Physical custody 
        childTerms = [childNameFirst, 'barn']
        for term in childTerms:
            if childNameFirst == 'not found':
                dummyPhys = 999
                print("phsical custody 1")
            elif term in findTwoWords('boende', plaintNameFirst, rulingOnly) and 'skyddat' not in findTwoWords('boende', plaintNameFirst, rulingOnly):
                dummyPhys = 1
                print("phsical custody 2")
            elif term in findTwoWords('boende', svNameFirst, rulingOnly):
                dummyPhys = 2
                print("phsical custody 3")
            elif term in findTwoWords('bo tillsammans', plaintNameFirst, rulingOnly):
                dummyPhys = 1
                print("phsical custody 4")
            elif term in findTwoWords('bo tillsammans', svNameFirst, rulingOnly):
                dummyPhys = 2
                print("phsical custody 5")
            elif term in findTwoWords('bo', plaintNameFirst, findSentence('stadigvarande', rulingOnly)):
                dummyPhys = 1  
                print("phsical custody 6")
            elif term in findTwoWords('bo', svNameFirst, findSentence('stadigvarande', rulingOnly)):
                dummyPhys = 2
                print("phsical custody 7")
            elif findTwoWords('bilaga', 'sidorna', rulingOnly):
                dummyPhys = 999
                print("phsical custody 8")
            else:
                dummyPhys = 0
                print("phsical custody 9")
        
        #Alimony
        for term in rejectKey:
            if findSentence('underhåll', rulingOnly) and term not in findSentence('underhåll', rulingOnly):
                dummyAlimon = 1
            elif findTwoWords('bilaga', 'sidorna',  rulingOnly):
                dummyAlimon = 999                    
            else:
                dummyAlimon = 0 
              
        #Ruling by agreement
        for termAgree in agreementKey:
            if svNameFirst in findTwoWords('yrkande', termAgree, fullText):
                print('agree1: ' + termAgree)
                dummyAgree = 1
                dummyUnreach = 0
                break
            for termHelper in agreementAdd:
                findAgree = findTwoWords(termAgree, termHelper, fullText)
                if findAgree is not emptyString:
                    print('agree2: '+ termAgree + termHelper)
                    dummyAgree = 1
                    dummyUnreach = 0
                    break
                else:
                    dummyAgree = 0
                    continue
            else: 
                continue
            break
        if dummyAgree == 0 and 'förlikning' in findTwoWords('framgå', 'träff', fullText):
            print('agree4')
            dummyAgree = 1
            dummyUnreach = 0
           
        #Fast information (snabbupplysningar)
        if termLoop(socialOffice, findSentence('yttra', fullText)):
            print("snabbupply 1")
            dummyInfo = 1
        elif termLoop(socialOffice, findSentence('uppgett', fullText)):
            dummyInfo = 1
            print("snabbupply 2 " )
        elif '6 kap. 20 § andra stycket föräldrabalken' in fullText:
            dummyInfo = 1 
            print("snabbupply 3 ")
        else:
            dummyInfo = termLoop(fastInfoKey, fullText)
            print("snabbupply 4" )
              
        #Cooperation talks
        dummyCoop = termLoop(corpTalksKey, fullText)
           
        #Investigation
        dummyInvest = termLoop(investigationKey, fullText)
        if dummyInvest == 0:
            if 'tingsrätt' in findSentence('utredning', fullText):
                print('invest1')
                dummyInvest = 1
            elif any([x in findSentence('utredning', fullText) for x in socialOffice]):
                print('invest2')
                dummyInvest = 1
            elif "11 kap. 1 § socialtjänstlagen" in fullText:
                print('invest3')
                dummyInvest = 1
            else:
                print('invest4')
                for term in investigationHelper:
                    if term in findSentence('utredning', fullText):
                        print('invest5')
                        dummyInvest = 1
                        break
                    else:
                        print('invest6')
                        dummyInvest = 0
                        continue
        
        #Main hearing 
        for term in mainHearingKey:
            if findSentence(term, fullText) and 'utan' not in findSentence(term, fullText):
                print('mainhear1: ' + term)
                dummyMainHear = 1
                break
            elif findSentence(term, fullText) and 'ingen' not in findSentence(term, fullText):
                print('mainhear2: ' + term)
                dummyMainHear = 1
                break
            else:
                print('mainhear2: ' + key)
                dummyMainHear = 0
                continue
        
        print('Family names:')
        print("Child first name: "+childNameFirst)
        print("Sv first name: "+svNameFirst)
        print("Plaint first name: "+plaintNameFirst)
        print('sv adress: '+ cityString)
        
        #Format results
        i = ''.join(i.split())
        date = ''.join(date.split())
        
        #Fill dataframe with search results
        data['Barn'].append(i)
        data["File Path"].append(file)
        data['Domare'].append(judgeName.lower())
        data["Page Count"].append(pageCount)
        data['Rättelse'].append(dummyRat)
        data['Målnr'].append(caseNo)
        data["Tingsrätt"].append(courtName)
        data['År avslutat'].append(date)
        data['Deldom'].append(dummyDel)
        data['Kärande förälder'].append(plaintNo) 
        data['Svarande förälder'].append(svNo)   
        data['Kär advokat'].append(dummyOmbPlaint)
        data['Sv advokat'].append(defOmbud)
        data['Sv utlandet'].append(dummyAbroad)
        data['Sv okontaktbar'].append(dummyUnreach)
        data['Utfall'].append(dummyOut)   
        data['Umgänge'].append(dummyVisit)
        data['Stadigvarande boende'].append(dummyPhys)
        data['Underhåll'].append(dummyAlimon)                
        data['Enl överenskommelse'].append(dummyAgree)           
        data['Snabbupplysning'].append(dummyInfo)          
        data['Samarbetssamtal'].append(dummyCoop)
        data['Utredning'].append(dummyInvest)
        data['Huvudförhandling'].append(dummyMainHear)

#Dataframe created from dictionary
df = pd.DataFrame(data)
with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    print(df)

#Save to csv
#df.to_csv(output_path, sep = ',', encoding='utf-8-sig')

print("---Saved as CSV---")
print('Unreadable: ')
print(noUnreadable)




        
    
        
        
            
