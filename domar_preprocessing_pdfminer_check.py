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

import Levenshtein as leven #correct misspelled judge names with this somehow

import re, shutil, glob, io, pandas as pd

from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter

#Define Paths
pdf_dir = "P:/2020/14/Kodning/Test-round-3/check"
output_path = 'P:/2020/14/Kodning/Test-round-4/custody_data_test4.csv'

#Define key functions
def findSentence(string, part):
    sentenceRes = [sentence + '.' for sentence in part.split('.') if string in sentence]
    sentenceString = ''.join(sentenceRes)
    return sentenceString

def findFirstOccur(string, part):
    sentenceRes = [sentence + '.' for sentence in part.split('.') if string in sentence]
    if sentenceRes:
        sentenceString = sentenceRes[0]
    else:
        sentenceString = ''
    return sentenceString
    return sentenceString

def findTwoWordsFirstOccur(string1, string2, part):
    sentenceRes = [sentence + '.' for sentence in part.split('.') if string1 in sentence and string2 in sentence]
    if sentenceRes:
        sentenceString = sentenceRes[0]
    else:
        sentenceString = ''
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

def termLoopFirstOccur(termList, part):
    for term in termList:
        sentence = findFirstOccur(term, part)
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
with open('P:/2020/14/Kodning/all_files/filepaths.txt','r') as f:
    pdf_files = f.read().splitlines() 
"""
"""
unread_files = ["P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 494-14 Aktbil 16, DOM - Petra Pehrsson, Peder Jo.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 1626-14 Aktbil 26, DOM - Camilla Lundgren, Konsta.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 47-10 Dom 2011-01-04.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 1724-18 Dom 2019-05-10.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås_TR_T_1428-17_Dom_2018-03-01.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 925-18 Aktbil 19, DOM - Farhija Abukar, Ali Ahme.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås_TR_T_1655-16_Dom_2018-04-16.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 1929-08 Dom 2009-01-27.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 1850-10 Dagboksblad 2021-07-02.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 580-12 Dom 2013-01-07.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 1505-20 Aktbil 15, DOM - Irina Albared, Basel Alb.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 832-19 Aktbil 89, DOM - Camilla Lundgren, Peter .pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås_TR_T_25-17_Dom_2017-10-27.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 1186-10 Aktbil 28, DOM - Sven Nicolaisen, Therése.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 1588-12 Aktbil 25, DOM - Peter Johansson, Susanne.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/block 25 t 530-17.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 450-15 Dom 2015-05-06.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 5539-12 Dom 2014-01-20.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 3659-19 Dom 2020-09-18.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 8038-12 Dom 2014-05-08.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 8385-16 Dom 2018-11-05.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 520-16 Dom 2017-03-20.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 9198-18 Dom 2020-05-19.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 7053-10 Dom 2011-12-12.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 1055-15 Dom 2016-01-19.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 9168-10 Dom 2011-06-09.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 7897-13 Dom 2015-02-03.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 2851-16 Dom 2017-11-30.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 6741-18 Dom 2019-11-25.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 2580-11 Dom 2013-04-04.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 9797-09 Dom 2011-03-08.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 6532-14 Dom 2015-06-16.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 665-14 Dom 2015-02-18.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 6926-16 Dom 2017-02-06.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 8618-13 Dom 2014-10-22.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 390-19 Dom 2019-09-16.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 7304-13 Dom 2014-04-11.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 7172-12 Dom 2014-01-29.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 7199-13 Dom 2014-01-30.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 6932-12 Dom 2013-02-22.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 5031-08 Dom 2011-03-31.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 5532-16 Dom 2016-10-17.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 7270-11 Dom 2012-08-31.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 9174-13 Deldom 2014-04-24.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 3944-17 Dom 2018-06-20.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 3974-17 Dom 2018-08-29.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 11103-15 Dom 2016-10-04.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 3932-16 Dom 2017-03-22.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 7728-14 Dom 2016-06-15.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 6549-14 Dom 2016-03-21.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 10511-17 Dom 2019-03-22.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 5122-16 Dom 2016-10-07.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 6938-20 Dom 2020-08-25.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 1852-13 Dom 2014-06-02.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 3732-18 Dom 2019-04-08.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 5675-12 Dom 2012-12-06.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 3778-20 Dom 2020-12-16.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 9075-13 Dom 2015-04-07.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 9852-19 Dom 2020-09-21.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 7946-11 Dom 2013-05-02.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 8378-14 Dom 2015-04-08.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 2003-11 Dom 2011-06-17.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 773-14 Dom 2014-09-15.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 648-14 Deldom 2016-01-25.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 9029-14 Dom 2015-11-06.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 433-20 Dom 2020-12-21.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 1778-11 Dom 2013-02-06.pdf",	"P:/2020/14/Tingsrätter/Blekinge/Domar/all_cases/Blekinge TR T 1661-17 Aktbil 57, DOM (DELDOM) - Ali Beool, Ingr.pdf",	"P:/2020/14/Tingsrätter/Blekinge/Domar/all_cases/Blekinge TR T 2532-19 Aktbil 23, DOM - Mike El Hajj, Tagrid El .pdf",	"P:/2020/14/Tingsrätter/Blekinge/Domar/all_cases/Blekinge TR T 559-19 Aktbil 90, DOM - Ted Larsson, Marie Östli.pdf",	"P:/2020/14/Tingsrätter/Blekinge/Domar/all_cases/Blekinge TR T 3214-12 Aktbil 134, DOM - Linda Nilsson, Jimmy Ras.pdf",	"P:/2020/14/Tingsrätter/Blekinge/Domar/all_cases/Blekinge TR T 106-15 Aktbil 19, DOM - Alaa Hajjorefai, Bassam .pdf",	"P:/2020/14/Tingsrätter/Blekinge/Domar/all_cases/Blekinge TR T 1621-19 Aktbil 36, DOM - Fawaz Alhaji Yasin, Neda.pdf",	"P:/2020/14/Tingsrätter/Blekinge/Domar/all_cases/Blekinge TR T 2035-06 Dom 2008-08-11_1.pdf",	"P:/2020/14/Tingsrätter/Blekinge/Domar/all_cases/Blekinge TR T 115-10 Aktbil 106, DOM - Birgitta Ström, Mikael S.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 3176-07 2008-12-12 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 3140-13 2014-02-28 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 2702-20 2021-05-19 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 759-08 2008-10-03 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 3412-08 2009-09-08 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 2215-11 2013-02-21 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 186-19 2019-06-03 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 900-16 2016-12-14 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 1601-11 2012-08-29 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 3136-18 2020-07-01 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 1123-09 2010-01-08 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 2523-20 2020-10-05 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 2764-12 2013-11-14 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 2113-14 2015-11-18 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 2981-17 2018-12-11 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 1897-12 2012-10-30 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 2835-09 2010-10-13 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 2464-13 2013-11-06 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 1562-18 2019-02-20 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 3284-07 2008-12-02 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 2342-07 2009-03-24 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 3700-09 2010-11-15 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 2581-09 2010-09-23 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 3977-11 2012-03-12 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 742-08 2009-02-03 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 2885-08 2009-11-23 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 2069-13 2015-04-28 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 427-11 2013-02-18 Dom.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 1053-15 Dom 2016-04-05.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 1802-18 Dom 2019-07-01.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 1575-14 Dom 2016-06-09.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 1895-20 Dom 2020-11-09.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 2754-11 Dom 2012-06-19.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 2655-10 Dom 2011-11-02.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 1820-11 Dom 2011-11-24.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 1015-11 Dom 2012-01-02.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 523-18 Dom 2018-06-15.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 330-14 Dom 2014-10-03.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 1040-16 Dom 2016-09-14.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 2895-09 Dom 2010-07-05.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 1692-16 Dom 2018-01-16.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 185-09 Dom 2009-08-21.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 892-17 Dom 2017-09-06.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 834-08 Dom 2010-02-12.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 1276-19 Dom 2020-05-15.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 1455-10 Dom 2011-02-11.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 746-18 Dom 2019-03-07.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 2590-16 Dom 2016-11-14.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 3033-12 Dom 2014-12-19.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 1595-19 Dom 2019-09-24.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 1266-14 Dom 2015-11-24.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 4025-20 Dom 2021-06-23.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 2541-18 Dom 2019-06-05.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 1527-18 Dom 2018-08-27.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 3296-17 Dom 2020-03-04.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 643-13 Dom 2014-04-25.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 1514-14 Dom 2015-10-14.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 2018-10 Dom 2011-10-03.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 3300-19 Dom 2020-11-30.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 1872-19 Dom 2019-12-10.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 1863-19 Dom 2020-03-19.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 927-15 Dom 2015-10-14.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 3548-20 Dom 2021-01-19.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 748-18 Dom 2019-01-07.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 3682-18 Dom 2019-01-25.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 1238-19 Dom 2020-07-17.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 156-17 Dom 2017-04-28.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 982-17 Dom 2018-03-02.pdf",	"P:/2020/14/Tingsrätter/Gotlands/Domar/all_cases/Gotlands TR T 550-17 Dom 2017-11-27.pdf",	"P:/2020/14/Tingsrätter/Gotlands/Domar/all_cases/Gotlands TR T 199-16 Dom 2016-05-20.pdf",	"P:/2020/14/Tingsrätter/Gotlands/Domar/all_cases/Gotlands TR T 370-14 Dom 2016-03-15.pdf",	"P:/2020/14/Tingsrätter/Gotlands/Domar/all_cases/Gotlands TR T 132-20 Dom 2020-05-26.pdf",	"P:/2020/14/Tingsrätter/Gotlands/Domar/all_cases/Gotlands TR T 449-16 Dom 2017-03-24.pdf",	"P:/2020/14/Tingsrätter/Gotlands/Domar/all_cases/Gotlands TR T 382-14 Dom 2015-04-29.pdf",	"P:/2020/14/Tingsrätter/Gotlands/Domar/all_cases/Gotlands TR T 924-16 Dom 2017-11-14.pdf",	"P:/2020/14/Tingsrätter/Gotlands/Domar/all_cases/Gotlands TR T 258-15 Dom 2016-05-11.pdf",	"P:/2020/14/Tingsrätter/Gotlands/Domar/all_cases/Gotlands TR T 942-16 Dom 2018-03-06.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/G+llivare TR T 257-13 Aktbil 54, DOM - Anna Jenssen, Fredrik Bj.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/G+llivare TR T 609-08 Aktbil 62, DOM - Pia Yu Nordgren, Yankai .pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gällivare TR T 486-08 Dom 2008-11-13.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/G+llivare TR T 116-19 Aktbil 105, DOM - Sandra Fryc, Fredrik Kar.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/G+llivare TR T 600-13 Aktbil 69, DOM - Christoffer Karlsson, Id.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/G+llivare TR T 521-18 Aktbil 9, DOM - Bayram Dagli, Lisa Dyran.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/G+llivare TR T 558-10 Aktbil 22, DOM - Socialn+mnden G+llivare .pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/G+llivare TR T 291-12 Aktbil 67, DOM - Haikel Arfaoui, Anna-Kar.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gällivare TR T 456-07 Dom 2008-08-29.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/G+llivare TR T 462-19 Aktbil 105, DOM - Lars Johansson, Ogulniya.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 1661-16 Dom 2017-07-06.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_102659.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 2936-14 Dom 2015-02-17.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_113902.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_102020.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 2098-19 Dom 2019-09-02.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 2751-13 Dom 2014-02-18.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 150-11 Dom 2011-05-02.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 1007-11 Dom 2011-05-10.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_101847.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 698-15 Dom 2015-04-28.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 862-18 Dom 2018-08-29.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 3242-07 Dom 2008-11-21.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 3331-09 Dom 2010-11-23.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 2717-18 Dom 2018-10-29.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 1071-11 Dom 2011-09-02.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_102057.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 1328-15 Dom 2017-12-18.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 1184-11 Dom 2012-03-14.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 1787-11 Dom 2012-03-14.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_114237.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 1003-17 Dom 2017-09-13.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_102800.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_120746.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 60-17 Dom 2017-10-26.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 799-15 Dom 2015-11-02.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 12264-19 Dom 2019-11-18.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 12276-19 Dom 2019-10-22.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 7408-21 Dom 2021-09-16.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 5640-18 Dom 2019-04-29.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 6124-17 Dom 2018-05-21.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 7709-16 Dom 2017-12-12.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 2760-21 Dom 2021-06-11.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 4857-19 Dom 2019-11-18.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 7009-16 Dom 2017-01-11.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 14242-19 Dom 2020-11-23.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 14121-19 Dom 2020-10-06.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 6295-18 Dom 2019-10-24.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 12758-18 Dom 2020-02-11.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 8840-15 Dom 2016-03-02.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 16225-18 Dom 2019-03-04.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 16872-20 Dom 2021-02-23.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 13470-17 Dom 2019-02-27.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 16239-16 Dom 2017-11-24.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 6372-17 Dom 2018-03-21.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 1906-16 Dom 2016-10-24.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 19357-20 Dom 2021-02-09.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 6599-18 Dom 2020-03-06.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 13924-19 Dom 2020-02-11.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 12045-16 Dom 2017-08-03.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 5535-15 Dom 2016-03-15.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 12996-15 Dom 2017-03-27.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 19008-19 Dom 2021-06-24.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 634-21 Dom 2021-03-08.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 7435-18 Dom 2019-06-18.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 9794-14 Dom 2016-04-21.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 8496-15 Dom 2016-12-15.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 10233-15 Dom 2017-03-20.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 12410-16 Dom 2017-09-13.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 10906-15 Dom 2017-08-11.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 7154-18 Dom 2018-08-14.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 41-19 Dom 2019-10-23.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 1598-17 Dom 2017-06-12.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 8184-17 Dom 2018-07-12.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 6708-18 Dom 2018-08-28.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 5852-17 Dom 2017-07-21.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 1307-15 Dom 2016-06-09.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 15387-16 Dom 2017-05-29.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 2121-21 Dom 2021-03-25.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 5553-18 Dom 2019-01-08.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 2294-18 Dom 2019-05-13.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 9193-15 Dom 2017-03-09.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 1221-16 Dom 2017-02-22.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 518-20 Dom 2021-03-22.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 12925-15 Dom 2016-04-11.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 7277-15 Dom 2016-11-14.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 2520-12 Dom 2013-05-23.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 1718-17 Dom 2017-11-29.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 635-16 Dom 2016-04-21.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 514-11 Dom 2011-11-28.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 849-13 Dom 2014-04-04.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 1890-18 Dom 2018-12-03.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 1766-11 Dom 2012-05-11.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 1746-10 Dom 2010-08-20.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 1057-18 Dom 2019-03-15.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 1975-16 Dom 2017-06-14.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 2392-12 Dom 2014-08-29.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 2477-20 Dom 2020-11-26.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 188-20 Dom 2020-08-19.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 204-12 Dom 2013-10-10.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 2628-12 Dom 2013-04-23.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 1001-07 Dom 2008-08-08.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 704-18 Dom 2018-10-02.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 1039-09 Dom 2009-09-08.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 30-17 Dom 2017-02-20.pdf",	"P:/2020/14/Tingsrätter/Haparanda/Domar/all_cases/Haparanda TR T 354-16 Dom 2017-12-05.pdf",	"P:/2020/14/Tingsrätter/Haparanda/Domar/all_cases/Haparanda TR T 446-18 Dom 2019-04-26.pdf",	"P:/2020/14/Tingsrätter/Haparanda/Domar/all_cases/Haparanda TR T 453-18 Dom 2018-08-22.pdf",	"P:/2020/14/Tingsrätter/Haparanda/Domar/all_cases/Haparanda TR T 213-20 Dom 2020-10-28.pdf",	"P:/2020/14/Tingsrätter/Haparanda/Domar/all_cases/Haparanda TR T 327-15 Dom 2016-06-03.pdf",	"P:/2020/14/Tingsrätter/Haparanda/Domar/all_cases/Haparanda TR T 109-19 Dom 2019-04-10.pdf",	"P:/2020/14/Tingsrätter/Haparanda/Domar/all_cases/Haparanda TR T 750-19 Dom 2020-10-20.pdf",	"P:/2020/14/Tingsrätter/Haparanda/Domar/all_cases/Haparanda TR T 953-17 Dom 2018-09-20.pdf",	"P:/2020/14/Tingsrätter/Hässleholms/Domar/all_cases/Hässleholms TR T 147-17 Dom 2018-11-02.pdf",	"P:/2020/14/Tingsrätter/Hässleholms/Domar/all_cases/Hässleholms TR T 110-17 Dom 2017-10-09.pdf",	"P:/2020/14/Tingsrätter/Hässleholms/Domar/all_cases/Hässleholms TR T 986-10 Dom 2012-02-14.pdf",	"P:/2020/14/Tingsrätter/Hässleholms/Domar/all_cases/Hässleholms TR T 289-16 Dom 2017-03-09.pdf",	"P:/2020/14/Tingsrätter/Hässleholms/Domar/all_cases/Hässleholms TR T 417-15 Dom 2015-08-28.pdf",	"P:/2020/14/Tingsrätter/Hässleholms/Domar/all_cases/Hässleholms TR T 524-11 Dom 2011-11-25.pdf",	"P:/2020/14/Tingsrätter/Hässleholms/Domar/all_cases/Hässleholms TR T 528-13 Dom 2014-03-20.pdf",	"P:/2020/14/Tingsrätter/Hässleholms/Domar/all_cases/Hässleholms TR T 725-07 Dom 2009-01-26.pdf",	"P:/2020/14/Tingsrätter/Hässleholms/Domar/all_cases/Hässleholms TR T 1447-09 Dom 2011-03-01.pdf",	"P:/2020/14/Tingsrätter/Hässleholms/Domar/all_cases/Hässleholms TR T 386-16 Dom 2016-10-26.pdf",	"P:/2020/14/Tingsrätter/Hässleholms/Domar/all_cases/Hässleholms TR T 1098-13 Dom 2015-06-02.pdf",	"P:/2020/14/Tingsrätter/Hässleholms/Domar/all_cases/Hässleholms TR T 1001-13 Dom 2014-09-03.pdf",	"P:/2020/14/Tingsrätter/Hässleholms/Domar/all_cases/Hässleholms TR T 6-12 Dom 2012-02-08.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 1422-19 Dom 2020-04-01.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 342-18 Dom 2018-04-05.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 1465-15 Dom 2015-09-28.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 4102-14 Dom 2016-05-03.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 3085-14 Dom 2015-01-20.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 4100-17 Dom 2018-05-28.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 2418-15 Dom 2015-09-14.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 939-17 Dom 2018-02-23.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 530-16 Dom 2016-05-02.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 713-17 Dom 2017-12-11.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 3482-11 Dom 2013-05-10.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 4724-11 Dom 2013-03-18.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 4341-18 Dom 2019-02-25.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 186-15 Dom 2015-12-21.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 3791-18 Dom 2020-07-01.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 3134-15 Dom 2016-10-06.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 2642-18 Dom 2020-02-21.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 3119-20 Dom 2021-07-02.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 2595-17 Dom 2019-11-15.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 2918-17 Dom 2018-12-17.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 1134-20 Dom 2020-10-27.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 2040-11 Dom 2011-07-29.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 2965-19 Dom 2020-06-23.pdf",	"P:/2020/14/Tingsrätter/Linköpings/Domar/all_cases/Linköpings TR T 1840-19 Dom 2020-05-19.pdf",	"P:/2020/14/Tingsrätter/Linköpings/Domar/all_cases/Linköpings TR T 4346-19 Dom 2020-01-27.pdf",	"P:/2020/14/Tingsrätter/Linköpings/Domar/all_cases/Linköpings TR T 396-15 Dom 2015-02-18.pdf",	"P:/2020/14/Tingsrätter/Linköpings/Domar/all_cases/Linköpings TR T 3900-14 Dom 2016-04-21.pdf",	"P:/2020/14/Tingsrätter/Linköpings/Domar/all_cases/Linköpings TR T 2961-16 Dom 2017-12-04.pdf",	"P:/2020/14/Tingsrätter/Linköpings/Domar/all_cases/Linköpings TR T 2918-13 Dom 2014-09-05.pdf",	"P:/2020/14/Tingsrätter/Linköpings/Domar/all_cases/Linköpings TR T 857-17 Dom 2017-05-29.pdf",	"P:/2020/14/Tingsrätter/Linköpings/Domar/all_cases/Linköpings TR T 149-14 Dom 2015-01-29.pdf",	"P:/2020/14/Tingsrätter/Linköpings/Domar/all_cases/Linköpings TR T 3360-14 Deldom 2015-04-10.pdf",	"P:/2020/14/Tingsrätter/Linköpings/Domar/all_cases/Linköpings TR T 441-15 Dom 2015-10-13.pdf",	"P:/2020/14/Tingsrätter/Linköpings/Domar/all_cases/Linköpings TR T 1898-17 Dom 2018-02-19.pdf",	"P:/2020/14/Tingsrätter/Linköpings/Domar/all_cases/Linköpings TR T 3426-17 Dom 2019-03-07.pdf",	"P:/2020/14/Tingsrätter/Linköpings/Domar/all_cases/Linköpings TR T 2481-17 Dom 2019-02-14.pdf",	"P:/2020/14/Tingsrätter/Linköpings/Domar/all_cases/Linköpings TR T 3120-16 Dom 2017-09-12.pdf",	"P:/2020/14/Tingsrätter/Linköpings/Domar/all_cases/Linköpings TR T 3691-18 Deldom 2018-11-27.pdf",	"P:/2020/14/Tingsrätter/Linköpings/Domar/all_cases/Linköpings TR T 1601-16 Dom 2016-07-29.pdf",	"P:/2020/14/Tingsrätter/Linköpings/Domar/all_cases/Linköpings TR T 2890-19 Dom 2020-09-03.pdf",	"P:/2020/14/Tingsrätter/Linköpings/Domar/all_cases/Linköpings TR T 3500-14 Dom 2015-09-14.pdf",	"P:/2020/14/Tingsrätter/Linköpings/Domar/all_cases/Linköpings TR T 3208-17 Dom 2018-09-07.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 1228-13 Dom 2014-09-23.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 2128-17 Dom 2018-09-26.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 948-12 Dom 2013-04-05.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 83-15 Dom 2016-05-30.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 3098-17 Dom 2018-04-16.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 1966-17 Dom 2019-05-22.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 1165-17 Dom 2017-11-01.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 1671-15 Dom 2015-10-23.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 1612-12 Dom 2012-10-17.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 914-14 Dom 2014-08-14.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 2582-13 Dom 2014-08-19.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 2125-15 Dom 2016-05-09.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 3699-18 Dom 2019-04-29.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 1600-15 Dom 2015-09-11.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 682-19 Dom 2020-07-01.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 1962-18 Dom 2019-03-07.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 2254-18 Dom 2020-01-21.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 2739-15 Dom 2016-11-14.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 2224-11 Dom 2012-04-30.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 1849-17 Dom 2018-06-20.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 2997-09 2009-09-29 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 5207-12 2014-09-30 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 3237-16 2018-04-23 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 6329-15 2017-10-03 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 3564-06 2008-10-07 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 1695-17 2018-05-25 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 572-10 2010-03-17 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 41-18 2018-10-26 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 3759-19 2021-03-30 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 1853-19 2020-02-25 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 192-14 2015-07-06 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 4656-18 2019-12-17 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 6362-13 2014-10-21 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 518-19 2019-04-25 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 1784-17 2019-01-25 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 5688-18 2019-09-10 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 1449-14 2014-12-02 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 651-19 2020-02-14 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 1393-13 2014-11-21 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 2420-14 2015-02-13 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 3260-08 2009-09-15 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 1412-10 2010-11-23 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 5364-09 2010-07-14 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 4830-20 2020-11-09 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 1273-18 2019-09-13 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 1928-08 2008-12-02 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 5101-14 2016-03-17 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 343-19 2019-03-04 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 3493-06 2009-01-13 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 6442-17 2018-02-26 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 6655-11 2012-04-20 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 779-20 2020-12-01 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 2532-07 2009-03-25 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 1156-11 2011-09-12 Deldom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 3403-13 2014-09-24 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 1181-16 2017-07-05 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 3477-14 2015-12-02 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 2261-08 2009-06-23 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 4698-20 2020-10-30 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 8692-20 2020-10-28 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 8124-18 2019-08-16 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 5973-15 2015-10-15 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 2176-11 2013-02-15 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 3999-12 2013-10-29 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 4708-09 2009-12-03 Deldom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 742-09 2010-05-03 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 1480-17 2017-09-20 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 7522-16 2016-10-31 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 11514-13 2014-03-31 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 8353-16 2017-07-11 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 10858-16 2017-01-19 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 3413-16 2017-03-28 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 2337-20 2020-11-11 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 9778-09 2010-03-26 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 11874-10 2011-06-20 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 2289-20 2020-11-03 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 8031-14 2015-04-10 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 5924-09 2010-01-15 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 11469-17 2019-04-01 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 4009-20 2020-12-17 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 12229-12 2014-05-05 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 10365-13 2015-06-18 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 1134-15 2016-11-04 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 8146-09 2011-09-19 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 2508-12 2013-03-20 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 10260-17 2019-10-15 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 3096-15 2017-02-16 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 5660-20 2020-08-20 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 7088-18 2018-10-23 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 3932-13 2014-12-08 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 8460-10 2011-04-26 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 650-19 2019-05-17 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 8391-13 2013-12-05 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 10235-08 2012-12-21 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 7708-19 2020-11-30 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 6826-16 2018-01-23 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 6252-13 2014-07-01 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 8113-14 2015-08-27 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 11548-10 2012-02-07 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 11392-11 2012-09-21 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 2912-18 2019-10-09 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 8092-17 2018-10-25 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 10225-10 2012-05-29 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 1462-09 2010-09-14 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 10894-11 2013-02-11 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 4058-07 2008-10-24 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 10098-20 2021-02-12 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 3460-19 2019-08-27 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 4238-08 2009-02-26 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 7594-08 2009-03-18 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 10145-12 2016-02-26 Slutligt beslut (ej särskilt uppsatt).pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 3745-11 2013-01-10 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 1226-20 2020-03-26 Dom.pdf",	"P:/2020/14/Tingsrätter/Mora/Domar/all_cases/Mora TR T 1089-10 Aktbil 16, DOM - Siv Johansson, Rolf Geze.pdf",	"P:/2020/14/Tingsrätter/Mora/Domar/all_cases/Mora TR T 363-10 Aktbil 90, DOM - Sylwia Jankowska, Mirosl.pdf",	"P:/2020/14/Tingsrätter/Mora/Domar/all_cases/Mora TR T 595-12 Aktbil 8, DOM - Gemma Doran, Brian Doran.pdf",	"P:/2020/14/Tingsrätter/Mora/Domar/all_cases/Mora TR T 163-10 Aktbil 128, DOM - Gönül Erkisi, Vahap Erki.pdf",	"P:/2020/14/Tingsrätter/Mora/Domar/all_cases/Mora TR T 904-19 Aktbil 34, DOM - Madeleine Helgesson, Lei.pdf",	"P:/2020/14/Tingsrätter/Mora/Domar/all_cases/Mora TR T 1517-07 Aktbil 117, DOM - Sven Åke Carlsson, Anna .pdf",	"P:/2020/14/Tingsrätter/Mora/Domar/all_cases/Mora TR T 1384-08 Aktbil 45, DOM - Niclas Petersson, Lena S.pdf",	"P:/2020/14/Tingsrätter/Mora/Domar/all_cases/Mora TR T 1353-13 Aktbil 46, DOM - Robin Grahn Greibe, Joha.pdf",	"P:/2020/14/Tingsrätter/Mora/Domar/all_cases/Mora TR T 1589-17 Aktbil 53, DOM - Miki Blessing, Maria Dan.pdf",	"P:/2020/14/Tingsrätter/Mora/Domar/all_cases/Mora TR T 520-19 Aktbil 13, DOM - Alemayehu Sime Worku, Fi.pdf",	"P:/2020/14/Tingsrätter/Mora/Domar/all_cases/Mora TR T 772-17 Aktbil 29, DOM - Fatima Gumah, Mahmood Kh.pdf",	"P:/2020/14/Tingsrätter/Mora/Domar/all_cases/Mora TR T 1034-16 Aktbil 111, DOM - Jörgen Bond, Lena Ström.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 5672-16 Dom 2018-02-08.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 999-09 Dom 2010-01-08.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 5830-19 Dom 2019-12-12.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 4182-15 Dom 2016-02-19.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 3190-12 Dom 2013-11-05.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/486-07 Dom 2008-10-10.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 27-15 Dom 2015-12-28.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 489-19 Dom 2019-07-09.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 7523-13 Dom 2014-06-18.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 611-11 Dom 2011-11-30.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 2789-13 Dom 2013-06-17.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 282-07 Dom 2009-03-13.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 71-12 Dom 2012-11-28.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 6362-20 Dom 2021-06-17.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 7850-20 Dom 2020-12-11.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 549-10 Dom 2011-02-15.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 2600-20 Dom 2020-06-24.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 4258-09 Dom 2010-04-28.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 6305-17 Dom 2018-01-05.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 1137-16 Dom 2016-10-21.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 3043-17 Dom 2018-07-24.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 5886-14 Dom 2015-09-11.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 5085-17 Dom 2019-10-18.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 1187-11 Dom 2012-01-13.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 2334-17 Dom 2018-01-09.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 5698-10 Dom 2011-08-18.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 2609-14 Dom 2014-10-20.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 3279-13 Dom 2014-09-23.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 569-14 Dom 2015-06-25.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 1171-15 Dom 2016-10-04.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 3015-19 Aktbil 85, DOM - Sulaiman Abualfita, Dina.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 220-17 Dom 2017-12-08.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 2165-16 Dom 2017-03-16.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 1190-15 Dom 2016-06-27.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 3561-20 Aktbil 68, DOM - Mats Bjernhagen, Josefin.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 888-20 Aktbil 92, DOM - Albertin Gabro, Romel Ga.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 3535-09 Dom 2010-11-09.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 2596-19 Dom 2020-04-21.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 2435-08 Dom 2010-06-14.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 486-14 Dom 2014-04-01.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 1689-20 Aktbil 85, DOM - Reza Adeli, Fatemah Ali .pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 2026-16 Dom 2017-05-30.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 1133-12 Dom 2012-09-10.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 2293-20 Aktbil 33, DOM - Pekka Breitholtz, Lana S.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 622-12 Dom 2013-10-08.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 3496-14 Dom 2016-02-02.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 374-14 Dom 2014-12-01.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 1976-15 Dom 2015-12-02.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 2932-14 Dom 2016-02-09.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 2181-15 Dom 2016-04-04.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 1696-17 Dom 2018-02-08.pdf",	"P:/2020/14/Tingsrätter/Norrtälje/Domar/all_cases/Norrtälje TR T 358-12 Dom 2012-05-30.pdf",	"P:/2020/14/Tingsrätter/Norrtälje/Domar/all_cases/Norrtälje TR T 1728-18 Dom 2020-03-24.pdf",	"P:/2020/14/Tingsrätter/Norrtälje/Domar/all_cases/Norrtälje TR T 218-18 Dom 2018-12-17.pdf",	"P:/2020/14/Tingsrätter/Norrtälje/Domar/all_cases/Norrtälje TR T 2264-11 Dom 2012-08-20.pdf",	"P:/2020/14/Tingsrätter/Norrtälje/Domar/all_cases/Norrtälje TR T 414-11 Dom 2012-12-21.pdf",	"P:/2020/14/Tingsrätter/Norrtälje/Domar/all_cases/Norrtälje TR T 866-12 Dom 2013-03-11.pdf",	"P:/2020/14/Tingsrätter/Norrtälje/Domar/all_cases/Norrtälje TR T 1412-15 Dom 2018-02-27.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 2157-12 Dom 2013-06-14.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 1234-10 Dom 2010-10-26.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 378-20 Dom 2020-11-30.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 1741-14 Aktbil 21, DOM - Fartun Abdulkadir, Shaer.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 766-12 Dom 2012-08-30.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 967-17 Dom 2017-06-12.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 747-13 Dom 2013-04-23.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 534-18 Aktbil 19, DOM - Exp Rim Alraghb, Mohamme.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 2911-18 Dom 2019-06-11.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 1252-16 Dom 2016-11-29.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 2592-14 Aktbil 17, DOM - Nicklas Kellgren, Theres.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 1463-15 Dom 2016-04-18.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 733-10 Dom 2010-11-12.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 1175-18 Dom 2019-05-24.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 576-14 Dom 2014-10-10.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 1474-08 Dom 2008-12-17.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 11-08 Dom 2008-10-09.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 2921-13 Dom 2014-05-16.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 900-15 Dom 2016-05-25.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 1333-14 Dom 2015-11-10.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/Skaraborgs TR T 6297-09 Dom 2010-08-30.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/Skaraborgs TR T 313-09 Dom 2010-09-08.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/T 187-98.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/Skaraborgs TR T 271-09 Dom 2009-12-15.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/Skaraborgs TR T 95-18 Dom 2018-08-30.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/T 1167-04.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/Skaraborgs TR T 2838-14 Dom 2014-10-23.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/Skaraborgs TR T 854-09 Dom 2009-06-17.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/Skaraborgs TR T 3681-17 Dom 2018-09-10.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/Skaraborgs TR T 4833-09 Deldom 2010-06-28.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/Skaraborgs TR T 2872-16 Dom 2017-04-06.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/Skaraborgs TR T 888-14 Dom 2015-08-26.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 66-17 Dom 2017-02-23.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 736-17 Dom 2018-06-11.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 293-15 Dom 2015-11-12.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 1530-08 Dom 2010-04-21.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 1036-12 Dom 2012-10-30.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 467-16 Dom 2016-07-01.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 64-12 Dom 2012-09-28.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 743-18 Dom 2019-01-11.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 461-12 Dom 2013-02-28.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 1357-17 Dom 2018-03-13.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 51-13 Dom 2013-10-18.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 809-20 Dom 2021-06-22.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 510-12 Dom 2012-09-26.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 2906-08 Dom 2008-09-12.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 7591-17 Dom 2018-02-12.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 4555-10 Dom 2012-02-16.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 10091-12 Dom 2013-09-25.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 7270-16 Dom 2016-12-16.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 3464-11 Dom 2012-02-17.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 4297-12 Dom 2013-02-08.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/2176-07.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 9517-12 Dom 2013-09-04.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 6361-15 Dom 2015-11-18.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 11309-19 Dom 2020-06-02.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 10116-09 Dom 2011-05-27.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 1209-16 Dom 2016-11-14.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 8922-19 Dom 2020-06-09.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 3622-15 Dom 2016-03-02.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/1756-07.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 2534-14 Dom 2014-11-05.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 887-09 Dom 2009-04-30.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 2843-09 Dom 2009-10-20.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 2098-10 Dom 2010-11-24.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 7088-08 Dom 2010-07-15.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 7666-13 Dom 2014-06-17.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 3678-11 Dom 2013-06-20.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 6312-17 Dom 2019-02-22.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 9691-10 Dom 2011-08-04.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 6092-19 Dom 2019-12-20.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 9445-16 Dom 2017-09-18.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 6241-13 Dom 2013-12-02.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 3711-13 Dom 2015-03-30.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 4439-17 Dom 2017-06-28.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 743-19 Dom 2019-12-11.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 8260-08 Dom 2009-07-03.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 3989-17 Dom 2018-04-24.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 8932-13 Dom 2014-07-17.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 4885-09 Dom 2010-01-20.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 105-09 Dom 2009-03-12.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 8452-12 Dom 2015-03-11.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 9163-13 Dom 2014-03-26.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 5863-15 Dom 2016-08-24.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/1952-07.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 1151-11 Dom 2012-03-14.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 5896-09 Dom 2010-10-14.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 1046-14 Dom 2015-04-01.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 10375-13 Dom 2014-03-20.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 5099-15 Dom 2016-06-08.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 6579-14 Dom 2015-06-22.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 4833-10 Deldom 2011-03-24.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 76-13 Dom 2014-02-11.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 6024-10 Dom 2011-09-29.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 7348-17 Dom 2018-12-07.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 5535-08 Dom 2010-02-19.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 7530-13 Dom 2014-06-16.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/1835-07.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 7750-10 Dom 2011-02-24.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 4225-11 Dom 2012-03-19.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 8884-14 Dom 2015-08-06.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 98-14 Dom 2015-01-23.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 73-15 Dom 2015-08-25.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 1045-14 Dom 2014-03-13.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 4737-14 Dom 2015-01-23.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 204-10 Dom 2011-04-05.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 5649-10 Dom 2010-10-05.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 5406-16 Dom 2017-07-07.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 10818-11 Dom 2012-08-20.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 2410-18 Dom 2018-09-07.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 8682-10 Dom 2012-05-10.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 6536-17 Dom 2017-11-02.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 979-14 Dom 2014-09-17.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 12936-20 Dom 2021-05-27.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 14498-14 Deldom 2015-05-19.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 6092-19 Dom 2019-09-04.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 3245-18 Dom 2019-04-03.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 15372-18 Dom 2019-12-19.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 460-20 Dom 2021-03-30.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 10895-18 Dom 2019-06-10.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 10534-16 Dom 2017-12-20.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 9901-15 Dom 2016-11-11.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 9939-19 Dom 2020-09-28.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 779-18 Dom 2019-04-02.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 11310-18 Dom 2018-11-05.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 13879-14 Dom 2016-03-15.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 12128-18 Dom 2020-01-17.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 7445-18 Dom 2019-11-14.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 3356-17 Dom 2017-05-19.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 1443-20 Dom 2020-09-04.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 4391-15 Dom 2016-12-20.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 15635-16 Dom 2017-03-17.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 11892-15 Dom 2016-10-07.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 3051-19 Dom 2020-03-16.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 4818-17 Dom 2018-03-20.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 11518-16 Dom 2017-04-07.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 6577-15 Dom 2017-03-31.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 3768-15 Dom 2016-09-27.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 8112-20 Dom 2020-08-04.pdf",	"P:/2020/14/Tingsrätter/Sundsvalls/Domar/all_cases/Sundsvalls TR T 1301-20 Dom 2020-11-17.pdf",	"P:/2020/14/Tingsrätter/Sundsvalls/Domar/all_cases/Sundsvalls TR T 1126-20 Dom 2021-04-26.pdf",	"P:/2020/14/Tingsrätter/Sundsvalls/Domar/all_cases/Sundsvalls TR T 1459-16 Dom 2017-10-18.pdf",	"P:/2020/14/Tingsrätter/Sundsvalls/Domar/all_cases/Sundsvalls TR T 173-18 Dom 2018-11-26.pdf",	"P:/2020/14/Tingsrätter/Sundsvalls/Domar/all_cases/Sundsvalls TR T 1013-16 Dom 2017-02-21.pdf",	"P:/2020/14/Tingsrätter/Sundsvalls/Domar/all_cases/Sundsvalls TR T 260-19 Dom 2020-02-07.pdf",	"P:/2020/14/Tingsrätter/Sundsvalls/Domar/all_cases/Sundsvalls TR T 1812-18 Dom 2020-03-10.pdf",	"P:/2020/14/Tingsrätter/Sundsvalls/Domar/all_cases/Sundsvalls TR T 2180-17 Dom 2018-02-20.pdf",	"P:/2020/14/Tingsrätter/Sundsvalls/Domar/all_cases/Sundsvalls TR T 697-21 Dom 2021-05-27.pdf",	"P:/2020/14/Tingsrätter/Sundsvalls/Domar/all_cases/Sundsvalls TR T 2517-15 Dom 2016-08-12.pdf",	"P:/2020/14/Tingsrätter/Sundsvalls/Domar/all_cases/Sundsvalls TR T 144-20 Dom 2020-10-28.pdf",	"P:/2020/14/Tingsrätter/Sundsvalls/Domar/all_cases/Sundsvalls TR T 2430-19 Dom 2020-12-18.pdf",	"P:/2020/14/Tingsrätter/Sundsvalls/Domar/all_cases/Sundsvalls TR T 718-15 Dom 2016-03-16.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 920-17 Dom 2018-02-14.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 1831-18 Dom 2019-05-21.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 1163-15 Dom 2016-10-05.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 383-19 Dom 2019-05-21.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 1699-16 Dom 2016-09-27.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 1261-19 Dom 2020-03-17.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 1018-19 Dom 2019-07-04.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 263-16 Dom 2017-05-11.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 764-16 Dom 2016-06-22.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 575-19 Dom 2019-12-10.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 2387-16 Dom 2018-02-06.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 2341-19 Dom 2021-01-14.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 3118-17 Dom 2018-02-02.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 2258-15 Dom 2016-11-09.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 1762-18 Dom 2019-03-27.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 12981-10 2011-07-11 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 1178-15 2015-12-01 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 10595-13 2014-10-03 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 471-15 2015-03-24 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 17996-13 2014-05-09 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 11851-14 2015-10-09 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 6780-08 2008-12-04 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 13566-13 2014-03-25 Deldom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 704-16 2016-12-21 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 6051-09 2011-01-27 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 15054-19 2020-06-23 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 7977-14 2015-03-23 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 10420-12 2013-03-15 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 963-09 2009-09-01 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 16822-15 2016-09-30 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 3779-16 2016-10-17 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 4144-13 2013-12-11 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 3395-18 2018-09-04 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 3877-19 2019-10-08 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 4083-16 2016-09-21 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 8469-11 2011-12-20 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 17065-11 2013-01-18 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 6058-19 2019-10-01 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 7917-13 2014-02-07 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 1856-13 2013-11-27 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 10642-18 2018-08-29 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 11266-17 2018-02-02 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 3896-14 2015-02-04 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 6925-10 2011-03-11 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 79-11 2011-02-02 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 16808-14 2016-10-10 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 1191-14 2014-11-24 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 10070-12 2013-06-17 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 18047-18 2019-08-13 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 2866-09 2011-02-23 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 5325-10 2010-06-11 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 14128-13 2014-03-17 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 2014-12 2012-04-25 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 13705-09 2011-02-28 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 1860-09 2010-06-23 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 5210-09 2010-10-05 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 1452-20 2020-06-03 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 19152-19 2020-03-24 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 6238-08 2008-11-27 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 6991-19 2020-12-01 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 15213-15 2017-05-02 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 401-18 2018-05-07 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 6046-09 2009-09-02 Deldom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 13776-16 2018-09-28 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 6823-14 2015-02-18 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 3019-20 2020-11-18 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 12912-12 2013-10-02 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 692-09 2009-05-27 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 14035-19 2020-10-20 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 1486-19 2020-02-05 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 8844-18 2019-05-22 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 8381-15 2015-07-21 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 6813-17 2018-04-06 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 12752-12 2013-12-11 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 16296-16 2017-02-17 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 660-15 2015-03-24 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 12709-13 2014-11-12 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 16635-16 2017-03-09 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 1768-17 2017-09-27 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 14720-17 2018-08-27 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 13636-15 2016-10-11 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 3599-11 2013-02-13 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 16934-12 2014-05-09 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 16301-11 2012-01-27 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 6491-17 2018-01-08 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 9715-08 2009-03-17 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 6266-12 2013-09-25 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 1873-20 2021-06-08 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 14127-19 2020-12-23 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 10880-17 2018-10-17 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 8300-14 2014-11-06 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 10691-07 2009-06-04 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 14365-16 2018-03-28 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 13222-10 2010-12-17 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 14163-16 2018-03-16 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 13730-14 2015-04-01 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 12816-14 2015-03-30 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 12315-20 2021-05-06 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 7570-17 2018-07-30 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 10108-17 2018-05-30 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 6409-12 2013-04-02 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 1828-13 2014-06-02 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 3486-20 2021-06-10 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 9612-13 2014-05-20 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 9767-15 2016-10-10 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 9328-09 2010-03-15 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 16715-16 2017-12-07 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 2300-18 2018-09-20 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 14711-15 2016-01-15 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 6457-18 2019-03-22 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 5842-15 2016-02-05 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 11785-13 2014-11-04 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 14153-14 2015-09-10 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 1384-10 2011-05-17 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 9139-16 2017-06-02 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 13487-17 2017-12-08 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 816-20 2020-10-12 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 14465-18 2019-12-04 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 13227-17 2018-12-20 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 14141-08 2009-03-16 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 15310-10 2011-12-20 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 11961-15 2016-11-03 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 15332-19 2020-10-13 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 5513-19 2020-03-05 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 9694-18 2019-09-23 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 17396-13 2014-03-14 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 6059-16 2018-02-16 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 5421-14 2014-09-08 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 11114-14 2015-09-29 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 14762-10 2011-08-08 Dom.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 414-10 Aktbil 64, DOM - Daniel Olofsson, Marie H.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1914-19 Aktbil 68, DOM - Intisar Al Awad, Kays Al.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2577-18 Aktbil 23, DOM - Fadi Alhawatt, Ameera Al.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1588-13 Aktbil 36, DOM - stadf+st f+rlikning, exp.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1782-11 Aktbil 70, DOM - Helena Meyer, Enrique Ar.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1105-11 Aktbil 23, DOM - Elinor Pernborn, Magnus .pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2679-09 Aktbil 23, DOM - J+rgen Moberg, Johanna M.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 984-19 Aktbil 15, DOM - Suzan Alshihawi, Shamden.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2715-19 Aktbil 81, DOM - Sven Ove J+rgensen, Hild.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1589-14 Aktbil 70, DOM - Marcus Th+rnqvist, Perni.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1163-15 Aktbil 59, DOM - exp parter omb, soc.f+rv.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 3072-13 Aktbil 11, DOM - Gun-Marie Carlsson, Pete.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2102-15 Aktbil 22, DOM - exp till William Callirg.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 3985-11 Aktbil 75, DOM - Karin W+nseth Karlqvist,.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2625-11 Aktbil 117, DOM - Ulrika Gustafsson, Shady.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1132-13 Aktbil 49, DOM - Mats Klerfors, Sonja Kra.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1922-09 Dom 2010-08-06.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2350-15 Dom 2016-04-12.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1906-18 Dom 2018-10-18.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1648-12 Dom 2013-06-19.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2489-11 Dom 2012-11-21.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1207-11 Deldom 2011-10-04.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 688-02.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1047-16 Dom 2017-05-02.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 3338-11 Dom 2012-10-18.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 3360-19 Dom 2020-01-10.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 339-11 Dom 2012-05-22.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2921-10 Dom 2011-07-25.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2977-10 Dom 2011-10-03.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1316-14 Dom 2015-02-10.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 597-95.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1315-99.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1241-11 Dom 2011-10-11.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 493-14 Dom 2014-12-16.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 576-20 Dom 2020-06-16.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2022-14 Dom 2015-04-29.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2440-14 Dom 2015-03-20.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1335-19 Dom 2019-09-02.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1099-97.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 2079-01.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 525-11 Dom 2012-04-18.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1259-11 Dom 2011-12-29.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 3744-13 Dom 2014-06-27.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 1724-15 Dom 2016-06-22.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 1566-18 Dom 2018-11-23.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 5896-19 Dom 2020-12-17.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 3731-11 Dom 2012-09-18.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 4966-12 Dom 2013-11-07.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 3712-15 Dom 2017-03-03.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 5976-11 Dom 2013-09-05.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 7510-10 Dom 2011-11-03.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 5926-10 Dom 2011-10-31.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 2966-08 Dom 2010-11-16.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 4406-11 Dom 2011-09-16.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 695-15 Dom 2015-10-19.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 3166-16 Dom 2016-09-06.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 628-14 Dom 2015-10-28.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 6566-19 Dom 2020-09-18.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 626-15 Deldom 2015-08-31.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 6471-16 Dom 2017-03-17.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 291-11 Dom 2011-03-17.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 2228-11 Dom 2012-12-11.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 2834-15 Dom 2015-07-07.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 77-15 Dom 2015-06-11.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 2930-12 Dom 2013-09-19.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 3340-16 Dom 2017-05-12.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 793-19 Dom 2019-12-09.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 5558-14 Dom 2015-01-20.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 5691-17 Dom 2019-05-20.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 7768-11 Dom 2013-06-04.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 2116-14 Dom 2014-06-12.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 6860-14 Dom 2015-09-21.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 3837-12 Dom 2012-10-30.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 424-14 Dom 2015-11-16.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 5901-14 Dom 2014-12-22.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 4839-13 Dom 2014-11-21.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 3456-17 Dom 2017-09-01.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 1958-09 Dom 2009-09-04.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 6652-11 Dom 2012-11-01.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 4204-17 Dom 2018-08-21.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 6867-11 Dom 2012-03-27.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 1199-16 Dom 2017-06-14.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 607-16 Deldom 2016-10-26.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 3249-19 Dom 2020-11-26.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 1325-18 Dom 2018-11-07.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 3775-10 Dom 2011-09-01.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 4085-12 Dom 2013-02-19.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 3952-18 Dom 2020-02-10.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 619-17 Dom 2017-12-22.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 4932-17 Dom 2018-12-11.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 1663-10 Dom 2011-04-06.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 2701-10 Dom 2010-12-02.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 1495-09 Dom 2011-11-25.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 1581-19 Dom 2020-04-02.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 1072-13 Dom 2013-10-25.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 3183-17 Dom 2019-06-10.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 503-18 Dom 2019-01-23.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 2408-17 Dom 2018-10-22.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 1603-18 Dom 2019-05-24.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 5906-09 Dom 2011-11-21.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 2712-20 Dom 2020-11-23.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 966-12 Dom 2012-05-02.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 5149-20 Dom 2021-06-16.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 5474-20 Dom 2021-01-28.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 3931-14 Dom 2015-07-13.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 1345-09 Dom 2011-09-27.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 4491-19 Dom 2020-06-23.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 5097-20 Dom 2021-06-01.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 1182-07 Dom 2009-11-25.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 1195-10 Dom 2010-06-04.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 2704-18 Dom 2019-11-22.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 2513-14 Dom 2015-06-05.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 4594-18 Dom 2020-04-23.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 4963-08 Dom 2009-03-26.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 2806-19 Dom 2021-01-27.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 610-16 Dom 2017-05-05.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 3834-19 Dom 2020-09-02.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 1429-15 Dom 2015-11-05.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 2937-09 Dom 2010-09-13.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 2410-18 Dom 2019-07-16.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 215-14 Dom 2014-06-26.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 2613-18 Dom 2019-02-25.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 5761-16 Dom 2017-05-04.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 3955-12 Dom 2012-10-19.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 1290-16 Dom 2017-03-27.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 1432-12 Dom 2014-06-17.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 2448-14 Dom 2015-09-08.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 6470-18 Dom 2020-02-05.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 3820-12 Dom 2013-03-28.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 3655-13 Dom 2014-04-03.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 1900-16 Dom 2017-07-07.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 4386-14 Dom 2016-04-11.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 5236-10 Dom 2012-02-28.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 1956-18 Dom 2019-03-08.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 3987-14 Dom 2015-02-18.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 6548-19 Dom 2021-03-11.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 1056-09 Dom 2009-11-19.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 5389-18 Dom 2018-12-14.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 447-11 Dom 2011-04-29.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 2692-15 Dom 2016-03-14.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 3095-18 Dom 2019-12-03.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 4323-19 Dom 2020-03-09.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 3364-14 Dom 2015-06-29.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 1341-10 Dom 2011-08-22.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 3565-13 Dom 2014-11-17.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 798-16 Dom 2017-02-21.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 5467-17 Dom 2019-05-07.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 4866-16 Deldom 2017-11-23.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 6131-19 Dom 2020-11-30.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 5515-17 Dom 2018-07-30.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 2870-12 Dom 2014-05-16.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 194-13 Dom 2014-05-23.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 4914-17 Dom 2018-07-10.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 3183-11 Deldom 2011-11-04.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 4588-17 Dom 2018-06-11.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 4120-09 Dom 2011-02-18.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 2416-09 Dom 2010-04-19.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 2720-10 Dom 2011-11-11.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 2904-14 Dom 2015-02-11.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 1911-18 Dom 2018-07-11.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 1388-08 Dom 2010-02-10.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 1997-08 Dom 2009-06-01.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 2907-07 Dom 2009-06-02.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 4116-18 Dom 2018-12-28.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 4145-18 Dom 2019-05-07.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 3777-11 Dom 2012-09-21.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 1931-19 Dom 2019-07-02.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 1624-16 Dom 2016-06-28.pdf",	"P:/2020/14/Tingsrätter/Ystads/Domar/all_cases/Ystads TR T 2416-17 Dom 2018-12-17.pdf",	"P:/2020/14/Tingsrätter/Ystads/Domar/all_cases/Ystads TR T 1967-18 Dom 2020-04-14.pdf",	"P:/2020/14/Tingsrätter/Ystads/Domar/all_cases/Ystads TR T 2147-17 Dom 2018-02-23.pdf",	"P:/2020/14/Tingsrätter/Ystads/Domar/all_cases/Ystads TR T 2415-16 Dom 2017-08-25.pdf",	"P:/2020/14/Tingsrätter/Ystads/Domar/all_cases/Skåne HR Ö 703-20 Slutligt beslut (ej särskilt uppsatt) 2020-03-23.pdf",	"P:/2020/14/Tingsrätter/Ystads/Domar/all_cases/Ystads TR T 1415-18 Dom 2018-12-27.pdf",	"P:/2020/14/Tingsrätter/Ystads/Domar/all_cases/Ystads TR T 2620-18 Dom 2019-05-27.pdf",	"P:/2020/14/Tingsrätter/Ångermanlands/Domar/all_cases/Ångermanlands TR T 841-16 Dom 2017-01-26.pdf",	"P:/2020/14/Tingsrätter/Ångermanlands/Domar/all_cases/Ångermanlands TR T 282-21 Dom 2021-03-30.pdf",	"P:/2020/14/Tingsrätter/Ångermanlands/Domar/all_cases/Ångermanlands TR T 1447-16 Dom 2017-12-27.pdf",	"P:/2020/14/Tingsrätter/Ångermanlands/Domar/all_cases/Ångermanlands TR T 1390-19 Dom 2019-07-15.pdf",	"P:/2020/14/Tingsrätter/Ångermanlands/Domar/all_cases/Ångermanlands TR T 2059-16 Dom 2017-09-06.pdf",	"P:/2020/14/Tingsrätter/Ångermanlands/Domar/all_cases/Ångermanlands TR T 2227-16 Dom 2016-12-16.pdf",	"P:/2020/14/Tingsrätter/Ångermanlands/Domar/all_cases/Ångermanlands TR T 1521-15 Dom 2016-09-22.pdf",	"P:/2020/14/Tingsrätter/Ångermanlands/Domar/all_cases/Ångermanlands TR T 2622-17 Dom 2018-12-17.pdf",	"P:/2020/14/Tingsrätter/Ångermanlands/Domar/all_cases/Ångermanlands TR T 2613-17 Dom 2019-03-12.pdf",	"P:/2020/14/Tingsrätter/Ångermanlands/Domar/all_cases/Ångermanlands TR T 450-19 Dom 2020-02-20.pdf",	"P:/2020/14/Tingsrätter/Ångermanlands/Domar/all_cases/Ångermanlands TR T 2101-18 Dom 2019-01-22.pdf",	"P:/2020/14/Tingsrätter/Ångermanlands/Domar/all_cases/Ångermanlands TR T 628-18 Dom 2018-07-02.pdf",	"P:/2020/14/Tingsrätter/Ångermanlands/Domar/all_cases/Ångermanlands TR T 1145-15 Dom 2016-06-02.pdf",	"P:/2020/14/Tingsrätter/Ångermanlands/Domar/all_cases/Ångermanlands TR T 263-17 Dom 2017-09-19.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 5898-10 Dom 2011-09-09.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 3963-13 Dom 2015-03-05.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2240-02.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/517-02.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 5731-12 Dom 2013-08-28.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 1158-14 Dom 2015-06-30.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 5378-18 Dom 2019-04-17.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/3787-04.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 2170-15 Dom 2015-06-29.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 5386-14 Dom 2015-05-20.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 1842-18 Dom 2020-03-24.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 5082-07 Dom 2008-08-27.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/3099-06.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1300-02.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 6883-10 Dom 2012-03-21.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2806-05.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 2924-18 Dom 2019-06-17.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2891-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1412-06.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2625-06.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2672-98.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 4922-18 Dom 2019-10-15.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 423-18 Dom 2018-07-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 1730-14 Dom 2015-01-09.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 2682-15 Dom 2016-11-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 4891-13 Dom 2013-12-19.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 4520-12 Dom 2014-01-29.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 1049-16 Dom 2017-05-05.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 6006-13 Dom 2015-03-06.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 1729-09 Dom 2011-05-20.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 285-09 Dom 2009-02-26.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 2162-16 Dom 2017-01-24.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/52-07.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 3249-19 Dom 2020-01-23.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/60-97.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 3676-13 Dom 2014-11-28.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2227-97.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 1340-18 Dom 2018-05-08.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/874-98.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 3885-16 Dom 2017-06-12.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/795-08.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 2895-15 Dom 2016-05-18.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1394-97.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 5883-16 Dom 2018-04-13.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 394-16 Dom 2016-08-17.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 3741-19 Dom 2020-05-07.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 660-08 Dom 2009-05-13.pdf",	"P:/2020/14/Tingsrätter/Östersunds/Domar/all_cases/Östersunds TR T 873-13 Dom 2014-12-09.pdf",	"P:/2020/14/Tingsrätter/Östersunds/Domar/all_cases/Östersunds TR T 2117-14 Dom 2014-10-07.pdf",	"P:/2020/14/Tingsrätter/Östersunds/Domar/all_cases/Östersunds TR T 2244-18 Dom 2019-04-03.pdf",	"P:/2020/14/Tingsrätter/Östersunds/Domar/all_cases/Östersunds TR T 3191-10 Dom 2011-05-30.pdf",	"P:/2020/14/Tingsrätter/Östersunds/Domar/all_cases/Östersunds TR T 463-12 Dom 2012-12-11.pdf",	"P:/2020/14/Tingsrätter/Östersunds/Domar/all_cases/Östersunds TR T 1174-09 Dom 2010-09-15.pdf",	"P:/2020/14/Tingsrätter/Östersunds/Domar/all_cases/Östersunds TR T 2622-17 Dom 2018-03-20.pdf",	"P:/2020/14/Tingsrätter/Östersunds/Domar/all_cases/Östersunds TR T 1135-18 Dom 2018-05-22.pdf",	"P:/2020/14/Tingsrätter/Östersunds/Domar/all_cases/Östersunds TR T 1153-11 Dom 2012-12-13.pdf",	"P:/2020/14/Tingsrätter/Östersunds/Domar/all_cases/Östersunds TR T 1096-09 Dom 2010-03-02.pdf",	"P:/2020/14/Tingsrätter/Östersunds/Domar/all_cases/Östersunds TR T 1416-09 Dom 2010-03-24.pdf",	"P:/2020/14/Tingsrätter/Östersunds/Domar/all_cases/Östersunds TR T 2816-17 Dom 2017-12-07.pdf",	"P:/2020/14/Tingsrätter/Östersunds/Domar/all_cases/Östersunds TR T 2348-09 Dom 2010-06-28.pdf"]
    
noCopy = 0                 
for file in unread_files:
    try:
        shutil.copy(file,pdf_dir)
    except:
        noCopy += 1
        continue

print(noCopy)
"""

#Read in PDFs
pdf_files = glob.glob("%s/*.pdf" % pdf_dir)
print(pdf_files)

#Initialize variables
noOfFiles = 0
noUnreadable = 0
countries = ['saknas', 'okänd', 'adress', 'u.s.a.', 'u.s.a', 'usa', 'afghanistan', 'albanien', 'algeriet', 'andorra', 'angola', 'antigua och barbuda', 'argentina', 'armenien', 'australien', 'azerbajdzjan', 'bahamas', 'bahrain', 'bangladesh', 'barbados', 'belgien', 'belize', 'benin', 'bhutan', 'bolivia', 'bosnien och hercegovina', 'botswana', 'brasilien', 'brunei', 'bulgarien', 'burkina faso', 'burundi', 'centralafrikanska republiken', 'chile', 'colombia', 'costa rica', 'cypern', 'danmark', 'djibouti', 'dominica', 'dominikanska republiken', 'ecuador', 'egypten', 'ekvatorialguinea', 'elfenbenskusten', 'el salvador', 'eritrea', 'estland', 'etiopien', 'fiji', 'filippinerna', 'finland', 'frankrike', 'förenade arabemiraten', 'gabon', 'gambia', 'georgien', 'ghana', 'grekland', 'grenada', 'guatemala', 'guinea', 'guinea-bissau', 'guyana', 'haiti', 'honduras', 'indien', 'indonesien', 'irak', 'iran', 'irland', 'island', 'israel', 'italien', 'jamaica', 'japan', 'jemen', 'jordanien', 'kambodja', 'kamerun', 'kanada', 'kap verde', 'kazakstan', 'kenya', 'kina', 'kirgizistan', 'kiribati', 'komorerna', 'kongo-brazzaville', 'kongo-kinshasa', 'kroatien', 'kuba', 'kuwait', 'laos', 'lesotho', 'lettland', 'libanon', 'liberia', 'libyen', 'liechtenstein', 'litauen', 'luxemburg', 'madagaskar', 'malawi', 'malaysia', 'maldiverna', 'mali', 'malta', 'marocko', 'marshallöarna', 'mauretanien', 'mauritius', 'mexiko', 'mikronesiska federationen', 'moçambique', 'moldavien', 'monaco', 'montenegro', 'mongoliet', 'myanmar', 'namibia', 'nauru', 'nederländerna', 'nepal', 'nicaragua', 'niger', 'nigeria', 'nordkorea', 'nordmakedonien', 'norge', 'nya zeeland', 'oman', 'pakistan', 'palau', 'panama', 'papua nya guinea', 'paraguay', 'peru', 'polen', 'portugal', 'qatar', 'rumänien', 'rwanda', 'ryssland', 'saint kitts och nevis', 'saint lucia', 'saint vincent och grenadinerna', 'salo-monöarna', 'samoa', 'san marino', 'são tomé och príncipe', 'saudiarabien', 'schweiz', 'senegal', 'seychellerna', 'serbien', 'sierra leone', 'singapore', 'slovakien', 'slovenien', 'somalia', 'spanien', 'sri lanka', 'storbritannien', 'sudan', 'surinam', 'sverige', 'swaziland', 'sydafrika', 'sydkorea', 'sydsudan', 'syrien', 'tadzjikistan', 'tanzania', 'tchad', 'thailand', 'tjeckien', 'togo', 'tonga', 'trinidad och tobago', 'tunisien', 'turkiet', 'turkmenistan', 'tuvalu', 'tyskland', 'uganda', 'ukraina', 'ungern', 'uruguay', 'usa', 'uzbekistan', 'vanuatu', 'vatikanstaten', 'venezuela', 'vietnam', 'vitryssland', 'zambia', 'zimbabwe', 'österrike', 'östtimor']

emptyString = ''
                
#Define search terms
svarandeSearch = ' Svarande|SVARANDE|Motpart|MOTPART|SVARANDE och KÄRANDE '
defendantNationality = 'medborgare i (\w+ )'
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
    '1' : '((\w+ ){1})T\s*I\s*N\s*G\s*S\s*R\s*Ä\s*T\s*T',
    '2' : '((\w+){1})[.]?.?T\s*I\s*N\s*G\s*S\s*R\s*A\s*T\s*T'
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
separationKey = ['separera', 'relationen tog slut', 'förhållandet tog slut', 'relationen avslutades', 'förhållandet avslutades', 'skildes', 'skiljas', 'skiljer' ]
rejectKey = ['avskriv',' ogilla','lämnas utan bifall','avslå',' inte ','skrivs', 'kvarstå']  
excludePhysical = ['jämna' , 'växelvisa', 'skyddat']

#Intiialize lists and dictionary to fill
data = {'Barn':[], 'Målnr':[], 'Tingsrätt':[], 'År avslutat':[], 'Deldom':[], 'Kärande förälder':[], 'Svarande förälder':[], 'Kär advokat':[], 'Sv advokat':[], 'Sv utlandet':[], 'Sv okontaktbar':[], 'Utfall':[], 'Umgänge':[], 'Stadigvarande boende':[], 'Underhåll':[], 'Enl överenskommelse':[], 'Snabbupplysning':[], 'Samarbetssamtal':[], 'Utredning':[], 'Huvudförhandling':[], 'SeparationYear': [], 'Domare':[], "Page Count": [], 'Rättelse': [], "File Path": []}

#Loop over files and extract data
for file in pdf_files:
    print(" ")
    print("Currently reading:")
    print(file)
        
    pageCount = 0
    rsrcmgr = PDFResourceManager()
    retstr = io.StringIO()
    codec = 'utf-8-sig'
    laparams = LAParams(line_margin=3)
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
    firstPageFormatted = (pages_text_formatted[0]).split("il")
    
    if "Rättelse" in firstPage:
        fullTextOG = ''.join(pages_text[1:])
        firstPage = ''.join(pages_text[1])
        fullTextFormatted = ''.join(pages_text_formatted[1:])
        dummyRat = 1
    else:
        fullTextOG = ''.join(pages_text)
        fullTextFormatted = '.'.join(pages_text_formatted)
        dummyRat = 0

    splitTextOG = re.split('_{10,40}', fullTextOG)
        
    noOfFiles += 1                                                      
    headerOG = re.split('_{10,40}', firstPage)[0]   
    header = headerOG.lower()    
    appendixPage = [i for i, item in enumerate(pages_text) if re.search(appendixStart, item)]
    if not appendixPage:
        appendixPageNo = len(pages_text)
    else:
        appendixPageNo = appendixPage[0]
    if appendixPageNo >3:
        lastPageFormatted = '.'.join((pages_text_formatted[appendixPageNo-1]).split(".")) + '.'.join((pages_text_formatted[appendixPageNo-2]).split(".")) + '.'.join((pages_text_formatted[appendixPageNo-3]).split("."))
        lastPageFormatted3 = (pages_text_formatted[appendixPageNo-1]).split(".")
        lastPageOG = pages_text[appendixPageNo-1]
        lastPage = lastPageOG.lower()  
    else:
        lastPageFormatted = '.'.join((pages_text_formatted[appendixPageNo-1]).split("."))
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
        rulingOnlyOG1 = re.split('\n\s*\n\s*[A-ZÅÄÖ.,]{4,}\s{0,1}[A-ZÅÄÖ.,]{0,4}\s*\n', rulingStringFormatted)[0]
        rulingOnlyOG = ' '.join(''.join(rulingOnlyOG1).split())
        rulingOnly = rulingOnlyOG.lower()
    except AttributeError:
        rulingOnlyOG = ' '.join(''.join(re.split('(YRKANDEN)', rulingStringFormatted)[0].lower() ).split())
        rulingOnly = rulingOnlyOG.lower()
    
    print('FULL TEXT: ' + fullText)
        
    #Get plaintiff and defendant passage
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
            try:
                svarandeStringOG = re.split("Hustrun|HUSTRUN", headerOG)[1] 
                kärandeStringOG = re.split('Mannen|MANNEN', (re.split("Hustrun|HUSTRUN", headerOG)[0]))[1]
            except IndexError:
                svarandeStringOG = re.split("Mannen|MANNEN", headerOG)[1] 
                kärandeStringOG = re.split('Hustrun|HUSTRUN', (re.split("Mannen|MANNEN", headerOG)[0]))[1]
    svarandeString = svarandeStringOG.lower()
    kärandeString = kärandeStringOG.lower()
    
    #District Court
    courtName = searchLoop(courtSearch, fullTextOG, 0)
    courtNameList = courtName.split()
    
    #Get DOMSKÄL part
    print('DOMSKAL: ')
    domStart = re.split('DOMSKÄL', rulingString)[1]
    domList = domStart.split()
    domClean1 = list(filter(lambda i: i != 'TINGSRÄTT', domList))
    domClean = list(filter(lambda i: i != 'DOM', domClean1))        
    domskalOG = re.split('[A-ZÅÄÖ.,]{3,}\s{0,1}[A-ZÅÄÖ.,]{3,}', domClean)[0]
    domskal = domskalOG.lower()
    print(domskal)

    #List of children's numbers
    childNoRes = []
    childNo = set(re.findall('\d{6,8}\s?-\s?\d{4}', rulingOnly))   
    for i in childNo:
        mistakeChilNos = searchKey("\A197|\A198|\A5|\A6|\A7|\A8", i, 0)
        if mistakeChilNos is None: # child ID should not start with 197 or 198, or 5,6,7,8  
            childNoRes.append(i)  
    if not childNoRes:
        childNoRes = ['not found']
    
    #Loop to create dictionary with one row per child
    for i in childNoRes:   
                        
        #Get child's name
        childNameKey = ('([A-ZÅÐÄÖÉÜÆØÞ][A-ZÅÐÄÖÉÜÆØÞa-zåäïüóöéæøßþîčćžđšžůúýëçâêè]+)[,]?\s*[(]?\s*' + i )
        childNameFirst = searchKey(childNameKey, rulingOnlyOG, 1)
        if childNameFirst is not None:
            childKey1 = re.compile("(([A-ZÅÐÄÖÉÜÆØÞ][a-zåäïüóöéæøßþîčćžđšžůúýëçâêèA-ZÅÐÄÖÉÜÆØÞ-]+\s*){1,4})"+ childNameFirst + '\s*[,]?[(]?\s*' + i)
            childNameFull = childKey1.search(rulingOnlyOG)
            if childNameFull is not None:
                childNameFull = childNameFull.group(1)
                childKey2 = re.compile('[A-ZÅÐÄÖÉÜÆØÞ][A-ZÅÐÄÖÉÜÆØÞ]+')
                childNameCaps = childKey2.search(childNameFull)
                if childNameCaps is None:
                    childKey3 = re.compile('[A-ZÅÐÄÖÉÜÆØÞ][a-zåäïüóöéæøßþîčćžđšžůúýëçâêè]+')
                    childNameFirst = childKey3.search(childNameFull).group(0).lower()
                else:
                    childNameFirst = childNameCaps.group(0).lower()
        else:
            childName = 'not found'
            childNameFirst = 'not found'
        childNameFirst = childNameFirst.lower()
        
        #Case ID for child i
        caseNo = ''.join((searchKey(searchCaseNo, header, 2)).split())

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
        elif svNameFirst in findTwoWords('inte', 'sverige', fullText):
            dummyAbroad = 1
        elif 'utomlands' in findTwoWords('befinn', 'sig', fullText):
            dummyAbroad = 1 #didnt include svNameFirst because sv might be referred to by Han
        elif searchKey(defendantNationality, svarandeString, 0) and 'sverige' not in searchKey(defendantNationality, svarandeString, 0):
            dummyAbroad = 1
        else:
            dummyAbroad = 0
        
        #Defendant unreachable
        print(findSentence('förordnat god man', fullText))
        if 'okontaktbar' in fullText or 'förordnat god man' in fullText and svNameFirst in findSentence('förordnat god man', fullText):
            print('unreach1')
            dummyUnreach = 1
        elif svNameFirst in findTwoWords('inte', 'kontakt', fullText):
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

        #Year of Separation of Unmarried Parents
        for term in separationKey:
            if term in fullText:
                dummySeparate = searchKey('(\d\d\d\d)', findSentence(term, fullText), 0)
                break
            else:
                dummySeparate = '-'
                continue
        
        #Outcome
        try:
            findGemensam = findFirstOccur(searchKey('(gemensam)[^m]',rulingOnly,1), rulingOnly)
        except TypeError:
            findGemensam = findFirstOccur('gemen-', rulingOnly)
        vardnInGemensam = 'vårdn' in findGemensam
        findEnsam = findFirstOccur('ensam', rulingOnly)
        findVardn = findFirstOccur('vårdn', rulingOnly)
        findEnsamVardn = findTwoWordsFirstOccur('ensam','vårdn',rulingOnly)
        findGemensamVardn = findTwoWordsFirstOccur('gemensam', 'vårdn', rulingOnly)
        findVardnBarn = findTwoWordsFirstOccur('barn', 'vårdn', rulingOnly)
        transferToDef = 'till ' + svNameFirst
        transferToPlaint = 'till ' + plaintNameFirst
        vardnInRuling = 'vårdn' in rulingOnly
        findChild = findFirstOccur(i, rulingOnly)
        
        print("RULING ONLY: "+rulingOnly)       
                
        if 'vård' not in rulingOnly: #reduced to vård to account for vårdanden
            #No custody ruling in this court record
            print("out1a")
            dummyOut = 0
        elif vardnInRuling and 'påminn' in findVardn:
            print("out1c")
            dummyOut = 0
        elif vardnInRuling and 'erinra' in findVardn:
            print("out1d")
            dummyOut = 0
        elif vardnInRuling and 'upply' in findVardn:
            print("out1e")
            dummyOut = 0
        elif 'vård' not in findChild:
            print('out1f')
            dummyOut = 0
        elif i in findVardn and 'ska' in findGemensam and 'om' in findGemensam and vardnInGemensam and not any([x in findGemensamVardn for x in rejectKey]):
            dummyOut = 1
            print("out2")
        elif i in findVardn and 'vårdn' in rulingOnly and 'fortsätt' in findGemensam and 'ska' in findGemensam and not any([x in findGemensamVardn for x in rejectKey]):
            dummyOut = 1
            print("out3")
        elif i in findVardn and vardnInGemensam and findTwoWords('alltjämt','ska' , findGemensam) and not any([x in findGemensamVardn for x in rejectKey]):
            dummyOut = 1
            print("out4")
        elif i in findVardn and vardnInGemensam and findTwoWords('alltjämt', 'är', rulingOnly) and not any([x in findGemensamVardn for x in rejectKey]):
            dummyOut = 1
            print("out5")
        elif i in findVardn and vardnInGemensam and 'skall tillkomma' in rulingOnly and not any([x in findGemensamVardn for x in rejectKey]): 
            dummyOut = 1
            print("out6")
        elif i in findVardn and vardnInGemensam and 'anförtror' in findVardn and not any([x in findGemensamVardn for x in rejectKey]): 
            dummyOut = 1
            print("out6")    
        elif i in findVardn and 'vårdn' in findEnsam and plaintNameFirst in findEnsam and 'utan' not in findEnsamVardn and not any([x in findEnsamVardn for x in rejectKey]):
            dummyOut = 2
            print("out7")
        elif i in findVardn and 'vårdn' in findEnsam and svNameFirst in findEnsam and 'utan' not in findEnsamVardn and not any([x in findEnsamVardn for x in rejectKey]):
            dummyOut = 3
            print("out8")
        elif i in findVardn and 'ensam' in rulingOnly and vardnInRuling and plaintNameFirst in findVardn and not any([x in findEnsamVardn for x in rejectKey]):
            dummyOut = 2
            print("out10a")
        elif i in findVardn and plaintNameFirst in findEnsam and not any([x in findEnsamVardn for x in rejectKey]):
            dummyOut = 2
            print("out10")
        elif i in findVardn and 'ensam' in rulingOnly and vardnInRuling and  svNameFirst in findVardn and not any([x in findEnsamVardn for x in rejectKey]):
            dummyOut = 3
            print("out11a")    
        elif i in findVardn and svNameFirst in findEnsam and not any([x in findEnsamVardn for x in rejectKey]):
            dummyOut = 3
            print("out11")
        elif i in findVardn and 'vårdn' in findTwoWords('över','flytt',rulingOnly) and transferToDef in findVardn and not any([x in findVardn for x in rejectKey]):
            dummyOut = 3
            print("out12")
        elif i in findVardn and 'vårdn' in findTwoWords('över','flytt',rulingOnly) and transferToPlaint in findVardn and not any([x in findVardn for x in rejectKey]):
            dummyOut = 2
            print("out13")
        elif i in findVardn and vardnInRuling and 'tillerkänn' in findVardn and svNameFirst in findSentence('tillerkänn', rulingOnly) and not any([x in findVardn for x in rejectKey]):
            dummyOut = 3
            print("out14")
        elif i in findVardn and vardnInRuling and 'tillerkänn' in findVardn and plaintNameFirst in findSentence('tillerkänn', rulingOnly) and not any([x in findVardn for x in rejectKey]):
            dummyOut = 2
            print("out15")
        elif i in findVardn and vardnInRuling and 'anförtro' in findVardn and svNameFirst in findSentence('anförtro', rulingOnly) and not any([x in findVardn for x in rejectKey]):
            dummyOut = 3
            print("out14")
        elif i in findVardn and vardnInRuling and 'anförtro' in findVardn and plaintNameFirst in findSentence('anförtro', rulingOnly) and not any([x in findVardn for x in rejectKey]):
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
            findUmg = findTwoWordsFirstOccur(key, childNameFirst, rulingOnly)
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
                break
            elif term in findTwoWords('boende', plaintNameFirst, rulingOnly) and not any([x in findTwoWords('boende', plaintNameFirst, rulingOnly) for x in excludePhysical]):
                dummyPhys = 1
                print("phsical custody 2")
                break
            elif term in findTwoWords('boende', svNameFirst, rulingOnly) and not any([x in findTwoWords('boende', svNameFirst, rulingOnly) for x in excludePhysical]):
                dummyPhys = 2
                print("phsical custody 3")
                break
            elif term in findTwoWords('bo tillsammans', plaintNameFirst, rulingOnly) and not any([x in findTwoWords('bo tillsammans', plaintNameFirst, rulingOnly) for x in excludePhysical]):
                dummyPhys = 1
                print("phsical custody 4")
                break
            elif term in findTwoWords('bo tillsammans', svNameFirst, rulingOnly) and not any([x in findTwoWords('bo tillsammans', svNameFirst, rulingOnly) for x in excludePhysical]):
                dummyPhys = 2
                print("phsical custody 5")
                break
            elif term in findThreeWords('ska','bo', plaintNameFirst, rulingOnly) and not any([x in findThreeWords('ska','bo', plaintNameFirst, rulingOnly) for x in excludePhysical]):
                dummyPhys = 1  
                print("phsical custody 6")
                break
            elif term in findThreeWords('ska','bo', svNameFirst, rulingOnly) and not any([x in findThreeWords('ska','bo', svNameFirst, rulingOnly) for x in excludePhysical]):
                dummyPhys = 2
                print("phsical custody 7")
                break
            elif findTwoWords('bilaga', 'sidorna', rulingOnly):
                dummyPhys = 999
                print("phsical custody 8")
                break
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
            findAgree1 = findThreeWords(svNameFirst,'yrkande', termAgree, fullText)
            if svNameFirst in findTwoWords('yrkande', termAgree, fullText) and not any([x in findAgree1 for x in agreementHelper]):
                print('agree1: ' + termAgree)
                dummyAgree = 1
                dummyUnreach = 0
                break
            for termHelper in agreementAdd:
                findAgree2 = findTwoWords(termAgree, termHelper, fullText)
                if findAgree2 is not emptyString and not any([x in findAgree2 for x in agreementHelper]):
                    print('agree2: '+ termAgree + termHelper)
                    dummyAgree = 1
                    dummyUnreach = 0
                    break
                else:
                    dummyAgree = 0
                    continue
            else: 
                print('in else for agree')
                continue
            break
        print(dummyAgree)
        if dummyAgree == 0 and 'förlikning' in findTwoWords('framgå', 'träff', fullText):
            print('agree4')
            dummyAgree = 1
            dummyUnreach = 0
        if dummyOut == 0:
            dummyAgree = 0
           
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
            dummyInfo = termLoopFirstOccur(fastInfoKey, fullText)
            print("snabbupply 4" )
              
        #Cooperation talks
        dummyCoop = termLoopFirstOccur(corpTalksKey, fullText)
           
        #Investigation
        dummyInvest = termLoop(investigationKey, fullText)
        if dummyInvest == 0:
            if 'ingsrätt' in findSentence(' utredning', fullTextOG): #search for tingsratt or Tingsratt in fullTextOG to not get the TINGSRATT from header
                print('invest1')
                dummyInvest = 1
            elif any([x in findSentence(' utredning', fullText) for x in socialOffice]):
                print('invest2')
                dummyInvest = 1
            elif "11 kap. 1 § socialtjänstlagen" in fullText:
                print('invest3')
                dummyInvest = 1
            else:
                print('invest4')
                for term in investigationHelper:
                    if term in findSentence(' utredning', fullText):
                        print('invest5')
                        dummyInvest = 1
                        break
                    else:
                        print('invest6')
                        dummyInvest = 0
                        continue
        
        #Main hearing 
        for term in mainHearingKey:
            print(findSentence(term, fullText))
            if findSentence(term, fullText) and 'utan' not in findSentence(term, fullText) and ' ingen' not in findSentence(term, fullText):
                print('mainhear1: ' + term)
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
        
        print('Family names:')
        print("Child first name: "+childNameFirst)
        print("Sv first name: "+svNameFirst)
        print("Plaint first name: "+plaintNameFirst)
        print('sv adress: '+ cityString)
        
        #Fill dataframe with search results
        i = ''.join(i.split())
        data['Barn'].append(i)
        data["File Path"].append(file)
        data["Page Count"].append(pageCount)
        data['Rättelse'].append(dummyRat)
        data['Målnr'].append(caseNo)
        data['Domare'].append(judgeName.lower())
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
        data['SeparationYear'].append(dummySeparate)
        data['Huvudförhandling'].append(dummyMainHear)
    
#Dataframe created from dictionary
df = pd.DataFrame(data)
with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    print(df)

print("---Saved as CSV---")
print('Unreadable: ')
print(noUnreadable)




