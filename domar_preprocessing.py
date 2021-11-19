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
pdf_dir = "P:/2020/14/Kodning/Test-round-1/check_cases"
output_path = 'P:/2020/14/Kodning/Test-round-1/custody_data_test1.csv'

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
            print(i)
            break
    return result

def termLoop(termList, part):
    for term in termList:
        if term in part:
            dummy = 1
            break
        else:
            dummy = 0
            continue
    return dummy

def city(string,i):
    stringList = list((string.strip()).split(" "))
    return stringList[-i]

"""
sample_files = ["P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alings+s TR T 783-13 Aktbil 46, DOM - Ylva Stenberg, Mikael T+.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 1780-08 Dom 2009-01-15.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 1650-08 Dom 2009-09-04.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 173-18 Aktbil 24, DOM (DELDOM) - Faeza Alnasser,.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 1916-09 Dom 2009-10-09.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/T 1001-15 Dom.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 1530-17 Dom 2017-09-13.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 90-12 Deldom 2012-11-16.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 6435-17 Dom 2018-06-21.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 6899-10 Dom 2011-06-17.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 6166-17 Dom 2019-04-17.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 4426-12 Dom 2013-04-16.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 3581-14 Dom 2014-12-17.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 4179-14 Deldom 2015-01-28.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 9594-12 Dom 2013-08-12.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 5948-11 Dom 2013-12-09.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 1464-16 Dom 2016-05-18.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 14945-19 Dom 2020-05-06.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 2509-13 Dom 2013-10-28.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 2216-18 Dom 2019-02-07.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 9438-16 Dom 2017-06-12.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 1841-18 Dom 2019-03-25.pdf",	"P:/2020/14/Tingsrätter/Blekinge/Domar/all_cases/Blekinge TR T 1054-18 Aktbil 18, DOM - Mohamad Abubakar, Hurria.pdf",	"P:/2020/14/Tingsrätter/Blekinge/Domar/all_cases/Blekinge TR T 2435-14 Aktbil 64, DOM - Issam Helal, Fatima Hhaf.pdf",	"P:/2020/14/Tingsrätter/Blekinge/Domar/all_cases/Blekinge TR T 115-10 Aktbil 106, DOM - Birgitta Ström, Mikael S.pdf",	"P:/2020/14/Tingsrätter/Blekinge/Domar/all_cases/Blekinge TR T 2035-06 Dom 2008-08-11.pdf",	"P:/2020/14/Tingsrätter/Blekinge/Domar/all_cases/Blekinge TR T 651-19 Aktbil 75, DOM - Conny Jöreskär, Maria Jö.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 1005-15 2016-02-12 Deldom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 1190-16 2017-01-12 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 1900-18 2019-03-20 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 1820-08 2009-02-04 Deldom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 1786-08 2009-06-08 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 663-13 2014-05-09 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 1284-17 2018-04-05 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 2654-14 2015-06-11 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 2907-16 2018-01-26 Dom.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 1130-17 Dom 2017-09-14.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 119-12 Dom 2013-02-04.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 363-19 Dom 2019-05-10.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 1558-08 Dom 2009-05-12.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 255-17 Dom 2018-04-20.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 2778-08 Dom 2008-12-09.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 1633-17 Dom 2018-08-29.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 2250-20 Dom 2020-08-17.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 749-12 Dom 2013-07-02.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 2880-08 Deldom 2009-08-19.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 3082-14 Deldom 2015-07-09.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 3405-12 Dom 2013-08-15.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 288-18 Dom 2018-03-12.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 1262-12 Deldom 2012-12-12.pdf",	"P:/2020/14/Tingsrätter/Gotland/Domar/all_cases/Gotlands TR T 1028-15 Dom 2016-05-27.pdf",	"P:/2020/14/Tingsrätter/Gotland/Domar/all_cases/Gotlands TR T 296-16 Dom 2016-11-24.pdf",	"P:/2020/14/Tingsrätter/Gotland/Domar/all_cases/Gotlands TR T 161-18 Dom 2018-06-29.pdf",	"P:/2020/14/Tingsrätter/Gotland/Domar/all_cases/Gotlands TR T 236-19 Dom 2020-11-23.pdf",	"P:/2020/14/Tingsrätter/Gotland/Domar/all_cases/Gotlands TR T 829-18 Dom 2018-12-11.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/G+llivare TR T 792-16 Aktbil 56, DOM - Patrik Malmstr+m, Katari.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gällivare TR T 190-09 Dom 2009-08-21.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/G+llivare TR T 55-20 Aktbil 26, DOM - Cecilia Norgren, Kent No.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/G+llivare TR T 146-10 Aktbil 143, DOM - Dharma Johansson, Robert.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/G+llivare TR T 627-18 Aktbil 57, DOM - Arthur Arnautovic, Louis.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 2398-13 Dom 2014-06-05.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 3442-11 Dom 2012-10-31.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 3276-17 Dom 2018-04-12.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 3280-12 Dom 2013-01-22.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 969-10 Dom 2010-12-09.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 2069-13 Dom 2016-02-02.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 2338-09 Dom 2010-03-15.pdf",	"P:/2020/14/Tingsrätter/Göteborg/Domar/all_cases/Göteborgs TR T 8983-19 Dom 2020-04-17.pdf",	"P:/2020/14/Tingsrätter/Göteborg/Domar/all_cases/Göteborgs TR T 9236-17 Dom 2018-07-03.pdf",	"P:/2020/14/Tingsrätter/Göteborg/Domar/all_cases/Göteborgs TR T 9501-18 Dom 2018-10-31.pdf",	"P:/2020/14/Tingsrätter/Göteborg/Domar/all_cases/Göteborgs TR T 2027-19 Dom 2020-05-05.pdf",	"P:/2020/14/Tingsrätter/Göteborg/Domar/all_cases/Göteborgs TR T 15569-19 Dom 2020-02-10.pdf",	"P:/2020/14/Tingsrätter/Göteborg/Domar/all_cases/Göteborgs TR T 13072-16 Deldom 2017-07-25.pdf",	"P:/2020/14/Tingsrätter/Göteborg/Domar/all_cases/Göteborgs TR T 15313-18 Dom 2019-02-21.pdf",	"P:/2020/14/Tingsrätter/Göteborg/Domar/all_cases/Göteborgs TR T 11341-18 Dom 2019-10-29.pdf",	"P:/2020/14/Tingsrätter/Göteborg/Domar/all_cases/Göteborgs TR T 5513-16 Dom 2016-06-30.pdf",	"P:/2020/14/Tingsrätter/Göteborg/Domar/all_cases/Göteborgs TR T 1172-19 Dom 2019-11-18.pdf",	"P:/2020/14/Tingsrätter/Göteborg/Domar/all_cases/Göteborgs TR T 13477-17 Dom 2018-09-05.pdf",	"P:/2020/14/Tingsrätter/Göteborg/Domar/all_cases/Göteborgs TR T 8874-16 Deldom 2017-04-07.pdf",	"P:/2020/14/Tingsrätter/Göteborg/Domar/all_cases/Göteborgs TR T 9568-19 Dom 2020-02-20.pdf",	"P:/2020/14/Tingsrätter/Halmstad/Domar/all_cases/Halmstads TR T 1953-14 Dom 2014-09-19.pdf",	"P:/2020/14/Tingsrätter/Halmstad/Domar/all_cases/Halmstads TR T 1787-19 Dom 2019-11-06.pdf",	"P:/2020/14/Tingsrätter/Halmstad/Domar/all_cases/Halmstads TR T 1667-16 Dom 2017-07-04.pdf",	"P:/2020/14/Tingsrätter/Halmstad/Domar/all_cases/Halmstads TR T 1075-09 Dom 2009-08-14.pdf",	"P:/2020/14/Tingsrätter/Halmstad/Domar/all_cases/Halmstads TR T 1620-18 Dom 2019-07-02.pdf",	"P:/2020/14/Tingsrätter/Halmstad/Domar/all_cases/Halmstads TR T 2887-14 Dom 2015-10-08.pdf",	"P:/2020/14/Tingsrätter/Halmstad/Domar/all_cases/Halmstads TR T 1884-08 Dom 2012-03-12.pdf",	"P:/2020/14/Tingsrätter/Haparanda/Domar/all_cases/Haparanda TR T 823-16 Dom 2017-12-14.pdf",	"P:/2020/14/Tingsrätter/Haparanda/Domar/all_cases/Haparanda TR T 619-19 Dom 2020-04-21.pdf",	"P:/2020/14/Tingsrätter/Haparanda/Domar/all_cases/Haparanda TR T 446-18 Dom 2019-04-26.pdf",	"P:/2020/14/Tingsrätter/Haparanda/Domar/all_cases/Haparanda TR T 392-20 Dom 2020-08-03.pdf",	"P:/2020/14/Tingsrätter/Haparanda/Domar/all_cases/Haparanda TR T 354-16 Deldom 2017-03-07.pdf",	"P:/2020/14/Tingsrätter/Hässleholm/Domar/all_cases/Hässleholms TR T 162-09 Dom 2009-06-22.pdf",	"P:/2020/14/Tingsrätter/Hässleholm/Domar/all_cases/Hässleholms TR T 725-15 Dom 2015-08-20.pdf",	"P:/2020/14/Tingsrätter/Hässleholm/Domar/all_cases/Hässleholms TR T 1652-09 Dom 2010-11-01.pdf",	"P:/2020/14/Tingsrätter/Hässleholm/Domar/all_cases/Hässleholms TR T 1327-13 Dom 2015-05-06.pdf",	"P:/2020/14/Tingsrätter/Hässleholm/Domar/all_cases/Hässleholms TR T 798-16 Dom 2016-12-01.pdf",	"P:/2020/14/Tingsrätter/Hässleholm/Domar/all_cases/Hässleholms TR T 329-12 Dom 2013-09-12.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 1458-17 Dom 2018-10-22.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 3092-11 Dom 2012-05-16.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 654-14 Dom 2015-12-18.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 3778-14 Dom 2014-12-22.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 4268-19 Dom 2021-02-05.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 1639-18 Dom 2018-10-08.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 1394-16 Dom 2018-05-09.pdf",	"P:/2020/14/Tingsrätter/Linköping/Domar/all_cases/Linköpings TR T 2645-19 Dom 2019-11-21.pdf",	"P:/2020/14/Tingsrätter/Linköping/Domar/all_cases/Linköpings TR T 473-18 Dom 2018-09-13.pdf",	"P:/2020/14/Tingsrätter/Linköping/Domar/all_cases/Linköpings TR T 782-19 Dom 2020-01-23.pdf",	"P:/2020/14/Tingsrätter/Linköping/Domar/all_cases/Linköpings TR T 1798-20 Dom 2020-11-17.pdf",	"P:/2020/14/Tingsrätter/Linköping/Domar/all_cases/Linköpings TR T 1417-15 Dom 2016-01-20.pdf",	"P:/2020/14/Tingsrätter/Linköping/Domar/all_cases/Linköpings TR T 4184-14 Deldom 2015-11-06.pdf",	"P:/2020/14/Tingsrätter/Linköping/Domar/all_cases/Linköpings TR T 3078-14 Dom 2014-11-18.pdf",	"P:/2020/14/Tingsrätter/Lund/Domar/all_cases/Lunds tingsrätt T 6758-09 2011-12-07 Dom.pdf",	"P:/2020/14/Tingsrätter/Lund/Domar/all_cases/Lunds tingsrätt T 629-18 2018-04-05 Dom.pdf",	"P:/2020/14/Tingsrätter/Lund/Domar/all_cases/Lunds tingsrätt T 3583-18 2018-08-15 Dom.pdf",	"P:/2020/14/Tingsrätter/Lund/Domar/all_cases/Lunds tingsrätt T 3878-08 2010-05-07 Dom.pdf",	"P:/2020/14/Tingsrätter/Lund/Domar/all_cases/Lunds tingsrätt T 1321-17 2017-11-16 Deldom.pdf",	"P:/2020/14/Tingsrätter/Lund/Domar/all_cases/Lunds tingsrätt T 101-18 2018-04-13 Dom.pdf",	"P:/2020/14/Tingsrätter/Lund/Domar/all_cases/Lunds tingsrätt T 6302-11 2013-03-06 Dom.pdf",	"P:/2020/14/Tingsrätter/Lund/Domar/all_cases/Lunds tingsrätt T 2076-16 2016-06-15 Dom.pdf",	"P:/2020/14/Tingsrätter/Lund/Domar/all_cases/Lunds tingsrätt T 1235-12 2013-01-15 Dom.pdf",	"P:/2020/14/Tingsrätter/Lund/Domar/all_cases/Lunds tingsrätt T 6441-10 2011-07-26 Deldom.pdf",	"P:/2020/14/Tingsrätter/Lund/Domar/all_cases/Lunds tingsrätt T 5024-09 2010-01-12 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 2892-12 2012-10-15 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 1618-18 2018-04-12 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 2995-17 2018-10-12 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 5710-19 2020-04-17 Deldom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 11549-10 2011-07-13 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 4857-18 2018-12-20 Deldom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 10834-12 2014-06-19 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 7989-14 2016-02-26 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 7234-08 2008-10-30 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 2305-12 2012-12-28 Deldom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 1257-16 2017-08-25 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 7150-10 2012-01-24 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 267-11 2012-01-18 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 7608-15 2016-07-07 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 3745-11 2013-01-10 Dom.pdf",	"P:/2020/14/Tingsrätter/Mora/Domar/all_cases/Mora TR T 18-13 Aktbil 67, DOM - Lennart Vallin, Natalia .pdf",	"P:/2020/14/Tingsrätter/Mora/Domar/all_cases/Mora TR T 153-18 Aktbil 73, DOM - Petra Zinderland, Stefan.pdf",	"P:/2020/14/Tingsrätter/Mora/Domar/all_cases/Mora TR T 1589-17 Aktbil 53, DOM - Miki Blessing, Maria Dan.pdf",	"P:/2020/14/Tingsrätter/Mora/Domar/all_cases/Mora TR T 412-20 Aktbil 14, DOM - Mikael Andersson, Chenih.pdf",	"P:/2020/14/Tingsrätter/Mora/Domar/all_cases/Mora TR T 1113-08 Dom 2008-08-29.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 6317-12 Dom 2014-05-13.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 3876-08 Dom 2010-04-20.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 5597-15 Dom 2016-09-22.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 144-17 Dom 2018-04-13.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 343-11 Dom 2011-04-05.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 3910-20 Dom 2021-03-31.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 358-11 Dom 2011-02-23.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 6047-09 Dom 2010-02-24.pdf",	"P:/2020/14/Tingsrätter/Norrköping/Domar/all_cases/Norrköpings TR T 1940-17 Dom 2018-09-28.pdf",	"P:/2020/14/Tingsrätter/Norrköping/Domar/all_cases/Norrköpings TR T 404-19 Dom 2019-02-26.pdf",	"P:/2020/14/Tingsrätter/Norrköping/Domar/all_cases/Norrköpings TR T 2778-18 Dom 2019-01-14.pdf",	"P:/2020/14/Tingsrätter/Norrköping/Domar/all_cases/Norrköpings TR T 3546-18 Dom 2018-12-04.pdf",	"P:/2020/14/Tingsrätter/Norrköping/Domar/all_cases/Norrköpings TR T 2075-12 Dom 2013-11-20.pdf",	"P:/2020/14/Tingsrätter/Norrköping/Domar/all_cases/Norrköpings TR T 1482-10 Dom 2011-06-15.pdf",	"P:/2020/14/Tingsrätter/Norrköping/Domar/all_cases/Norrköpings TR T 2510-08 Dom 2009-02-24.pdf",	"P:/2020/14/Tingsrätter/Norrköping/Domar/all_cases/Norrköpings TR T 2358-11 Deldom 2012-05-30.pdf",	"P:/2020/14/Tingsrätter/Norrtälje/Domar/all_cases/Norrtälje TR T 2422-11 Dom 2012-10-24.pdf",	"P:/2020/14/Tingsrätter/Norrtälje/Domar/all_cases/Norrtälje TR T 556-18 Dom 2019-10-16.pdf",	"P:/2020/14/Tingsrätter/Norrtälje/Domar/all_cases/Norrtälje TR T 869-12 Dom 2013-05-02.pdf",	"P:/2020/14/Tingsrätter/Norrtälje/Domar/all_cases/Norrtälje TR T 414-11 Dom 2012-12-21.pdf",	"P:/2020/14/Tingsrätter/Norrtälje/Domar/all_cases/Norrtälje TR T 2035-09 Dom 2010-04-19.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 3515-18 Dom 2019-01-10.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 2248-18 Aktbil 47, DOM (DELDOM) - Mohammad Al Sat.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 301-19 Dom 2019-09-06.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 576-13 Dom 2013-05-13.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 2592-14 Aktbil 17, DOM - Nicklas Kellgren, Theres.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 2911-15 Dom 2016-12-20.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 981-18 Dom 2018-10-24.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 498-19 Dom 2019-07-19.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 1046-15 Dom 2016-06-22.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 275-17 Dom 2018-02-27.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 2120-10 Dom 2011-02-17.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 245-15 Dom 2016-09-07.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 1342-19 Dom 2020-08-24.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 2262-19 Deldom 2020-04-27.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 10005-15 Dom 2017-09-28.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 7940-09 Dom 2010-01-13.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 9593-18 Deldom 2019-12-17.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 3835-15 Dom 2016-02-26.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 2471-11 Dom 2012-06-08.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 3849-08 Dom 2009-02-26.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 1705-12 Deldom 2012-11-30.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 6633-13 Dom 2013-11-18.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 5018-17 Dom 2018-05-14.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 8241-08 Dom 2009-03-17.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 3939-16 Dom 2016-09-14.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 1989-19 Dom 2020-01-08.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 837-18 Dom 2018-10-16.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 6695-17 Dom 2019-05-29.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 5923-15 Deldom 2016-03-09.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 4133-14 Deldom 2015-01-21.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 5151-18 Dom 2019-01-07.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 4504-20 Dom 2020-10-16.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 7472-15 Dom 2016-03-18.pdf",	"P:/2020/14/Tingsrätter/Stockholm/Domar/all_cases/Stockholms TR T 16421-14 Dom 2016-02-09.pdf",	"P:/2020/14/Tingsrätter/Stockholm/Domar/all_cases/Stockholms TR T 11208-15 Deldom 2016-09-23.pdf",	"P:/2020/14/Tingsrätter/Stockholm/Domar/all_cases/Stockholms TR T 2339-21 Dom 2021-06-03.pdf",	"P:/2020/14/Tingsrätter/Stockholm/Domar/all_cases/Stockholms TR T 11965-17 Dom 2018-10-01.pdf",	"P:/2020/14/Tingsrätter/Stockholm/Domar/all_cases/Stockholms TR T 13783-19 Dom 2020-05-27.pdf",	"P:/2020/14/Tingsrätter/Stockholm/Domar/all_cases/Stockholms TR T 3242-16 Dom 2018-02-28.pdf",	"P:/2020/14/Tingsrätter/Stockholm/Domar/all_cases/Stockholms TR T 2264-15 Dom 2016-05-04.pdf",	"P:/2020/14/Tingsrätter/Stockholm/Domar/all_cases/Stockholms TR T 14909-20 Dom 2020-12-03.pdf",	"P:/2020/14/Tingsrätter/Stockholm/Domar/all_cases/Stockholms TR T 14118-14 Dom 2015-10-21.pdf",	"P:/2020/14/Tingsrätter/Sundsvall/Domar/all_cases/Sundsvalls TR T 1816-19 Dom 2020-06-03.pdf",	"P:/2020/14/Tingsrätter/Sundsvall/Domar/all_cases/Sundsvalls TR T 126-16 Dom 2016-09-23.pdf",	"P:/2020/14/Tingsrätter/Sundsvall/Domar/all_cases/Sundsvalls TR T 2892-18 Deldom 2019-03-28.pdf",	"P:/2020/14/Tingsrätter/Sundsvall/Domar/all_cases/Sundsvalls TR T 1126-20 Dom 2021-04-26.pdf",	"P:/2020/14/Tingsrätter/Sundsvall/Domar/all_cases/Sundsvalls TR T 2143-20 Dom 2021-06-29.pdf",	"P:/2020/14/Tingsrätter/Sundsvall/Domar/all_cases/Sundsvalls TR T 1531-15 Dom 2016-11-04.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 1163-15 Dom 2016-10-05.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 13-20 Dom 2020-12-01.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 3035-14 Dom 2016-01-29.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 2542-15 Dom 2017-03-24.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 1334-15 Dom 2016-06-13.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 271-21 Dom 2021-08-17.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 3487-19 Aktbil 100, DOM - Sultan Ali, Farzana Kous.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 4668-10 Aktbil 97, DOM - exp till Adv.Robert Mj+s.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2679-09 Aktbil 23, DOM - J+rgen Moberg, Johanna M.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1064-20 Dom 2020-10-16.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 3342-19 Dom 2020-09-14.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2361-12 Aktbil 25, DOM - Exp till Stefan Axberg o.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 297-16 Dom 2017-10-05.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 497-14 Dom 2014-12-16.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1642-20 Dom 2020-07-31.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1080-12 Deldom 2013-01-25.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1282-07 Dom 2009-03-18.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 3206-18 Dom 2018-12-14.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 3140-11 Dom 2012-08-31.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 6867-08 Dom 2010-10-14.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 6373-10 Deldom 2011-06-28.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 5144-16 Deldom 2017-05-02.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 3932-17 Deldom 2017-11-01.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 132-17 Dom 2017-08-02.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 5262-17 Dom 2018-05-22.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 3669-18 Dom 2019-01-11.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 1942-17 Dom 2017-09-05.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 7513-18 Deldom 2019-06-20.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 3470-14 Dom 2015-03-11.pdf",	"P:/2020/14/Tingsrätter/Vänersborg/Domar/all_cases/Vänersborgs TR T 2898-15 Dom 2016-09-14.pdf",	"P:/2020/14/Tingsrätter/Vänersborg/Domar/all_cases/Vänersborgs TR T 3536-08 Dom 2009-04-20.pdf",	"P:/2020/14/Tingsrätter/Vänersborg/Domar/all_cases/Vänersborgs TR T 740-16 Dom 2016-06-10.pdf",	"P:/2020/14/Tingsrätter/Vänersborg/Domar/all_cases/Vänersborgs TR T 1197-09 Dom 2010-06-01.pdf",	"P:/2020/14/Tingsrätter/Vänersborg/Domar/all_cases/Vänersborgs TR T 730-19 Dom 2019-10-11.pdf",	"P:/2020/14/Tingsrätter/Vänersborg/Domar/all_cases/Vänersborgs TR T 3178-08 Dom 2010-03-17.pdf",	"P:/2020/14/Tingsrätter/Vänersborg/Domar/all_cases/Vänersborgs TR T 1843-17 Dom 2018-01-08.pdf",	"P:/2020/14/Tingsrätter/Vänersborg/Domar/all_cases/Vänersborgs TR T 6805-11 Deldom 2012-10-08.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 3564-08 Dom 2009-10-23.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 1203-11 Dom 2011-07-01.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 3643-12 Dom 2014-03-20.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 2426-14 Dom 2016-05-04.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 3593-17 Dom 2017-10-24.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 4963-08 Dom 2009-03-26.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 4464-14 Dom 2015-09-11.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 3919-18 Dom 2018-10-09.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 2289-19 Dom 2019-06-28.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 473-19 Dom 2020-01-23.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 4582-13 Dom 2014-10-28.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 3588-18 Dom 2019-05-20.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 5034-17 Dom 2019-09-05.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 3024-13 Dom 2014-05-14.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 1145-13 Dom 2014-09-29.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 1468-15 Dom 2016-05-30.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 3528-13 Dom 2013-11-15.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 5141-19 Dom 2020-07-15.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 4260-16 Dom 2017-05-31.pdf",	"P:/2020/14/Tingsrätter/Ystad/Domar/all_cases/Ystads TR T 1461-18 Dom 2019-06-24.pdf",	"P:/2020/14/Tingsrätter/Ystad/Domar/all_cases/Ystads TR T 3089-16 Dom 2018-06-04.pdf",	"P:/2020/14/Tingsrätter/Ystad/Domar/all_cases/Ystads TR T 24-19 Dom 2019-09-26.pdf",	"P:/2020/14/Tingsrätter/Ystad/Domar/all_cases/Ystads TR T 487-17 Dom 2017-10-04.pdf",	"P:/2020/14/Tingsrätter/Ystad/Domar/all_cases/Ystads TR T 2361-18 Deldom 2019-03-26.pdf",	"P:/2020/14/Tingsrätter/Ångermanland/Domar/all_cases/Ångermanlands TR T 1198-15 Dom 2016-06-09.pdf",	"P:/2020/14/Tingsrätter/Ångermanland/Domar/all_cases/Ångermanlands TR T 1663-17 Dom 2018-07-18.pdf",	"P:/2020/14/Tingsrätter/Ångermanland/Domar/all_cases/Ångermanlands TR T 2740-19 Dom 2020-08-19.pdf",	"P:/2020/14/Tingsrätter/Ångermanland/Domar/all_cases/Ångermanlands TR T 2098-18 Dom 2018-12-06.pdf",	"P:/2020/14/Tingsrätter/Ångermanland/Domar/all_cases/Ångermanlands TR T 1447-16 Dom 2017-12-27.pdf",	"P:/2020/14/Tingsrätter/Ångermanland/Domar/all_cases/Ångermanlands TR T 157-14 Dom 2014-10-27.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 1004-18 Dom 2018-12-07.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 2448-09 Dom 2010-03-25.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 1758-12 Dom 2012-12-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 1425-09 Dom 2009-11-24.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 1049-16 Dom 2017-05-05.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 411-15 Dom 2016-02-18.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 4105-11 Dom 2011-12-22.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 4299-12 Dom 2013-09-19.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 2654-16 Dom 2017-10-27.pdf",	"P:/2020/14/Tingsrätter/Östersund/Domar/all_cases/Östersunds TR T 952-10 Dom 2010-05-19.pdf",	"P:/2020/14/Tingsrätter/Östersund/Domar/all_cases/Östersunds TR T 2-17 Dom 2017-02-28.pdf",	"P:/2020/14/Tingsrätter/Östersund/Domar/all_cases/Östersunds TR T 1316-17 Dom 2017-06-15.pdf",	"P:/2020/14/Tingsrätter/Östersund/Domar/all_cases/Östersunds TR T 273-12 Dom 2012-04-11.pdf",	"P:/2020/14/Tingsrätter/Östersund/Domar/all_cases/Östersunds TR T 3033-09 Dom 2011-05-24.pdf"]
for file in sample_files:
    shutil.copy(file,pdf_dir)
"""
#Read in PDFs
pdf_files = glob.glob("%s/*.pdf" % pdf_dir)
print(pdf_files)

#Initialize variables
noOfFiles = 0
noUnreadable = 0
countries = 'saknas okänd adress  u.s.a. u.s.a usa sekretess afghanistan  albanien  algeriet  andorra  angola  antigua och barbuda  argentina  armenien  australien  azerbajdzjan  bahamas  bahrain  bangladesh  barbados  belgien  belize  benin  bhutan  bolivia  bosnien och hercegovina  botswana  brasilien  brunei  bulgarien  burkina faso  burundi  centralafrikanska republiken  chile  colombia  costa rica  cypern  danmark  djibouti  dominica  dominikanska republiken  ecuador  egypten  ekvatorialguinea  elfenbenskusten  el salvador  eritrea  estland  etiopien  fiji  filippinerna  finland  frankrike  förenade arabemiraten  gabon  gambia  georgien  ghana  grekland  grenada  guatemala  guinea  guinea-bissau  guyana  haiti  honduras  indien  indonesien  irak  iran  irland  island  israel  italien  jamaica  japan  jemen  jordanien  kambodja  kamerun  kanada  kap verde  kazakstan  kenya  kina  kirgizistan  kiribati  komorerna  kongo-brazzaville  kongo-kinshasa  kroatien  kuba  kuwait  laos  lesotho  lettland  libanon  liberia  libyen  liechtenstein  litauen  luxemburg  madagaskar  malawi  malaysia  maldiverna  mali  malta  marocko  marshallöarna  mauretanien  mauritius  mexiko  mikronesiska federationen  moçambique  moldavien  monaco  mon-tenegro  mongoliet  myanmar  namibia  nauru  nederländerna  nepal  nicaragua  niger  nigeria  nordkorea  nordmakedonien  norge  nya zeeland  oman  pakistan  palau  panama  papua nya guinea  paraguay  peru  polen  portugal  qatar  rumänien  rwanda  ryssland  saint kitts och nevis  saint lucia  saint vincent och grenadinerna  salo-monöarna  samoa  san marino  são tomé och príncipe  saudiarabien  schweiz  senegal  seychellerna  serbien  sierra leone  singapore  slovakien  slovenien  somalia  spanien  sri lanka  storbritannien  sudan  surinam  sverige  swaziland  sydafrika  sydkorea  sydsudan  syrien  tadzjikistan  tanzania  tchad  thailand  tjeckien  togo  tonga  trinidad och tobago  tunisien  turkiet  turkmenistan  tuvalu  tyskland  uganda  ukraina  ungern  uruguay  usa  uzbekistan  vanuatu  vatikanstaten  venezuela  vietnam  vitryssland  zambia  zimbabwe  österrike  östtimor  '
emptyString = ''
                
#Define search terms
svarandeSearch = ' Svarande|SVARANDE|Motpart|MOTPART|SVARANDE och KÄRANDE '
defendantNationality = 'medborgare i (\w+ )+sekretess'
party ='((\w+\s?-?(\w+\s?-?)+?){1}((\w+\s?-?)*\w+))\s*[,]\s*(\d{6,10}.?\s*(\d{4})?[,]?\s)?' 
nameCaps = '[A-ZÅÄÖ]{3,}'
idNo ='(\d{6,10}.?.?(\d{4})?[,]?\s)'
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
fastInfoKey = ['snabbupplysning', 'upplysning', 'upplysningar']
corpTalksKey = ['samarbetssamtal','medlingssamtal','medling', 'medlare']
mainHearingKey = ['huvudförhandling' , 'rättegång' , 'sakframställning' , 'förhör' ]
lawyerKey = ["ombud:", 'god man:',  'advokat:', "ombud", 'god man',  'advokat']
investigationKey = ['vårdnadsutredning','boendeutredning','umgängesutredning']
agreementKey = ['samförståndslösning',  'överenskommelse', 'överens']
agreementAdd = ['parterna' ,'framgår' ,'enlighet' ,'följer','fastställa', 'kommit','barnets','bästa']
socialOffice = ['social', 'nämnden', 'kommun']
rejectKey = ['inte längre' , 'avslås']

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
    firstPageFormatted = (pages_text_formatted[1]).split(".")
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
        lastPageFormatted3 = (pages_text_formatted[appendixPageNo-1]).split(".")
        lastPageOG = pages_text[appendixPageNo-1]
        lastPage = lastPageOG.lower()                       
        fullTextOG = (re.split(appendixStart, fullTextOG)[0])  
        fullText = fullTextOG.lower()
        rulingString = ''.join(re.split('_{10,40}',fullTextOG)[1:]).lower()
        headings = re.findall(nameCaps, rulingString)
        try:
            rulingOnly = re.split('yrkanden', rulingString)[0]
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
        print("a")
        for i in childNoRes:   
            print("b")                                          
            i = ''.join(i.split())
            data['Barn'].append(i)
            
            #Get child's name
            try:
                childNameKey = ('([A-ZÅÄÖ][a-zåäöé]+)[,]?[)]?\s*' + i )
                childNameFirst = searchKey(childNameKey, fullTextOG, 1).lower()
            except AttributeError:
                childName = 'not found'
                childNameFirst = 'not found'

            #Add file path and page count for each observation/pdf
            data["File Path"].append(file)
            data["Page Count"].append(pageCount)
            data['Rättelse'].append(dummyRat)
            
            #Case ID for child i
            caseNo = ''.join((searchKey(searchCaseNo, header, 2)).split())
            data['Målnr'].append(caseNo)
            
            #District Court
            courtName = searchLoop(courtSearch, fullText, 0)
            data["Tingsrätt"].append(courtName)

            #Year Closed
            date = searchLoop(dateSearch, header, 1)
            year = date.split('-')[0]
            data['År avslutat'].append(date)
            
            #Deldom
            if 'deldom' in file:
                dummyDel = 1
            else:
                dummyDel = 0
            data['Deldom'].append(dummyDel)
            
            #Plaintiff
            plaintNameFull = kärandeStringOG.split(",")[0]
            try:
                plaintNameFirst = searchKey(nameCaps, plaintNameFull, 0).lower()
            except AttributeError:
                plaintNameFirst = plaintNameFull.split()[0].lower()
            try:
                plaintNo = ''.join(searchKey(idNo, kärandeString, 0).split())
            except AttributeError:
                plaintNo = "-"
            data['Kärande förälder'].append(plaintNo) 

            # Defendant
            svNameFull = svarandeStringOG.split(",")[0]
            try:
                svNameFirst = searchKey(nameCaps, svNameFull, 0).lower()
            except AttributeError:
                svNameFirst = svNameFull.split()[0].lower()
            try:
                svNo = ''.join(searchKey(idNo, svarandeString, 0).split())
            except AttributeError:
                svNo = "-"
            data['Svarande förälder'].append(svNo)            
             
            #Plaintiff representative (Kär advokat)
            if 'ombud' in kärandeString or "god man" in kärandeString or "advokat" in kärandeString:
                dummyOmbPlaint = 1
            else:
                dummyOmbPlaint = 0 
            data['Kär advokat'].append(dummyOmbPlaint)

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
            data['Sv advokat'].append(defOmbud)

            #Defendant abroad 
            if cityString in countries:
                dummyAbroad = 1
            else:
                dummyAbroad = 0
            data['Sv utlandet'].append(dummyAbroad)
            
            #Defendant unreachable
            svUnreach1 = (re.compile(('(han|hon) har inte kunnat få kontakt med ' + svNameFirst))).search(fullText)
            svUnreach2 = (re.compile(('(han|hon) har inte lyckats etablera kontakt med ' + svNameFirst))).search(fullText)

            print(findTwoWords('okän', 'befinn', fullText))
            print(svNameFirst)

            if 'okontaktbar' in fullText:
                if svNameFirst in findSentence('förordnat god man', fullText):
                    print('unreach1')
                    dummyUnreach = 1
                else:
                    print('unreach2')
                    dummyUnreach = 0
            elif svUnreach1 is not None or svUnreach2 is not None:
                print('unreach3')
                dummyUnreach = 1
            elif 'förordnat god man' in fullText:
                if svNameFirst in findSentence('förordnat god man', fullText):
                    print('unreach4')
                    dummyUnreach = 1
                else:
                    print('unreach5')
                    dummyUnreach = 0
            elif 'varken kan bestrida eller medge' in fullText:
                print('unreach6')
                dummyUnreach = 1
            elif 'inte fått någon kontakt' in fullText:
                if 'huvudman' in findSentence('någon kontakt', fullText) or svNameFirst in findSentence('någon kontakt', fullText):
                    dummyUnreach = 1
                    print('unreach7')
                else:
                    dummyUnreach = 999
            elif dummyAbroad == 1 and svGodMan == 1:
                dummyUnreach = 1
                print('unreach8')
            elif svNameFirst in findTwoWords('okän', 'befinn', fullText):
                print('unreach8a')
                dummyUnreach = 1
            else:
                print('unreach9')
                dummyUnreach = 0
            data['Sv okontaktbar'].append(dummyUnreach)
            
            #Outcome
            try:
                findGemensam = findSentence(searchKey('(gemensam)[^m]',rulingOnly,1), rulingOnly)
            except TypeError:
                findGemensam = findSentence('gemensam ', rulingOnly)
            vardnInGemensam = 'vårdn' in findGemensam
            findEnsam = findSentence('ensam', rulingOnly)
            findVardn = findSentence('vårdn', rulingOnly)
            transferToDef = 'till ' + svNameFirst
            transferToPlaint = 'till ' + plaintNameFirst
            vardnInRuling = 'vårdn' in rulingOnly
                        
            if 'vårdn' not in rulingOnly or vardnInRuling and 'påminn' in findVardn or vardnInRuling and 'erinra' in findVardn:
                #No custody ruling in this court record
                print("out1")
                dummyOut = 0
            elif 'käromalet ogillas' in rulingOnly or "lämnas utan bifall" in rulingOnly or 'avskriv' in rulingOnly:
                dummyOut = 4  
                print("out9")
            elif findTwoWords('avslås', 'vårdn', rulingOnly):
                dummyOut = 4
                print("out9a")
            elif 'ska' in findGemensam and 'om' in findGemensam and vardnInGemensam:
                dummyOut = 1
                print("out2")
            elif 'vårdn' in rulingOnly and 'fortsätt' in findGemensam and 'ska' in findGemensam:
                dummyOut = 1
                print("out3")
            elif vardnInGemensam and 'alltjämt ska' in findGemensam:
                dummyOut = 1
                print("out4")
            elif vardnInGemensam and'ska alltjämt' in rulingOnly:
                dummyOut = 1
                print("out5")
            elif vardnInGemensam and 'skall tillkomma' in rulingOnly: 
                dummyOut = 1
                print("out6")
            elif 'vårdn' in findEnsam and plaintNameFirst in findEnsam and 'utan' not in findEnsam:
                dummyOut = 2
                print("out7")
            elif 'vårdn' in findEnsam and svNameFirst in findEnsam and 'utan' not in findEnsam:
                dummyOut = 3
                print("out8")
            elif 'ensam' in rulingOnly and vardnInRuling and plaintNameFirst in findVardn or plaintNameFirst in findEnsam:
                dummyOut = 2
                print("out10")
            elif 'ensam' in rulingOnly and vardnInRuling and  svNameFirst in findVardn or svNameFirst in findEnsam:
                dummyOut = 3
                print("out11")
            elif vardnInRuling and 'överflytt' in rulingOnly and transferToDef in findVardn:
                dummyOut = 3
                print("out12")
            elif vardnInRuling and 'överflytt' in rulingOnly and transferToPlaint in findVardn:
                dummyOut = 2
                print("out13")
            elif vardnInRuling and 'tillerkänn' in findVardn and svNameFirst in findSentence('tillerkänn', rulingOnly):
                dummyOut = 3
                print("out14")
            elif vardnInRuling and 'tillerkänn' in findVardn and plaintNameFirst in findSentence('tillerkänn', rulingOnly):
                dummyOut = 2
                print("out15")
            elif 'bilaga' in rulingOnly and 'överens' in findSentence('bilaga', rulingOnly):
                dummyOut = 999
                print("out16")
            else: 
                dummyOut = 999
                print("out17")
            print(dummyOut)
            data['Utfall'].append(dummyOut)    
            
            #Visitation rights
            for term in rejectKey:
                if findTwoWords('umgänge', childNameFirst, rulingOnly) and term not in findTwoWords('umgänge', childNameFirst, rulingOnly):  
                    print('umg1')
                    if childNameFirst == 'not found':
                        dummyVisit = 999
                    elif 'avslår' in findTwoWords('umgänge', childNameFirst, rulingOnly):
                        print('umg2')
                        dummyVisit = 0
                    elif findTwoWords('semester', childNameFirst, rulingOnly):
                        print('umg2a')
                        dummyVisit = 0
                    elif findTwoWords('bilaga', 'sidorna', rulingOnly):
                            print('umg4')
                            dummyVisit = 999
                    #If umgänge is found in rulingOnly but NOT semester or avslar
                    else:
                        print('umg5')
                        dummyVisit = 1
                #If umgänge is not found in rulingOnly
                else:
                    print('umg6')
                    dummyVisit = 0 
            data['Umgänge'].append(dummyVisit)
            
            #N. Physical custody 
            if childNameFirst in findTwoWords('stadigvarande', plaintNameFirst, rulingOnly) :
                dummyPhys = 1
            elif childNameFirst in findTwoWords('stadigvarande', svNameFirst, rulingOnly):
                dummyPhys = 2
            elif 'bo tillsammans' in rulingOnly: 
                if childNameFirst == 'not found':
                    dummyPhys = 999
                elif childNameFirst in findTwoWords('bo tillsammans', plaintNameFirst, fullText):
                    dummyPhys = 1
                elif childNameFirst in findTwoWords('bo tillsammans', svNameFirst, fullText):
                    dummyPhys = 2
                else:
                    dummyPhys = 999
            elif findTwoWords('bilaga', 'sidorna', rulingOnly):
                    dummyPhys = 999      
            else:
                dummyPhys = 0
            data['Stadigvarande boende'].append(dummyPhys)
            
            #Alimony
            if 'underhåll' in fullText:
                dummyAlimon = 1 
            #Alimony sum
            elif findTwoWords('bilaga', 'sidorna',  rulingOnly):
                    dummyAlimon = 999                    
            else:
                dummyAlimon = 0 
            data['Underhåll'].append(dummyAlimon)
                 
            #Ruling by agreement
            for termAgree in agreementKey:
                if termAgree in fullText:
                    print(termAgree)
                    for termHelper in agreementAdd:
                        v = findTwoWords(termAgree, termHelper, fullText)
                        if v is not emptyString and searchKey(yearSearch, v, 0) is year:
                            print('agree1')
                            dummyAgree = 1
                            break
                        elif v is not emptyString and searchKey(yearSearch, v, 0) is None:
                            print('agree2')
                            dummyAgree = 1 
                            break
                        else:
                            dummyAgree = 0
                            continue
                else:
                    print(termAgree)
                    if svNameFirst in findSentence('yrkandet', fullText) and 'medger' in findSentence('yrkandet', fullText):
                        dummyAgree = 1
                        print('agree4')
                    elif svNameFirst in findSentence('yrkandet', fullText) and 'medgett' in findSentence('yrkandet', fullText):
                        dummyAgree = 1
                        print('agree5')
                    else:
                        dummyAgree = 0 
                        print('agree6')
                break
            data['Enl överenskommelse'].append(dummyAgree)
            
            #Fast information (snabbupplysningar)
            if termLoop(socialOffice, findSentence('yttrat', fullText)):
                dummyInfo = 1
            else:
                dummyInfo = termLoop(fastInfoKey, fullText)
            data['Snabbupplysning'].append(dummyInfo)
            
            #Cooperation talks
            dummyCoop = termLoop(corpTalksKey, fullText)
            for term in corpTalksKey:
                if term in fullText:
                    print('coop1')
                    v = findSentence(term, fullText)
                    print(v)
                    print
                    if v is not emptyString and searchKey(yearSearch, v, 0) is year:
                        print('coop2')
                        dummyCoop = 1
                        break
                    elif v is not emptyString and searchKey(yearSearch, v, 0) is None:
                        print('coop3')
                        dummyCoop = 1   
                        break
                else:
                    print('coop4')
                    dummyCoop = 0
            data['Samarbetssamtal'].append(dummyCoop)
            
            #Investigation
            dummyInvest = termLoop(investigationKey, fullText)
            data['Utredning'].append(dummyInvest)
                        
            #Main hearing 
            for term in mainHearingKey:
                if term in fullText:
                    if 'utan' in findSentence(term, fullText):
                        print('mainhear1')
                        dummyMainHear = 0
                        break
                    else:
                        print('mainhear2')
                        dummyMainHear = 1
                        break
                else:
                    print('mainhear3')
                    dummyMainHear = 0
            data['Huvudförhandling'].append(dummyMainHear)

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
    else:
        print('Error: PDF at path %s not readable!' %(file))
        noUnreadable += 1
    
#Dataframe created from dictionary
print(noUnreadable)
df = pd.DataFrame(data)
with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    print(df)

#Save to csv
#df.to_csv(output_path, sep = ',', encoding='utf-8-sig')

print("---Saved as CSV---")



