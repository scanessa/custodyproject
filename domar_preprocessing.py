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

import re, shutil, glob, io, pandas as pd

from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter

#Define Paths
pdf_dir = "P:/2020/14/Kodning/Test-round-2/check_cases"
output_path = 'P:/2020/14/Kodning/Test-round-2/custody_data_test2.csv'

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
    print(i)
    return result

def termLoop(termList, part):
    for term in termList:
        if term in part:
            dummy = 1
            break
        else:
            dummy = 0
            continue
    print(term)
    return dummy

def city(string,i):
    stringList = (string.strip()).split(" ")
    return stringList[-i]

"""
sample_files = ["P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 75-18 Deldom 2018-08-17.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 544-15 Aktbil 100, DOM (DELDOM) - angående vårdna.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 6484-17 Deldom 2018-07-09.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 9400-10 Deldom 2011-06-10.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 1144-13 Deldom 2014-03-12.pdf",	"P:/2020/14/Tingsrätter/Blekinge/Domar/all_cases/Blekinge TR T 1892-14 Aktbil 19, DOM (DELDOM) - Yaa Fosuah, Mik.pdf",	"P:/2020/14/Tingsrätter/Blekinge/Domar/all_cases/Blekinge TR T 1661-17 Aktbil 57, DOM (DELDOM) - Ali Beool, Ingr.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 2218-19 2020-02-11 Deldom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 3617-17 2018-07-05 Deldom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 3387-18 2019-07-08 Deldom.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 1115-15 Deldom 2016-03-23.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 85-13 Deldom 2013-05-06.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 1649-15 Deldom 2016-01-26.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 531-14 Deldom 2014-10-31.pdf",	"P:/2020/14/Tingsrätter/Gotland/Domar/all_cases/Gotlands TR T 18-16 Deldom 2016-09-14.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 1162-10 Deldom 2011-01-27.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 1627-08 Deldom 2009-07-02.pdf",	"P:/2020/14/Tingsrätter/Göteborg/Domar/all_cases/Göteborgs TR T 592-15 Deldom 2015-09-24.pdf",	"P:/2020/14/Tingsrätter/Göteborg/Domar/all_cases/Göteborgs TR T 1307-15 Deldom 2016-01-08.pdf",	"P:/2020/14/Tingsrätter/Göteborg/Domar/all_cases/Göteborgs TR T 4981-18 Deldom 2018-10-31.pdf",	"P:/2020/14/Tingsrätter/Halmstad/Domar/all_cases/Halmstads TR T 2368-15 Deldom 2016-11-28.pdf",	"P:/2020/14/Tingsrätter/Halmstad/Domar/all_cases/Halmstads TR T 2786-19 Deldom 2020-03-31.pdf",	"P:/2020/14/Tingsrätter/Halmstad/Domar/all_cases/Halmstads TR T 2649-14 Deldom 2015-08-31.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 3564-08 Deldom 2009-12-28.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 4034-07 Deldom 2008-07-03.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 4315-07 Deldom 2008-12-10.pdf",	"P:/2020/14/Tingsrätter/Linköping/Domar/all_cases/Linköpings TR T 3550-17 Deldom 2018-06-11.pdf",	"P:/2020/14/Tingsrätter/Linköping/Domar/all_cases/Linköpings TR T 514-16 Deldom 2016-11-30.pdf",	"P:/2020/14/Tingsrätter/Linköping/Domar/all_cases/Linköpings TR T 3360-14 Deldom 2015-04-10.pdf",	"P:/2020/14/Tingsrätter/Lund/Domar/all_cases/Lunds tingsrätt T 3097-15 2016-09-05 Deldom.pdf",	"P:/2020/14/Tingsrätter/Lund/Domar/all_cases/Lunds tingsrätt T 2304-15 2017-06-21 Deldom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 806-13 2013-02-28 Deldom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 671-09 2009-08-21 Deldom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 6121-12 2013-02-01 Deldom.pdf",	"P:/2020/14/Tingsrätter/Mora/Domar/all_cases/Mora TR T 744-19 Aktbil 30, DOM (DELDOM) - Joakim Cecen, M.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 58-10 Deldom 2010-07-09.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 5960-09 Deldom 2010-07-21.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 5043-09 Deldom 2010-05-19.pdf",	"P:/2020/14/Tingsrätter/Norrköping/Domar/all_cases/Norrköpings TR T 1908-17 Deldom 2018-02-06.pdf",	"P:/2020/14/Tingsrätter/Norrköping/Domar/all_cases/Norrköpings TR T 1795-18 Deldom 2019-03-13.pdf",	"P:/2020/14/Tingsrätter/Norrköping/Domar/all_cases/Norrköpings TR T 3811-08 Deldom 2009-04-16.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 3925-18 Deldom 2019-02-12.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 2040-13 Deldom 2014-06-25.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 1495-11 Aktbil 35, DOM (DELDOM) - Tesalonica Lagu.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 1074-09 Deldom 2010-02-16.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 973-17 Deldom 2017-11-02.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 5161-07 Deldom 2008-03-28.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 7408-09 Deldom 2010-09-28.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 3972-14 Deldom 2015-01-14.pdf",	"P:/2020/14/Tingsrätter/Stockholm/Domar/all_cases/Stockholms TR T 11111-15 Deldom 2016-09-09.pdf",	"P:/2020/14/Tingsrätter/Stockholm/Domar/all_cases/Stockholms TR T 15140-16 Deldom 2018-03-23.pdf",	"P:/2020/14/Tingsrätter/Stockholm/Domar/all_cases/Stockholms TR T 2838-16 Deldom 2016-10-24.pdf",	"P:/2020/14/Tingsrätter/Sundsvall/Domar/all_cases/Sundsvalls TR T 1235-19 Deldom 2019-11-26.pdf",	"P:/2020/14/Tingsrätter/Sundsvall/Domar/all_cases/Sundsvalls TR T 2892-18 Deldom 2019-03-28.pdf",	"P:/2020/14/Tingsrätter/Sundsvall/Domar/all_cases/Sundsvalls TR T 1885-18 Deldom 2019-04-30.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 838-14 Deldom 2014-05-14.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2827-15 Deldom 2016-03-30.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 302-07 Deldom 2007-09-05.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 234-16 Deldom 2016-05-31.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 2876-20 Deldom 2020-08-11.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 7500-19 Deldom 2020-05-27.pdf",	"P:/2020/14/Tingsrätter/Vänersborg/Domar/all_cases/Vänersborgs TR T 867-20 Deldom 2020-09-04.pdf",	"P:/2020/14/Tingsrätter/Vänersborg/Domar/all_cases/Vänersborgs TR T 1783-08 Deldom 2009-03-11.pdf",	"P:/2020/14/Tingsrätter/Vänersborg/Domar/all_cases/Vänersborgs TR T 2683-19 Deldom 2020-02-19.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 1950-10 Deldom 2010-12-29.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 2173-11 Deldom 2014-01-16.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 5706-13 Deldom 2015-05-13.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 158-19 Deldom 2019-11-12.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 3447-11 Deldom 2012-06-01.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 2764-17 Deldom 2018-02-16.pdf",	"P:/2020/14/Tingsrätter/Ystad/Domar/all_cases/Ystads TR T 446-19 Deldom 2019-08-23.pdf",	"P:/2020/14/Tingsrätter/Ystad/Domar/all_cases/Ystads TR T 3081-18 Deldom 2019-08-14.pdf",	"P:/2020/14/Tingsrätter/Ystad/Domar/all_cases/Ystads TR T 2900-17 Deldom 2018-09-26.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 3917-15 Deldom 2016-04-18.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 1792-10 Dom 2012-04-20.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås_TR_T_1659-08_Dom_2009-12-15.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 2068-10 Aktbil 16, DOM - Malin Nilsson, Tony Karl.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 615-13 Aktbil 44, DOM - Kristian Edrud, Kirsti O.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 8507-12 Dom 2014-02-05.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 3951-14 Dom 2015-01-29.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 4393-16 Dom 2016-11-30.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 6162-11 Dom 2013-03-12.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 10398-10 Dom 2011-02-17.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 5783-12 Dom 2013-06-10.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 3422-12 Dom 2013-06-17.pdf",	"P:/2020/14/Tingsrätter/Blekinge/Domar/all_cases/Blekinge TR T 3031-19 Aktbil 24, DOM - Gülcan Düzgün, Mortaza J.pdf",	"P:/2020/14/Tingsrätter/Blekinge/Domar/all_cases/Blekinge TR T 1054-18 Aktbil 18, DOM - Mohamad Abubakar, Hurria.pdf",	"P:/2020/14/Tingsrätter/Blekinge/Domar/all_cases/Blekinge TR T 1051-17 Aktbil 28, DOM - Abbas Haidar, Sukaina Ha.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 3381-20 2021-06-15 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 295-14 2014-04-15 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 3511-09 2011-02-28 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 1466-10 2011-05-09 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 600-19 2019-04-15 Dom.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 1749-17 Dom 2018-08-31.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 40-10 Dom 2010-02-08.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 119-12 Dom 2013-02-04.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 394-17 Dom 2017-11-02.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 461-19 Dom 2019-11-12.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 1386-18 Dom 2019-07-01.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 89-11 Dom 2011-10-31.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 1064-12 Dom 2013-07-30.pdf",	"P:/2020/14/Tingsrätter/Gotland/Domar/all_cases/Gotlands TR T 805-15 Dom 2017-05-16.pdf",	"P:/2020/14/Tingsrätter/Gotland/Domar/all_cases/Gotlands TR T 943-19 Dom 2019-10-17.pdf",	"P:/2020/14/Tingsrätter/Gotland/Domar/all_cases/Gotlands TR T 124-19 Dom 2019-05-17.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/G+llivare TR T 397-12 Aktbil 60, DOM - Peter Zaff, Satu-P+ivi Z.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/G+llivare TR T 978-11 Aktbil 90, DOM - Anders Magnusson, +sa Wa.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/G+llivare TR T 438-14 Aktbil 20, DOM - Hava Gol Zafari, Socialn.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 2294-12 Dom 2012-12-04.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_120935.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_115711.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 408-15 Dom 2016-02-02.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 3299-19 Dom 2020-05-20.pdf",	"P:/2020/14/Tingsrätter/Göteborg/Domar/all_cases/Göteborgs TR T 9681-16 Dom 2017-03-30.pdf",	"P:/2020/14/Tingsrätter/Göteborg/Domar/all_cases/Göteborgs TR T 3063-19 Dom 2021-04-29.pdf",	"P:/2020/14/Tingsrätter/Göteborg/Domar/all_cases/Göteborgs TR T 2172-18 Dom 2019-02-05.pdf",	"P:/2020/14/Tingsrätter/Göteborg/Domar/all_cases/Göteborgs TR T 14242-19 Dom 2020-11-23.pdf",	"P:/2020/14/Tingsrätter/Göteborg/Domar/all_cases/Göteborgs TR T 5000-19 Dom 2019-05-20.pdf",	"P:/2020/14/Tingsrätter/Göteborg/Domar/all_cases/Göteborgs TR T 13472-16 Dom 2016-12-02.pdf",	"P:/2020/14/Tingsrätter/Göteborg/Domar/all_cases/Göteborgs TR T 128-19 Dom 2019-10-22.pdf",	"P:/2020/14/Tingsrätter/Göteborg/Domar/all_cases/Göteborgs TR T 341-20 Dom 2020-09-24.pdf",	"P:/2020/14/Tingsrätter/Halmstad/Domar/all_cases/Halmstads TR T 1984-19 Dom 2019-12-20.pdf",	"P:/2020/14/Tingsrätter/Halmstad/Domar/all_cases/Halmstads TR T 1706-15 Dom 2015-09-22.pdf",	"P:/2020/14/Tingsrätter/Halmstad/Domar/all_cases/Halmstads TR T 2053-17 Dom 2017-12-01.pdf",	"P:/2020/14/Tingsrätter/Halmstad/Domar/all_cases/Halmstads TR T 2478-11 Dom 2011-12-06.pdf",	"P:/2020/14/Tingsrätter/Haparanda/Domar/all_cases/Haparanda TR T 774-15 Dom 2017-02-09.pdf",	"P:/2020/14/Tingsrätter/Haparanda/Domar/all_cases/Haparanda TR T 331-16 Dom 2016-07-13.pdf",	"P:/2020/14/Tingsrätter/Haparanda/Domar/all_cases/Haparanda TR T 354-16 Dom 2017-12-05.pdf",	"P:/2020/14/Tingsrätter/Hässleholm/Domar/all_cases/Hässleholms TR T 542-13 Dom 2014-05-13.pdf",	"P:/2020/14/Tingsrätter/Hässleholm/Domar/all_cases/Hässleholms TR T 35-18 Dom 2018-04-05.pdf",	"P:/2020/14/Tingsrätter/Hässleholm/Domar/all_cases/Hässleholms TR T 725-07 Dom 2009-01-26.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 4109-15 Dom 2016-03-09.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 2758-20 Dom 2020-09-01.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 3671-10 Dom 2011-03-18.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 1177-14 Dom 2014-07-14.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 2378-18 Dom 2019-04-15.pdf",	"P:/2020/14/Tingsrätter/Linköping/Domar/all_cases/Linköpings TR T 756-15 Dom 2015-04-14.pdf",	"P:/2020/14/Tingsrätter/Linköping/Domar/all_cases/Linköpings TR T 1440-18 Dom 2018-06-11.pdf",	"P:/2020/14/Tingsrätter/Linköping/Domar/all_cases/Linköpings TR T 1597-19 Dom 2020-03-16.pdf",	"P:/2020/14/Tingsrätter/Linköping/Domar/all_cases/Linköpings TR T 3693-14 Dom 2015-01-02.pdf",	"P:/2020/14/Tingsrätter/Lund/Domar/all_cases/Lunds tingsrätt T 1154-18 2019-04-03 Dom.pdf",	"P:/2020/14/Tingsrätter/Lund/Domar/all_cases/Lunds tingsrätt T 405-16 2016-05-20 Dom.pdf",	"P:/2020/14/Tingsrätter/Lund/Domar/all_cases/Lunds tingsrätt T 1783-14 2014-10-21 Dom.pdf",	"P:/2020/14/Tingsrätter/Lund/Domar/all_cases/Lunds tingsrätt T 6454-12 2013-02-19 Dom.pdf",	"P:/2020/14/Tingsrätter/Lund/Domar/all_cases/Lunds tingsrätt T 2896-20 2020-11-24 Dom.pdf",	"P:/2020/14/Tingsrätter/Lund/Domar/all_cases/Lunds tingsrätt T 3391-19 2019-09-25 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 9646-14 2015-03-31 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 10046-14 2015-07-01 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 6421-16 2018-03-06 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 1893-14 2014-10-30 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 3272-13 2014-11-19 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 5687-17 2018-10-12 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 6261-09 2010-03-24 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 7501-12 2013-07-05 Dom.pdf",	"P:/2020/14/Tingsrätter/Mora/Domar/all_cases/Mora TR T 1475-11 Aktbil 39, DOM - Vanja Dahlström, Wäinö K.pdf",	"P:/2020/14/Tingsrätter/Mora/Domar/all_cases/Mora TR T 338-20 Aktbil 11, DOM - Abdol Qauom, Hamideh Yag.pdf",	"P:/2020/14/Tingsrätter/Mora/Domar/all_cases/Mora TR T 2236-09 Aktbil 20, DOM - Mora kommun Annelie Lenn.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 967-16 Dom 2016-12-05.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 3731-17 Dom 2017-12-19.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 3351-20 Dom 2020-09-21.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 6425-18 Dom 2019-03-29.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 4089-16 Dom 2017-03-15.pdf",	"P:/2020/14/Tingsrätter/Norrköping/Domar/all_cases/Norrköpings TR T 135-19 Dom 2019-11-21.pdf",	"P:/2020/14/Tingsrätter/Norrköping/Domar/all_cases/Norrköpings TR T 3798-19 Dom 2020-07-23.pdf",	"P:/2020/14/Tingsrätter/Norrköping/Domar/all_cases/Norrköpings TR T 3487-13 Dom 2015-01-30.pdf",	"P:/2020/14/Tingsrätter/Norrköping/Domar/all_cases/Norrköpings TR T 1404-17 Dom 2017-12-20.pdf",	"P:/2020/14/Tingsrätter/Norrköping/Domar/all_cases/Norrköpings TR T 1010-14 Dom 2014-06-27.pdf",	"P:/2020/14/Tingsrätter/Norrtälje/Domar/all_cases/Norrtälje TR T 358-12 Dom 2012-05-30.pdf",	"P:/2020/14/Tingsrätter/Norrtälje/Domar/all_cases/Norrtälje TR T 1170-17 Dom 2018-03-29.pdf",	"P:/2020/14/Tingsrätter/Norrtälje/Domar/all_cases/Norrtälje TR T 427-09 Dom 2010-06-23.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 2470-15 Dom 2016-02-09.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 182-19 Dom 2019-03-04.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 1541-09 Dom 2009-11-20.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 2777-16 Dom 2016-11-29.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 1163-17 Dom 2018-06-28.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 39-15 Dom 2015-11-16.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 1039-11 Dom 2011-08-03.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 515-16 Dom 2016-06-29.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 8114-10 Dom 2011-11-01.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 7085-15 Dom 2016-07-14.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 519-14 Dom 2015-04-01.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 4528-09 Dom 2010-05-31.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 5211-13 Dom 2013-09-23.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 7760-16 Dom 2017-02-28.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 7908-10 Dom 2012-05-21.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 1134-16 Dom 2016-06-01.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 5195-11 Dom 2012-03-19.pdf",	"P:/2020/14/Tingsrätter/Stockholm/Domar/all_cases/Stockholms TR T 15102-14 Dom 2016-06-27.pdf",	"P:/2020/14/Tingsrätter/Stockholm/Domar/all_cases/Stockholms TR T 16894-20 Dom 2021-01-29.pdf",	"P:/2020/14/Tingsrätter/Stockholm/Domar/all_cases/Stockholms TR T 14765-16 Dom 2017-01-20.pdf",	"P:/2020/14/Tingsrätter/Stockholm/Domar/all_cases/Stockholms TR T 10554-15 Dom 2017-04-06.pdf",	"P:/2020/14/Tingsrätter/Stockholm/Domar/all_cases/Stockholms TR T 6423-19 Dom 2020-01-31.pdf",	"P:/2020/14/Tingsrätter/Sundsvall/Domar/all_cases/Sundsvalls TR T 1674-18 Dom 2020-01-03.pdf",	"P:/2020/14/Tingsrätter/Sundsvall/Domar/all_cases/Sundsvalls TR T 1933-16 Dom 2016-12-22.pdf",	"P:/2020/14/Tingsrätter/Sundsvall/Domar/all_cases/Sundsvalls TR T 2542-18 Dom 2019-10-15.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 760-20 Dom 2021-05-20.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 1164-16 Dom 2017-04-12.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 2638-20 Dom 2020-10-27.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2983-11 Aktbil 12, DOM - Orust kommun, Fusia -, A.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2816-19 Dagboksblad 2021-11-04.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 3509-13 Aktbil 90, DOM - Carl Mannheimer, Anielka.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1804-16 Aktbil 25, DOM - Veronica Andersson, Oska.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 3499-18 Dom 2019-09-05.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2173-16 Dom 2016-12-06.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1496-98.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1390-14 Dom 2015-05-13.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 485-15 Dom 2015-04-30.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 2218-10 Dom 2010-05-17.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 5434-16 Dom 2018-08-29.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 2346-14 Dom 2014-09-29.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 5861-10 Dom 2011-11-03.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 3072-18 Dom 2018-09-20.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 449-09 Dom 2010-11-09.pdf",	"P:/2020/14/Tingsrätter/Vänersborg/Domar/all_cases/Vänersborgs TR T 6612-11 Dom 2013-03-07.pdf",	"P:/2020/14/Tingsrätter/Vänersborg/Domar/all_cases/Vänersborgs TR T 1557-12 Dom 2012-06-29.pdf",	"P:/2020/14/Tingsrätter/Vänersborg/Domar/all_cases/Vänersborgs TR T 2252-13 Dom 2013-09-10.pdf",	"P:/2020/14/Tingsrätter/Vänersborg/Domar/all_cases/Vänersborgs TR T 4048-16 Dom 2016-12-09.pdf",	"P:/2020/14/Tingsrätter/Vänersborg/Domar/all_cases/Vänersborgs TR T 2236-16 Dom 2017-02-09.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 633-08 Dom 2009-03-30.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 4021-15 Dom 2016-03-23.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 4050-20 Dom 2020-12-09.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 2158-19 Dom 2019-10-17.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 5692-10 Dom 2011-06-13.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 4425-20 Dom 2020-12-02.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 4319-11 Dom 2014-10-14.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 2954-09 Dom 2009-11-13.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 1422-19 Dom 2019-07-22.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 937-17 Dom 2018-01-24.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 2694-12 Dom 2012-10-16.pdf",	"P:/2020/14/Tingsrätter/Ystad/Domar/all_cases/Ystads TR T 2527-17 Dom 2018-01-30.pdf",	"P:/2020/14/Tingsrätter/Ystad/Domar/all_cases/Ystads TR T 3038-18 Dom 2019-04-30.pdf",	"P:/2020/14/Tingsrätter/Ystad/Domar/all_cases/Ystads TR T 1355-19 Dom 2020-03-03.pdf",	"P:/2020/14/Tingsrätter/Ångermanland/Domar/all_cases/Ångermanlands TR T 1661-16 Dom 2017-06-19.pdf",	"P:/2020/14/Tingsrätter/Ångermanland/Domar/all_cases/Ångermanlands TR T 1739-17 Dom 2018-07-23.pdf",	"P:/2020/14/Tingsrätter/Ångermanland/Domar/all_cases/Ångermanlands TR T 1972-15 Dom 2016-05-26.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/98-99.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 2403-18 Dom 2018-07-27.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 5898-10 Dom 2011-09-09.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 1381-19 Dom 2019-06-05.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/556-00.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 4791-18 Dom 2020-02-12.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 4219-09 Dom 2009-11-10.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 4612-15 Dom 2016-01-26.pdf",	"P:/2020/14/Tingsrätter/Östersund/Domar/all_cases/Östersunds TR T 703-09 Dom 2010-08-09.pdf",	"P:/2020/14/Tingsrätter/Östersund/Domar/all_cases/Östersunds TR T 1939-11 Dom 2011-09-06.pdf",	"P:/2020/14/Tingsrätter/Östersund/Domar/all_cases/Östersunds TR T 2861-12 Dom 2012-12-27.pdf",	"P:/2020/14/Tingsrätter/Östersund/Domar/all_cases/Östersunds TR T 1055-07 Dom 2011-05-05.pdf"]

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
party ='((\w+\s?-?(\w+\s?-?)+?){1}((\w+\s?-?)*\w+))\s*[,]\s*(\d{6,10}.?\s*(\d{4})?[,]?\s)?' 
nameCaps = '[A-ZÅÄÖ]{3,}'
idNo ='((\d{6,10}.?.?(\d{4})?)[,]?\s)'
appendixStart = '((?<!se )Bilaga [1-9]|(?<!se )Bilaga A|sida\s+1\s+av)'
searchCaseNo = 'mål\s*(nr)?[.]?\s*t\s*(\d*.?.?\d*)'
namePlaceHolder = '(?i)((\w+\s?-?(\w+\s?-?)+?){1}((\w+\s?-?)*\w+))'
yearSearch = '\s(\d{4})\s?,?[.]?'
word = '(\w+ )+'

dateSearch = {
    '1' : 'dom\s+(\d*-\d*-\d*)',
    '2' : 'dom\s+sid\s*1\s*[(][0-9]*[)]\s*(\d*-\d*-\d*)',
    '3' : '(\d*-\d*-\d*)'
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
fastInfoKey = ['snabbupplysning', 'upplysning', 'upplysningar', 'snabbyttrande']
corpTalksKey = ['samarbetssamtal','medlingssamtal','medling', 'medlare']
mainHearingKey = ['huvudförhandling' , ' rättegång ' , 'sakframställning' , 'förhör' ]
lawyerKey = ["ombud:", 'god man:',  'advokat:', "ombud", 'god man',  'advokat']
investigationKey = ['vårdnadsutredning','boendeutredning','umgängesutredning']
investigationHelper = ["vårdn", "umgänge", "boende"]
agreementKey = ['samförståndslösning',  'överenskommelse', 'överens', 'medger', 'medgett']
agreementAdd = ['parterna' ,'framgår' ,'enlighet' ,'följer','fastställa', 'kommit','barnets','bästa']
agreementHelper = ['umgänge', 'boende']
socialOffice = ['social', 'nämnden', 'kommun', 'familjerätt']
umgangeKey = ['umgänge', 'umgås']
rejectKey = ['avskriv','käromalet ogillas','lämnas utan bifall','avslå','inte längre','skrivs']  

#Intiialize lists and dictionary to fill
data = {'Barn':[], 'Målnr':[], 'Tingsrätt':[], 'År avslutat':[], 'Deldom':[], 'Kärande förälder':[], 'Svarande förälder':[], 'Kär advokat':[], 'Sv advokat':[], 'Sv utlandet':[], 'Sv okontaktbar':[], 'Utfall':[], 'Umgänge':[], 'Stadigvarande boende':[], 'Underhåll':[], 'Enl överenskommelse':[], 'Snabbupplysning':[], 'Samarbetssamtal':[], 'Utredning':[], 'Huvudförhandling':[], 'Domare':[], "Page Count": [], 'Rättelse': [], "File Path": []}

#Loop over files and extract data
for file in pdf_files:
    print(" ")
    print("Currently reading:")
    print(file)
        
    pageCount = 0
    rsrcmgr = PDFResourceManager()
    retstr = io.StringIO()
    codec = 'utf-8-sig'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    pages_text = []
    pages_text_formatted = []
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,caching=True,check_extractable=True):
            read_position = retstr.tell()
            interpreter.process_page(page)
            retstr.seek(read_position, 0)
            page_text = retstr.read()
            page_text_clean = ' '.join((''.join(page_text)).split())
            pages_text.append(page_text_clean)
            pages_text_formatted.append(page_text)
            pageCount += 1
             
    #Convert full text to clean string
    firstPage = pages_text[0]
    firstPageFormatted = (pages_text_formatted[0]).split(".")
    if "Rättelse" in firstPage:
        fullTextOG = ''.join(pages_text[1:])
        firstPage = ''.join(pages_text[1])
        dummyRat = 1
    else:
        fullTextOG = ''.join(pages_text)
        dummyRat = 0

    splitTextOG = re.split('_{10,40}', fullTextOG)
        
    if len(splitTextOG) > 1: 
        noOfFiles += 1                                                      
        headerOG = re.split('_{10,40}', firstPage)[0]   
        header = headerOG.lower()    
        appendixPage = [i for i, item in enumerate(pages_text) if re.search(appendixStart, item)]
        if not appendixPage:
            appendixPageNo = len(pages_text)
        else:
            appendixPageNo = appendixPage[0]
        lastPageFormatted = '.'.join((pages_text_formatted[appendixPageNo-1]).split(".")) + '.'.join((pages_text_formatted[appendixPageNo-2]).split("."))
        lastPageFormatted3 = (pages_text_formatted[appendixPageNo-2]).split(".")
        lastPageOG = pages_text[appendixPageNo-1]
        lastPage = lastPageOG.lower()                       
        fullTextOG = (re.split(appendixStart, fullTextOG)[0])  
        fullText = fullTextOG.lower()
        rulingString = ''.join(re.split('_{10,40}',fullTextOG)[1:])
        try:
            rulingOnly = re.split('YRKANDEN', rulingString)[0].lower()
        except AttributeError:
            rulingOnly = re.split('(_{15,35}|-{15,35})', rulingString)[0].lower() 
        fullTextList = fullText.split(".")   
        
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
        childNo = set(re.findall('\d{6,8}\s?-\d{4}', rulingString))   
        for i in childNo:
            mistakeChilNos = searchKey("\A197|\A198|\A5|\A6|\A7|\A8", i, 0)
            if mistakeChilNos is None: # child ID should not start with 197 or 198, or 5,6,7,8  
                childNoRes.append(i)   
        
        #Loop to create dictionary with one row per child
        for i in childNoRes:   
            i = ''.join(i.split())
            data['Barn'].append(i)
            
            #Get child's name
            childNameKey = ('([A-ZÅÄÖ][a-zåäöé]+)[,]?\s*[(]?\s*' + i )
            childNameFirst = searchKey(childNameKey, fullTextOG, 1)
            print(fullTextOG)
            print(childNameFirst)
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
            findVardnBarn = findTwoWords('vårdn', 'barn', rulingOnly)
            transferToDef = 'till ' + svNameFirst
            transferToPlaint = 'till ' + plaintNameFirst
            vardnInRuling = 'vårdn' in rulingOnly
            
            print(rulingOnly)
                        
            if 'vårdn' not in rulingOnly or vardnInRuling and 'påminn' in findVardn or vardnInRuling and 'erinra' in findVardn or vardnInRuling and 'upplyser' in findVardn:
                #No custody ruling in this court record
                print("out1")
                dummyOut = 0
            elif 'ska' in findGemensam and 'om' in findGemensam and vardnInGemensam and not any([x in findVardn for x in rejectKey]):
                dummyOut = 1
                print("out2")
            elif 'vårdn' in rulingOnly and 'fortsätt' in findGemensam and 'ska' in findGemensam and not any([x in findVardn for x in rejectKey]):
                dummyOut = 1
                print("out3")
            elif vardnInGemensam and findTwoWords('alltjämt','ska' , findGemensam) and not any([x in findVardn for x in rejectKey]):
                dummyOut = 1
                print("out4")
            elif vardnInGemensam and findTwoWords('alltjämt', 'är', rulingOnly) and not any([x in findVardn for x in rejectKey]):
                dummyOut = 1
                print("out5")
            elif vardnInGemensam and 'skall tillkomma' in rulingOnly and not any([x in findVardn for x in rejectKey]): 
                dummyOut = 1
                print("out6")
            elif 'vårdn' in findEnsam and plaintNameFirst in findEnsam and 'utan' not in findEnsam and not any([x in findVardn for x in rejectKey]):
                dummyOut = 2
                print("out7")
            elif 'vårdn' in findEnsam and svNameFirst in findEnsam and 'utan' not in findEnsam and not any([x in findVardn for x in rejectKey]):
                dummyOut = 3
                print("out8")
            elif 'ensam' in rulingOnly and vardnInRuling and plaintNameFirst in findVardn and not any([x in findVardn for x in rejectKey]):
                dummyOut = 2
                print("out10a")
            elif plaintNameFirst in findEnsam and not any([x in findVardn for x in rejectKey]):
                dummyOut = 2
                print("out10")
            elif 'ensam' in rulingOnly and vardnInRuling and  svNameFirst in findVardn and not any([x in findVardn for x in rejectKey]):
                dummyOut = 3
                print("out11a")    
            elif svNameFirst in findEnsam and not any([x in findVardn for x in rejectKey]):
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
            elif 'käromalet ogillas' in rulingOnly or "lämnas utan bifall" in rulingOnly or 'avskriv' in findVardn:
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
            if childNameFirst == 'not found':
                dummyPhys = 999
                print("phsical custody 1")
            elif childNameFirst in findTwoWords('boende', plaintNameFirst, rulingOnly) and 'skyddat' not in findTwoWords('boende', plaintNameFirst, rulingOnly):
                dummyPhys = 1
                print("phsical custody 2")
            elif childNameFirst in findTwoWords('boende', svNameFirst, rulingOnly):
                dummyPhys = 2
                print("phsical custody 3")
            elif childNameFirst in findTwoWords('bo tillsammans', plaintNameFirst, fullText):
                dummyPhys = 1
                print("phsical custody 4")
            elif childNameFirst in findTwoWords('bo tillsammans', svNameFirst, fullText):
                dummyPhys = 2
                print("phsical custody 5")
            elif childNameFirst in findTwoWords('bo', plaintNameFirst, findSentence('stadigvarande', fullText)):
                dummyPhys = 1  
                print("phsical custody 6")
            elif childNameFirst in findTwoWords('bo', svNameFirst, findSentence('stadigvarande', fullText)):
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
                if svNameFirst in findTwoWords('yrkande', term, fullText):
                    dummyAgree = 1
                    dummyUnreach = 0
                    break
                for termHelper in agreementAdd:
                    findAgree = findTwoWords(termAgree, termHelper, fullText)
                    if findAgree is not emptyString and not any([x in findAgree for x in agreementHelper]):
                        print('agree1')
                        print(termAgree + termHelper)
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
                dummyAgree = 1
                dummyUnreach = 0
               
            #Fast information (snabbupplysningar)
            if termLoop(socialOffice, findSentence('yttra', fullText)):
                dummyInfo = 1
            elif termLoop(socialOffice, findSentence('uppgett', fullText)):
                dummyInfo = 1
            elif '6 kap. 20 § andra stycket föräldrabalken' in fullText:
                dummyInfo = 1 
            else:
                dummyInfo = termLoop(fastInfoKey, fullText)
                  
            #Cooperation talks
            for term in corpTalksKey:
                if term in fullText and 'avslå' not in findSentence(term, fullText):
                    print('coop2')
                    dummyCoop = 1
                    break
                else:
                    print('coop3')
                    dummyCoop = 0  
                    break
               
            #Investigation
            dummyInvest = termLoop(investigationKey, fullText)
            print('invest0')
            if dummyInvest == 0:
                if 'tingsrätt' in findSentence('utredning', fullText):
                    print('invest1')
                    dummyInvest = 1
                else:
                    print('invest2')
                    dummyInvest = 0
                for term in investigationHelper:
                    if term in findSentence('utredning', fullText):
                        print('invest3')
                        dummyInvest = 1
                        break
                    else:
                        print('invest4')
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
                            
            #Name of judge
            try:
                judgeName = ((searchLoop(judgeSearch, lastPageFormatted, 1)).split('\n'))[0]
            except:
                judgeName = 'Not found'
            data['Domare'].append(judgeName.lower())
            
            print('Family names:')
            print("Child first name: "+childNameFirst)
            print("Sv first name: "+svNameFirst)
            print("Plaint first name: "+plaintNameFirst)
            print('sv adress: '+ cityString)
            
            #Fill dataframe with search results
            data["File Path"].append(file)
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

    else:
        print('Error: PDF at path %s not readable!' %(file))
        noUnreadable += 1
#Dataframe created from dictionary
df = pd.DataFrame(data)
with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    print(df)

#Save to csv
#df.to_csv(output_path, sep = ',', encoding='utf-8-sig')

print("---Saved as CSV---")
print('Unreadable: ')
print(noUnreadable)




