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
sample_files = ["P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 1036-13 Aktbil 70, DOM - Henrik Andersson, Martin.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 1070-12 Ak-tbil 91, DOM - Kristin Jansson, Peter M.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 109-13 Aktbil 108, DOM - Maria Rocha, Dennis Wenn.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 1099-12 Ak-tbil 83, DOM - Kjell Ångman, Terese Ols.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 1132-13 Ak-tbil 54, DOM - Faycel Bahri, Annica Nor.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 1188-13 Ak-tbil 36, DOM - Dennis Olsson, Ida Sahli.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 1251-13 Ak-tbil 19, DOM - Jessica Rosenberg, Bleda.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 1323-12 Ak-tbil 69, DOM - Ingemar Jårsand, Maria V.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 1338-14 Ak-tbil 13, DOM - Fredrik Andersson, Izabe.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 1417-13 Ak-tbil 13, DOM - Thomas Fråberg, Annika B.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 1626-13 Ak-tbil 45, DOM - Martin Pettersson, Karin.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 1746-13 Ak-tbil 29, DOM - Renåe Cummins Karlsson, .pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 1760-13 Ak-tbil 15, DOM - Anneli Eriksson, Daniel .pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 281-13 Aktbil 44, DOM - Stefan Lilja, Carina Vuk.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 297-14 Aktbil 23, DOM - Scott Lamb, Vicky-Lee Mc.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 303-13 Aktbil 117, DOM - Cissi Andersen, Kenny Jo.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 455-14 Aktbil 27, DOM - Peter Andreasson, Helen .pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 464-13 Aktbil 40, DOM - Christian Broberg, Heidi.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 472-13 Aktbil 37, DOM - Golam Golbarg, Sara Ahma.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 547-14 Aktbil 15, DOM - Fredrik Lindån, Linda Ol.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 582-14 Aktbil 52, DOM - Helån Hågberg, Mahmut Or.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 586-13 Aktbil 38, DOM - Cecilia Augustsson, Jean.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 65-13 Aktbil 20, DOM - Fredrik Arvidsson, Veron.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 783-13 Aktbil 46, DOM - Ylva Stenberg, Mikael Tå.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 899-12 Aktbil 99, DOM - Caroline Ekfeldt, Jari E.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 145-10 Dom 2010-05-17.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 1729-18 Dagboksblad 2021-08-13.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 178-15 Dom 2016-11-01.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 1850-10 Dagboksblad 2021-07-02.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 884-12 Aktbil 6, DOMEN finns i T 883-12, ska va.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 10964-15 Dom 2016-03-01.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 1830-11 Dom 2011-07-25.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 1906-17 Dom 2017-10-18.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 3389-13 Dom 2014-01-30.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 3415-13 Dom 2013-11-05.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 345-17 Slut-ligt beslut (ej särskilt uppsatt) 2017-03-31.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 4758-17 Dom 2018-10-18.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 6450-14 Dom 2014-11-20.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 6452-14 Dom 2014-11-20.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 8077-13 Dom 2015-03-11.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 9225-14 Dom 2015-07-31.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 926-16 Dom 2016-03-24.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 9474-12 Dom 2013-09-26.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 9482-10 Dom 2011-06-28.pdf",	"P:/2020/14/Tingsrätter/Attunda/Domar/all_cases/Attunda TR T 9522-17 Dom 2018-02-19.pdf",	"P:/2020/14/Tingsrätter/Blekinge/Domar/all_cases/Blekinge TR T 2598-20 Aktbil 18, DOM - Samia Al Masri, Tarek El.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 1387-08 2008-11-27 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 2852-16 2017-04-26 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 2913-07 2008-09-29 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 3233-07 2009-09-17 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 3252-07 2009-03-02 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 3511-09 2011-02-28 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 379-09 2009-10-08 Dom.pdf",	"P:/2020/14/Tingsrätter/Borås/Domar/all_cases/Borås tingsrätt T 561-11 2011-09-16 Dom.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 1085-11 Dom 2013-02-19.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 144-16 Dagboksblad 2021-06-17.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 2020-11 Dom 2012-03-22.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 238-08 Dom 2008-11-12.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 2716-08 Dom 2009-07-31.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 2854-10 Dagboksblad 2021-06-22.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 40-10 Dom 2010-02-08.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 824-14 Dagboksblad 2021-06-22.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 958-15 Dagboksblad 2021-06-22.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 1633-08 Dom 2009-03-06.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 1916-12 Dagboksblad 2021-09-20.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 195-10 Dom 2011-11-24.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 2578-09 Dom 2009-12-09.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 259-11 Dom 2011-02-25.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 2618-19 Dom 2020-03-02.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 2809-09 Dom 2009-12-02.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 553-09 Dom 2009-10-12.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 850-18 Dom 2018-11-14.pdf",	"P:/2020/14/Tingsrätter/Eskilstuna/Domar/all_cases/Eskilstuna TR T 940-17 Dom 2017-05-18.pdf",	"P:/2020/14/Tingsrätter/Gotlands/Domar/all_cases/Gotlands TR T 1076-16 Dom 2017-01-05.pdf",	"P:/2020/14/Tingsrätter/Gotlands/Domar/all_cases/Gotlands TR T 838-15 Dom 2017-04-11.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 1011-11 Aktbil 19, DOM - Zamzam Ahmad, Hamid Joha.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 1025-10 Aktbil 37, DOM - Jimmy Siekas, Tina Vaara.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 1030-12 Aktbil 43, DOM - Anna Maria Karlsson, Ing.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 106-16 Ak-tbil 9, DOM - Anders Isaksson, Åsa Isa.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 1088-11 Aktbil 36, DOM - Anna Maria Karlsson, Ing.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 116-19 Ak-tbil 105, DOM - Sandra Fryc, Fredrik Kar.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 122-14 Ak-tbil 42, DOM - Filip Henriksson, Annika.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 126-10 Ak-tbil 99, DOM - Tobias Hågberg, Chrisse .pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 133-10 Ak-tbil 44, DOM - Andreas Berggren, Erica .pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 146-10 Ak-tbil 143, DOM - Dharma Johansson, Robert.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 15-19 Aktbil 108, DOM - Johan Falk, Amanda Jonss.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 152-16 Ak-tbil 41, DOM - Sekretess MI, Mattias Ve.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 154-10 Ak-tbil 38, DOM - Ellen Marit Labba, Ander.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 154-20 Ak-tbil 71, DOM - Idah Gårdemalm, Emil Lin.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 178-19 Ak-tbil 16, DOM - Soonthorn Panun, Oatchar.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 183-15 Ak-tbil 108, DOM - Eric Anderson, Anisa Ser.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 185-13 Ak-tbil 58, DOM - Sanna Eklåv, Robert Lust.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 187-17 Ak-tbil 21, DOM - Khatiashvili Ketevan, Ti.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 190-18 Ak-tbil 51, DOM - Ida Arlastig, Johan Joha.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 194-12 Ak-tbil 36, DOM - Liliana Ramirez Cardenas.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 195-16 Ak-tbil 8, DOM - Philip Håggrot, Angelica.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 201-10 Ak-tbil 74, DOM - Anna Inga, Magnus Anders.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 210-11 Ak-tbil 12, DOM - Socialnåmnden Gållivare .pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 213-16 Ak-tbil 56, DOM - Jessica Båckstråm, Andre.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 214-09 Ak-tbil 83, DOM - Elle Suvi, Johan Furbeck.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 217-11 Ak-tbil 85, DOM - Emma Oskarsson Måki, Iva.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 219-18 Ak-tbil 141, DOM - Anton Holmqvist, Michell.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 219-19 Ak-tbil 107, DOM - Connie Sturk, Leif Sturk.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 238-19 Ak-tbil 40, DOM - Marlene Harrietsdotter N.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 242-18 Ak-tbil 20, DOM - Taha Mustafa, Roqia Zang.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 249-12 Ak-tbil 83, DOM - Arthur Hanssen, Mona Van.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 257-13 Ak-tbil 54, DOM - Anna Jenssen, Fredrik Bj.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 261-15 Ak-tbil 82, DOM - Ida Arlastig, Johan Arla.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 263-15 Ak-tbil 24, DOM - Ali Alp, Carola Nilsson.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 264-15 Ak-tbil 36, DOM - Kamal Ahmed, Silje Wesse.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 264-17 Ak-tbil 125, DOM - Emma Kyrå Åakmak, Murat .pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 285-16 Ak-tbil 8, DOM - Eija Kivilahti, Marko Ki.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 288-11 Ak-tbil 15, DOM - Socialnåmnden Jokkmokks .pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 289-15 Ak-tbil 39, DOM - Mubariz Musayev, Dilara .pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 291-12 Ak-tbil 67, DOM - Haikel Arfaoui, Anna-Kar.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 298-16 Ak-tbil 17, DOM - Mats Holmqvist, Helena K.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 299-10 Ak-tbil 76, DOM - Kristina Mattsson, Mikae.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 302-09 Ak-tbil 28, DOM - Mats Olsson, Towe Christ.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 307-17 Ak-tbil 32, DOM - Rosaline Joseph, Victor .pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 307-18 Ak-tbil 16, DOM - Alida Mugisha, Fabrice N.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 324-13 Ak-tbil 11, DOM - Åsa Pejok, Bjårn Springa.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 327-18 Ak-tbil 119, DOM - Micael Esko, Linnåa Stål.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 343-11 Ak-tbil 31, DOM - Peter Nilsson, Ann-Sofi .pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 346-11 Ak-tbil 42, DOM - Kajsa Backefalk Lundberg.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 352-16 Ak-tbil 17, DOM - Tony Strande, Kisasa Sha.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 357-18 Ak-tbil 70, DOM - Johanna Mangi Sundgren, .pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 363-11 Ak-tbil 46, DOM - Mikael Kalla, Mariann Vå.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 364-09 Ak-tbil 164, DOM - Åsa Isaksson Hedlund, An.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 376-10 Ak-tbil 19, DOM - Gunilla Winman, Hans Win.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 39-13 Aktbil 87, DOM - Lisa Eklund, Per-Erik Ke.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 397-12 Ak-tbil 60, DOM - Peter Zaff, Satu-Påivi Z.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 398-11 Ak-tbil 110, DOM - Corrine Winchester, Toby.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 402-17 Ak-tbil 19, DOM - Nathalie Låfdahl, Christ.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 422-11 Ak-tbil 36, DOM - Lizette Anveblad, Mattia.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 424-09 Ak-tbil 58, DOM - Hannele Våhå, Håkan Niem.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 436-16 Ak-tbil 18, DOM - Tesfay Mehari, Nigisti T.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 440-12 Ak-tbil 68, DOM - Maria Duvenås, Håkan Ylv.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 446-18 Ak-tbil 68, DOM - Ziad Fawal, Dima Hamwi K.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 450-16 Ak-tbil 25, DOM - Khalid Mohammed Alqahtan.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 462-15 Ak-tbil 33, DOM - Magnus Andersson, Anna I.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 462-19 Ak-tbil 105, DOM - Lars Johansson, Ogulniya.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 488-11 Ak-tbil 12, DOM - Susannå Olofsson, Lotfi .pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 493-14 Ak-tbil 25, DOM - Anucha Khunawatthananan,.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 497-18 Ak-tbil 242, DOM - Lars-Henrik Henriksson K.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 499-17 Ak-tbil 28, DOM - Ann-Sofi Bjårnfot, Danie.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 5-12 Aktbil 21, DOM - Annette Johansson Vaara,.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 508-17 Ak-tbil 92, DOM - Mohammed Khaje, Sharifa .pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 510-17 Ak-tbil 115, DOM - Mariam Anveri, Milad Qaz.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 516-15 Ak-tbil 16, DOM - Mats Christoffersson, An.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 521-18 Ak-tbil 9, DOM - Bayram Dagli, Lisa Dyran.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 527-17 Ak-tbil 24, DOM - Mwadi Kapi, Luganywa Luf.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 529-14 Ak-tbil 31, DOM - Elina Bodån, Tobias Naar.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 530-11 Ak-tbil 25, DOM - Kanokkon Phatprem, Boonr.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 534-12 Ak-tbil 36, DOM - Nicklas Hedlund, Isabel .pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 536-12 Ak-tbil 7, DOM - Sekretess ML, Sekretess .pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 541-10 Ak-tbil 18, DOM - Hossein Alizadeh, Hamyde.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 546-11 Ak-tbil 24, DOM - Sandra De Oliveira, Sand.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 549-18 Ak-tbil 46, DOM - Johanna Auoja, Patrik Th.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 55-20 Aktbil 26, DOM - Cecilia Norgren, Kent No.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 552-14 Ak-tbil 56, DOM - Robert Persson, Annette .pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 556-11 Ak-tbil 9, DOM - Socialnåmnden Kiruna kom.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 557-10 Ak-tbil 22, DOM - Socialnåmnden Gållivare .pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 558-10 Ak-tbil 22, DOM - Socialnåmnden Gållivare .pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 558-16 Ak-tbil 42, DOM - Zbigniew Nalepka, Christ.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 567-16 Ak-tbil 49, DOM - Hannele Iso-Kamula, Ande.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 569-14 Ak-tbil 17, DOM - Anette Nygren, Niklas Ol.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 57-17 Aktbil 30, DOM - Philip Håggrot, Angelica.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 576-16 Ak-tbil 17, DOM - Nour-Eddine Boufarra, Ya.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 587-15 Ak-tbil 27, DOM - Jan-Erik Engman, Maud Is.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 600-13 Ak-tbil 69, DOM - Christoffer Karlsson, Id.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 601-11 Ak-tbil 28, DOM - Sara Lantto, Daniel Gust.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 603-19 Ak-tbil 65, DOM - Anne-Marie Sandberg, Mat.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 605-17 Ak-tbil 21, DOM - Marianne Boman, Joakim S.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 609-08 Ak-tbil 62, DOM - Pia Yu Nordgren, Yankai .pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 614-09 Ak-tbil 44, DOM - Fredrik Rosenberg, Sakka.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 616-12 Ak-tbil 31, DOM - Sandra Kuhmunen, John Ed.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 620-16 Ak-tbil 60, DOM - Martin Markusbacka, Marl.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 627-15 Ak-tbil 35, DOM - Jonas Engstråm, Susanne .pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 627-18 Ak-tbil 57, DOM - Arthur Arnautovic, Louis.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 628-19 Ak-tbil 215, DOM - Kabber Abdullah, Rakel B.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 634-17 Ak-tbil 9, DOM - Fanus Menghistu, Habtema.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 640-19 Ak-tbil 97, DOM - Merimkul Forssån, Mikael.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 641-19 Ak-tbil 61, DOM - Andrea Andersson, Martin.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 65-19 Aktbil 123, DOM - Kate James, Christer Kos.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 663-18 Ak-tbil 19, DOM - Yordanos Berhegebreslasi.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 670-15 Ak-tbil 8, DOM - Almaz Gebreyesus, Berhan.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 671-17 Ak-tbil 45, DOM - Robert Johansson, Marian.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 680-12 Ak-tbil 24, DOM - Fawzia Hassan Omar, Faty.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 685-20 Ak-tbil 20, DOM - Yosief Gebremariam, Gene.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 687-20 Ak-tbil 52, DOM - Gabriella Andersson Ryyt.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 689-20 Ak-tbil 36, DOM - Johnny Bjårnstråm Widmar.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 698-12 Ak-tbil 29, DOM - Roger Nystråm, Pia Sotka.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 699-09 Ak-tbil 58, DOM - Pia Sotka, Roger Nystråm.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 700-09 Ak-tbil 46, DOM - Jårgen Frisk, Malin Aspl.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 717-11 Ak-tbil 7, DOM - Socialnåmnden Gållivare .pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 719-18 Ak-tbil 20, DOM - Niaz Mohammad Mohammad K.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 725-14 Ak-tbil 14, DOM - Ann Uhland, Michael Uhla.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 726-15 Ak-tbil 24, DOM - Elkim Engman, Andreas Kr.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 728-10 Ak-tbil 79, DOM - Hannington Mwagalanyi, A.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 733-09 Ak-tbil 19, DOM - Hans Winman, Gunilla Win.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 735-13 Ak-tbil 31, DOM - Wanida Khachonphet, Jan .pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 744-09 Ak-tbil 9, DOM - Marina Hedlund, Mikael H.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 745-17 Ak-tbil 48, DOM - Mathias Persson, Olga Pe.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 75-15 Aktbil 67, DOM - Philip Håggrot, Angelica.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 752-10 Ak-tbil 28, DOM - Yvonne Karlsson, Anders .pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 754-16 Ak-tbil 39, DOM - Klas Enoch, Malin Keskit.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 766-12 Ak-tbil 14, DOM - Annika Keskitalo, Lars-E.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 77-17 Aktbil 43, DOM - David Gustafsson, Anna S.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 770-16 Ak-tbil 48, DOM - Mattias Wallmark, Vanja .pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 792-16 Ak-tbil 56, DOM - Patrik Malmstråm, Katari.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 793-19 Ak-tbil 56, DOM - Mary Ayoti, Armel Nguepi.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 794-09 Ak-tbil 60, DOM - +?rjan Kattilavaara, Lena.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 800-16 Ak-tbil 15, DOM - Catherine Lantz, Stig Gå.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 809-15 Ak-tbil 44, DOM - Marina Shkleda, Mika Vik.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 811-09 Ak-tbil 38, DOM - Veronica Fors, Sven-Olof.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 817-14 Ak-tbil 6, DOM - Saba Solomon Gezahegn, T.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 820-14 Ak-tbil 20, DOM - Evelina Emmot, Joel Niem.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 822-10 Ak-tbil 38, DOM - Roland Apelqvist , Maria.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 829-17 Ak-tbil 44, DOM - Jonny Henriksson, My Wid.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 829-18 Ak-tbil 109, DOM - Cecilia Asplund, Gåran L.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 835-19 Ak-tbil 16, DOM - Khadije Khan Mohammadi, .pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 836-17 Ak-tbil 10, DOM - Gholam Hussein (Hasan), .pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 84-15 Aktbil 12, DOM - Carina Henriksson, Toivo.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 870-14 Ak-tbil 12, DOM - Azim Mohammadi, Ayda Rez.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 888-09 Ak-tbil 39, DOM - Anna Maria Karlsson, Ing.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 896-10 Ak-tbil 90, DOM - Anna-Mari Nilsson, Ola-P.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 900-17 Ak-tbil 113, DOM - Rasmus Bjårling, Donna N.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 919-17 Ak-tbil 22, DOM - Jill Andersson, Per-Fred.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 920-17 Ak-tbil 47, DOM - Mats Olsson, Theres +?lun.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 921-14 Ak-tbil 85, DOM - Hannele Iso-Kamula, Ande.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 940-10 Ak-tbil 38, DOM - Karin Apelqvist, Tomas A.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 949-10 Ak-tbil 113,    UTGPÅR.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 951-13 Ak-tbil 10, DOM - Hannele Iso-Kamula, Ande.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 978-11 Ak-tbil 90, DOM - Anders Magnusson, Åsa Wa.pdf",	"P:/2020/14/Tingsrätter/Gällivare/Domar/all_cases/Gållivare TR T 993-11 Ak-tbil 24, DOM - Chongkon Laoket, Samrit .pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210927_140113.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_101951.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_102117.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_102659.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_113557.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_114002.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_114252.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_114327.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_114756.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_115057.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_115504.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_115545.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_115610.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_115638.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_115711.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_115740.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_120035.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_120046.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_120102.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_120114.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_120124.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_120307.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_120415.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_120537.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_120647.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_120904.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR B 1917-19 Dom 2020-01-16.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 1185-10 Dom 2011-01-11.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 1302-17 Aktbil 74.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 1924-15 Dom 2015-08-24.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 429-10 Dom 2010-04-13.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/Gävle TR T 52-11 Dom 2011-11-17.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 1105-17 Dom 2017-02-22.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 1332-17 Dom 2017-03-29.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 14904-15 Dom 2016-01-19.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 15141-16 Dom 2017-02-08.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 18705-20 Dom 2021-06-23.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 18877-20 Dom 2021-01-18.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 19256-19 Dom 2020-03-02.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 1965-18 Dom 2018-02-28.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 2360-21 Dom 2021-06-09.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 296-17 Dom 2017-03-03.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 3130-17 Dom 2017-04-21.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 4338-18 Dom 2019-05-13.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 5924-19 Dom 2019-05-16.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 7317-17 Dom 2017-07-24.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 7806-19 Dom 2020-02-12.pdf",	"P:/2020/14/Tingsrätter/Göteborgs/Domar/all_cases/Göteborgs TR T 972-17 Dom 2018-04-20.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 1001-07 Dom 2008-08-08.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 1363-08 Dom 2008-07-22.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 1382-18 Dom 2019-04-30.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 2008-20 Dom 2020-09-07.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 2140-07 Dom 2008-09-29.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 2144-08 Dom 2009-06-18.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 2306-19 Dom 2019-12-19.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 2342-08 Dom 2009-05-14.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 2620-17 Dom 2018-10-15.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 2649-17 Dom 2018-10-15.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 3061-18 Dom 2018-12-28.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 380-13 Dom 2014-03-05.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 433-09 Dom 2009-05-20.pdf",	"P:/2020/14/Tingsrätter/Halmstads/Domar/all_cases/Halmstads TR T 704-18 Dom 2018-10-02.pdf",	"P:/2020/14/Tingsrätter/Haparanda/Domar/all_cases/Haparanda TR T 67-17 Dom 2018-04-27.pdf",	"P:/2020/14/Tingsrätter/Hässleholms/Domar/all_cases/Hässleholms TR T 1360-11 Dom 2012-10-05.pdf",	"P:/2020/14/Tingsrätter/Hässleholms/Domar/all_cases/Hässleholms TR T 522-16 Dom 2017-06-28.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 1458-17 Dom 2018-10-22.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 2172-11 Dom 2012-06-11.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 3249-13 Dom 2013-11-05.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 3593-19 Dom 2020-09-08.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 3813-16 Dom 2017-02-02.pdf",	"P:/2020/14/Tingsrätter/Kalmar/Domar/all_cases/Kalmar TR T 3943-20 Dagboksblad 2021-09-30.pdf",	"P:/2020/14/Tingsrätter/Linköpings/Domar/all_cases/Linköpings TR T 2731-16 Dom 2017-12-21.pdf",	"P:/2020/14/Tingsrätter/Linköpings/Domar/all_cases/Linköpings TR T 78-20 Dom 2020-10-09.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 1201-08 Dom 2008-11-21.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 1312-12 Dom 2012-08-23.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 1317-12 Dom 2012-08-16.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 147-07 Dom 2008-11-10.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 2858-15 Dom 2016-08-12.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 2956-07 Dom 2008-12-12.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 3012-07 Dom 2008-10-01.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 3341-11 Dom 2012-08-16.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 366-17 Dom 2017-03-07.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 385-16 Dom 2017-02-21.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 610-17 Dagboksblad 2021-10-14.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 734-15 Dom 2015-07-07.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 911-08 Dom 2009-10-20.pdf",	"P:/2020/14/Tingsrätter/Luleå/Domar/all_cases/Luleå TR T 995-16 Dom 2016-09-13.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 1270-15 2016-09-22 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 2737-16 2017-10-06 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 3326-12 2012-09-14 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 4281-11 2012-02-28 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 5581-10 2013-03-18 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 5859-14 2015-03-06 Dom.pdf",	"P:/2020/14/Tingsrätter/Lunds/Domar/all_cases/Lunds tingsrätt T 6465-10 2011-06-16 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 10985-17 2018-10-24 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 11233-12 2012-11-27 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 1167-11 2012-02-20 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 1818-15 2015-11-04 Deldom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 3402-12 2015-11-16 Dom.pdf",	"P:/2020/14/Tingsrätter/Malmö/Domar/all_cases/Malmö tingsrätt T 4406-11 2011-05-20 Dom.pdf",	"P:/2020/14/Tingsrätter/Mora/Domar/all_cases/Mora TR T 1617-07 Dom 2008-11-25.pdf",	"P:/2020/14/Tingsrätter/Mora/Domar/all_cases/Mora TR T 639-10 Aktbil 13, DOM - Charlotte Morravej, Nade.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/1064-06.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/1197-06.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/1294-08 Dom 2009-01-09.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/1680-06 Dom 2009-03-19.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/2023-10 Dom 2011-08-09.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/2125-06.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/2211-06.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/2343-08 Dom 2009-04-06.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/5203-07.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/549-10 Dom 2011-02-15.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/dagbok 1106-09.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/dagbok 3232-09.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/dagboken 1142-15.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/dagboken 2064-14.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/dagboken 277-17.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/dagboken 6359-19.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 1061-09 Dom 2010-03-26.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 1755-11 Dom 2011-06-22.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 1949-10 Dom 2011-01-05.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 2023-10 Dom 2011-08-09.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 2451-14 Dom 2014-06-04.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 3188-07 Dom 2009-03-24.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 3431-07 Dom 2008-12-02.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 3537-15 Dom 2016-10-28.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 3583-08 Dom 2008-11-28.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 3628-07 Dom 2008-10-14.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 3672-17 Dom 2017-07-26.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 4098-09 Dom 2010-02-16.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 4121-08 Dom 2010-04-06.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 4250-08 Dom 2009-02-26.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 4410-08 Dom 2009-01-19.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 469-14 Dom 2014-02-19.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 5257-09 Dom 2010-09-09.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 549-10 Dom 2011-02-15.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 5672-09 Dom 2011-02-28.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 5690-10 Dom 2011-02-14.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/Nacka TR T 6187-17 Dom 2018-06-07.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/T 2385-08 Dom 2009-06-22.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 1223-09 Deldom 2009-11-17.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 1853-09 Dom 2010-06-23.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 1918-14 Dom 2014-12-01.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 2213-09 Dom 2011-02-08.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 2287-17 Dom 2018-11-30.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 2510-08 Dom 2009-02-24.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 2730-10 Dom 2010-10-25.pdf",	"P:/2020/14/Tingsrätter/Norrköpings/Domar/all_cases/Norrköpings TR T 746-13 Dagboksblad 2021-08-09.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 1214-15 Dom 2016-03-02.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 1896-13 Dom 2014-09-24.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 2040-13 Deldom 2014-06-25.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 2040-13 Dom 2015-01-12.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 224-14 Dom 2014-03-11.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 2785-14 Dom 2014-12-22.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 3004-18 Aktbil 76, Dom-Svea hovrätt.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 3663-19 Dom 2020-06-30.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 4198-19 Dom 2020-06-01.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 855-18 Aktbil 111, DOM - Banafshe Behrooz, Kamran.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 864-09 Dom 2009-06-15.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 902-09 Dom 2009-10-14.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/Skaraborgs TR T 1079-12 Dom 2013-06-03.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/Skaraborgs TR T 2288-18 Dom 2019-07-25.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/Skaraborgs TR T 3154-15 Dom 2017-09-25.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/Skaraborgs TR T 662-09 Deldom 2009-09-24.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/Skaraborgs TR T 888-14 Dom 2015-08-26.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/T 1269-06.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/T 1311-02.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/T 1403-01.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/T 145-04.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/T 175-03.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/T 184-02.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/T 190-04.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/T 273-02.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/T 356-00.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/T 470-01.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/T 577-99.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/T 631-00.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/T 666-98.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/T 764-01.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/T 854-99.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/T 855-00.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/T 933-99.pdf",	"P:/2020/14/Tingsrätter/Skaraborgs/Domar/all_cases/T 959-03.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 1049-17 Dom 2018-10-22.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 1074-09 Deldom 2010-02-16.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 1088-09 Dom 2010-04-14.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 1111-18 Dom 2019-10-30.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 1128-12 Dom 2014-03-14.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 1167-13 Dom 2014-12-15.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 118-11 Dom 2012-01-11.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 1350-12 Dom 2014-01-29.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 137-16 Dom 2017-04-20.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 1494-18 Dom 2019-05-06.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 153-10 Dom 2011-02-15.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 1818-11 Dom 2012-01-09.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 1996-10 Dom 2012-02-14.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 2029-09 Dom 2011-02-17.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 212-12 Dom 2012-03-20.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 216-12 Dom 2013-06-28.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 245-15 Dom 2016-09-07.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 288-20 Dom 2020-10-21.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 292-17 Dom 2018-05-18.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 334-18 Dom 2018-11-22.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 341-10 Dom 2011-08-31.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 366-08 Dom 2009-01-21.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 401-14 Dom 2015-02-04.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 440-12 Dom 2013-06-24.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 480-17 Dom 2018-05-22.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 51-19 Dom 2020-02-03.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 54-14 Dom 2015-01-09.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 57-12 Dom 2012-10-18.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 589-18 Dom 2018-12-21.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 629-17 Dom 2018-04-30.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 63-16 Dom 2017-02-17.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 641-11 Dom 2012-05-10.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 646-16 Dom 2017-06-08.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 740-15 Dom 2016-10-28.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 744-16 Dom 2018-06-25.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 842-15 Dom 2017-04-05.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 870-12 Dom 2014-03-10.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 876-12 Dom 2013-10-23.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 911-16 Dom 2017-05-16.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 966-14 Dom 2016-07-04.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skelleftea? TR T 973-17 Deldom 2017-11-02.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 1121-08 Dom 2009-08-06.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 1283-08 Dom 2009-10-05.pdf",	"P:/2020/14/Tingsrätter/Skellefteå/Domar/all_cases/Skellefteå TR T 1760-06 Dom 2008-12-03.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/1921-07.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/2233-07.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/4494-07.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 1025-20 Dom 2020-11-27.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 135-12 Dom 2012-07-20.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 1581-08 Deldom 2008-10-28.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 1581-08 Dom 2009-09-02.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 1768-17 Dom 2017-04-20.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 1784-09 Dom 2009-07-09.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 1962-07 Dom 2008-08-15.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 2066-08 Dom 2008-12-12.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 2335-08 Dom 2008-12-18.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 2438-08 Dom 2008-09-16.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 2866-15 Dom 2016-11-15.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 3341-13 Dom 2013-12-20.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 3989-17 Dom 2018-04-24.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 4071-09 Dom 2011-04-07.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 4247-20 Dom 2020-09-23.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 4446-15 Dom 2016-02-08.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 4844-16 Dom 2016-06-29.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 4914-11 Dom 2014-09-22.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 5222-08 Dom 2009-06-17.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 5642-08 Dom 2008-11-11.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 5884-17 Dom 2018-03-16.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 595-13 Dom 2014-10-08.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 5969-16 Dom 2016-10-05.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 6196-10 Dom 2012-05-14.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 6378-07 Dom 2008-08-27.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 6454-08 Dom 2008-12-16.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 6914-17 Dom 2017-12-05.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 7318-17 Dom 2018-04-03.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 7359-19 Dom 2019-11-08.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 7388-12 Dom 2012-11-23.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 7576-18 Dom 2019-09-05.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 7606-07 Deldom 2008-08-21.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 7672-17 Dom 2018-04-04.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 7978-14 Dom 2015-10-16.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 7985-08 Dom 2010-09-21.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 8243-07 Dom 2008-10-20.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 8287-07 Dom 2009-04-20.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 855-12 Dom 2012-03-07.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 868-18 Dom 2018-09-10.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 8800-07 Dom 2008-10-29.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 8948-07 Dom 2008-11-06.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 9017-10 Dom 2012-05-11.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/Solna TR T 9051-16 Dom 2017-03-15.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 12443-17 Dom 2019-03-25.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 15641-15 Dom 2016-06-28.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 2219-16 Dom 2016-05-10.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 3146-18 Dom 2018-12-07.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 3408-16 Dom 2017-02-07.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 3728-17 Dom 2017-05-10.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 4714-15 Dom 2016-09-16.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 5245-17 Dom 2017-07-12.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 5504-15 Dom 2016-06-17.pdf",	"P:/2020/14/Tingsrätter/Stockholms/Domar/all_cases/Stockholms TR T 9918-14 Dom 2016-04-08.pdf",	"P:/2020/14/Tingsrätter/Sundsvalls/Domar/all_cases/Sundsvalls TR T 1217-15 Dom 2016-04-19.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 1407-19 Dom 2020-01-17.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 198-19 Dom 2019-12-17.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 2190-16 Dom 2016-10-13.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 2832-16 Dom 2016-12-07.pdf",	"P:/2020/14/Tingsrätter/Södertälje/Domar/all_cases/Södertälje TR T 370-19 Dom 2020-01-10.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 10317-09 2009-09-23 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 1164-13 2013-02-13 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 1188-09 2009-03-30 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 12571-15 2016-11-08 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 12576-18 2019-01-25 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 13011-09 2009-12-23 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 13051-16 2017-09-13 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 13062-18 2019-10-31 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 13070-11 2012-12-07 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 13129-15 2016-06-29 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 13319-11 2011-11-11 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 13405-18 2019-05-29 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 13698-09 2009-12-16 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 13711-15 2017-09-20 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 14116-08 2008-12-18 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 14385-09 2010-01-22 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 14610-14 2015-09-14 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 1471-10 2010-03-04 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 14922-11 2012-04-10 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 15100-15 2017-01-18 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 15210-14 2015-05-04 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 15524-16 2017-07-11 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 15530-14 2015-09-09 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 16336-12 2013-05-02 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 1644-09 2009-04-29 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 16841-15 2016-11-07 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 1839-14 2014-06-03 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 2048-16 2016-12-05 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 2051-17 2017-06-12 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 3026-19 2019-10-01 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 335-17 2018-04-06 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 4253-17 2017-04-18 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 4392-14 2016-03-21 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 5566-19 2019-11-22 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 6130-13 2013-11-20 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 6145-07 2008-08-21 Deldom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 6639-11 2011-06-27 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 7436-15 2017-04-06 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 7781-15 2015-11-18 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 8267-09 2010-07-12 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 8347-13 2014-02-04 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 8395-09 2009-07-30 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 8850-17 2018-02-09 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 8898-08 2009-03-30 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 8910-13 2014-09-26 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 9036-09 2010-04-19 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 9067-11 2011-09-21 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 9174-11 2013-01-09 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 9191-09 2010-12-14 Dom.pdf",	"P:/2020/14/Tingsrätter/Södertörns/Domar/all_cases/Södertörns tingsrätt T 9770-07 2008-03-28 Deldom.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1019-18 Aktbil 18, DOM - Joakim Hallbåck Svensson.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1065-13 Aktbil 16, DOM - Louise Gåransson Stenman.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1134-17 Aktbil 92, DOM - Gåran Maaklint, Johanna .pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1150-14 Aktbil 15, DOM - exp kårande samt svarand.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1163-15 Aktbil 59, DOM - exp parter omb, soc.fårv.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1275-15 Aktbil 55, DOM; exp. till Bjårn Stråmsted.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1321-09 Aktbil 96, DOM - Sara Skåld, Tobias Åman.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1368-19 Aktbil 17, DOM - Susanne Neu, Jonas Nyrån.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 141-10 Aktbil 74, DOM - Mats Ros, Ditte Kristens.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1440-10 Aktbil 10, DOM - Socialnåmnden Uddevalla .pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1502-11 Aktbil 41, DOM - Iza Larsson, Peter Molin.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1509-15 Aktbil 25, DOM - Camilla Hågberg, Magnus .pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1545-12 Aktbil 65, DOM - Michael Åsenfors, Anna-L.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1546-12 Aktbil 42, DOM - exp till Marita Månsson,.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1588-13 Aktbil 36, DOM - stadfåst fårlikning, exp.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1589-14 Aktbil 70, DOM - Marcus Thårnqvist, Perni.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1589-15 Aktbil 55, DOM -  exp till Maria Jånegren.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1597-10 Aktbil 12, DOM - Vånersborgs kommun, Thom.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1599-10 Aktbil 16, DOM - Susanne Sårqvist, Peter .pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1601-19 Aktbil 30, DOM - Niclas Båckstråm, Evelin.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1647-11 Aktbil 38, DOM - Malin Gaardån, Armand Ki.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1679-19 Aktbil 29, DOM - Malin Tång, Robert Tång .pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 177-12 Aktbil 38, DOM - Rebecca Bårjesson, Danie.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 179-11 Aktbil 17, DOM - Syrenå Olsson, Peter Sjå.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1797-11 Aktbil 32, DOM - Håkan Morån, Britt Johan.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1912-11 Aktbil 44, DOM -  exp till Adv.Åsa Hadart.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1920-12 Aktbil 23, DOM - Marta Simalienå, Linas S.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1926-12 Aktbil 50, DOM - Håkan Olsson, Jennifer L.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1957-19 Aktbil 37, DOM - Isabelle Hjårn, Samim Sa.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1962-13 Aktbil 162, DOM - Oliver Robinson, Åse Ste.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1997-15 Aktbil 27, DOM - Anton Carnerå, Cindie Na.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 1998-13 Aktbil 115, DOM - Katarina Clendinning, Ki.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2057-12 Aktbil 51, DOM - Camilla Hågberg, Mikael .pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 207-14 Aktbil 17, DOM - Bjårn Bjåle, Tsion Gebre.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2079-09 Aktbil 33, DOM - Patricia Rosån, Patrik B.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2341-13 Aktbil 37, DOM - My Purje, Christian Tårn.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2369-18 Aktbil 56, DOM - Gåran Maaklint, Johanna .pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2514-14 Aktbil 24, DOM - Sandra Eriksson, Andrå R.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2575-19 Aktbil 10, DOM - Stefan Karldån, Stefani .pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2577-19 Aktbil 7, DOM - Johan Karldån, Stefani N.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2619-08 Aktbil 39, DOM - Rolf-Kåre Lossius, Anett.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 265-09 Aktbil 9, DOM - Cathrine Sylvån, Benny S.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2679-09 Aktbil 23, DOM - Jårgen Moberg, Johanna M.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2715-19 Aktbil 81, DOM - Sven Ove Jårgensen, Hild.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2746-14 Aktbil 18, DOM - Magnus Normån, omb, Mari.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2792-17 Aktbil 82, DOM - Tommy Levin, Veronica Lå.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2816-19 Dagboksblad 2021-11-04.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2824-18 Aktbil 58, DOM - Carolina Lånngren, Peter.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2851-15 Aktbil 51, DOM - Conny Gårdenskog, Kristi.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2865-15 Aktbil 27, DOM - exp Andråas Johansson sa.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 287-12 Aktbil 48, DOM - Eva-Marie Ståhl, Robert .pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2897-10 Aktbil 15, DOM - Stadsdelsnåmnden Lundby .pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2944-12 Aktbil 44, DOM - Marcus Bergstråm, Emma W.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2964-19 Dagboksblad 2021-11-04.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2966-17 Aktbil 75, DOM - Emilia Andråasson, Eddie.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 3018-18 Aktbil 40, DOM - Jimmy Falk, Angelica Kår.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 3047-12 Aktbil 34, DOM; exp. till kårande ombud, .pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 3071-10 Aktbil 44, DOM - Håkan Morån, Britt Morån.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 3089-13 Aktbil 23, DOM - Sekretess, Kanan Ismayil.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 3341-09 Aktbil 20, DOM - Irene Bergstråm, Håkan O.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 3425-18 Aktbil 37, DOM - Jonas Daneborn Stålhamma.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 3507-10 Aktbil 18, DOM - Jenny Norån, Johan Velin.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 3567-13 Aktbil 18, DOM - Thomas Nyckelgård, Maria.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 3610-11 Aktbil 40, DOM - Theresia Willån, Mikael .pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 3814-09 Aktbil 99, DOM - Erica Strand, Kennet Åke.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 3875-08 Aktbil 32, DOM - Linda Stråm, Andreas Hel.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 3918-09 Aktbil 71, DOM - Åsa Hallqvist, Markus Ha.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 393-16 Aktbil 24, DOM -  Jenni Hammarbåck, Marcu.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 3985-11 Aktbil 75, DOM - Karin Wånseth Karlqvist,.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 4058-11 Aktbil 39, DOM - Exp Kenny Wallstråm, omb.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 4194-10 Aktbil 42, DOM - exp till Noåmi Publik, R.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 4386-11 Aktbil 31, DOM - Marcus Bergstråm, Emma W.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 449-13 Aktbil 21, DOM; exp. till kårandeombudet,.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 462-10 Aktbil 62, DOM - Anna Båe, Teuvo Hållback.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 4621-10 Aktbil 89, DOM - Cathrine Sylvån, Benny S.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 4668-10 Aktbil 97, DOM - exp till Adv.Robert Mjås.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 4693-10 Aktbil 31, DOM - Johanna Kårrdin, Jackie .pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 4810-09 Aktbil 77, DOM - Jårgen Petersson, Victor.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 4948-09 Aktbil 32, DOM - Jens Åkesson, Ulrika Kar.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 5150-09 Aktbil 25, DOM - Socialnåmnden i Munkedal.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 5433-10 Aktbil 35, DOM - Åsa Busk, Magnus Busk.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 572-14 Aktbil 68, DOM - Natalie Jensen, Andråas .pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 600-18 Aktbil 74, DOM - Martin Loveåver, Josefin.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 627-14 Aktbil 23, DOM - Andreas Hildån, Naomi Ma.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 659-13 Aktbil 32, DOM - Diala Farah, Roni Abou S.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 659-15 Aktbil 21, DOM -  exp till Helena Tjårneb.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 661-19 Aktbil 51, DOM om vårdnad och umgånge.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 701-18 Aktbil 35, DOM - Aina Jensen, Andråas Joh.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 724-09 Aktbil 62, DOM - Jenny Eriksson Såfstråm,.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 741-12 Aktbil 56, DOM; exp. till Gåran Persson, .pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 758-15 Aktbil 7, DOM -  exp Markus Edstråm, Per.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 799-20 Aktbil 60, DOM - Linnåa Falck, Mikael Mår.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 830-15 Aktbil 14, DOM - exp till Karin Lundstråm.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 847-13 Aktbil 61, DOM - Hans Fredån, Siw Knag.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 852-15 Aktbil 26, DOM - Elin Andersson, Jårgen W.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 865-12 Aktbil 78, DOM - Jenny Fjållhede, Marcus .pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 913-13 Aktbil 21, DOM - exp till Helåne Andersso.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 930-19 Aktbil 49, DOM om ensam vårdnad får kåran.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 934-16 Aktbil 25, DOM -  exp kåranden omb, Johan.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 978-20 Aktbil 68, DOM - Pasi Sievånen, Ulrika Si.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1010-00.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1028-97.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 104-03.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1051-02.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1055-03.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1068-03.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1068-98.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1110-98.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1119-98.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1184-00.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 119-98.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1260-98.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1301-03.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1313-02.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1362-98.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1394-97.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1406-98.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1422-99.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1459-97.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1492-02.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1495-97.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 151-98.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1530-99.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1566-00.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1582-01.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1605-98.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1630-99.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1639-98.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1649-97.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 169-03.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 17-98.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1700-99.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1787-99.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1806-97 o 1666-98.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1824-01.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1921-99.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1940-98.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1975-99.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 1981-98.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 201-02.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 2077-00.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 2094-98 o 355-99.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 2153-00.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 2181-98.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 222-05.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 224-99.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 2447-02.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 254-03.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 269-98.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 312-01.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 318-01.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 32-01.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 33-02.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 374-99.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 405-03.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 476-03.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 493-02.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 577-99.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 597-95.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 597-98.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 604-00.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 625-03 o 764-03.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 668-98.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 680-01.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 711-02.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 837-98.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 849-98.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 871-00.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 894-98.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 974-00.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1027-12 Deldom 2013-04-22.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1057-10 Dom 2011-05-13.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1073-12 Dom 2012-09-19.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1086-11 Dom 2012-01-13.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1175-15 Dom 2016-01-25.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1199-15 Dom 2015-12-22.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1253-15 Dom 2016-07-06.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1259-11 Dom 2011-12-29.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1301-12 Dom 2013-03-26.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1316-14 Dom 2015-02-10.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1343-11 Deldom 2012-08-21.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1343-11 Dom 2013-04-23.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1369-15 Deldom 2016-03-15.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1369-15 Dom 2016-05-26.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1374-13 Dom 2014-06-24.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1394-13 Dom 2014-07-24.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1418-11 Dom 2012-03-20.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1447-10 Dom 2011-05-17.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1531-10 Dom 2011-04-12.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 158-12 Dom 2012-12-21.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1589-12 Dom 2014-05-13.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1597-16 Dom 2016-11-30.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 16-13 Dom 2014-01-23.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1684-13 Dom 2014-03-03.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1762-12 Dom 2014-05-27.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1775-11 Dom 2011-12-06.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1820-11 Dom 2012-02-27.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1825-13 Dom 2014-01-24.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1867-11 Dom 2012-07-03.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1897-06 Deldom 2008-05-14.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1940-11 Dom 2012-08-21.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 1972-11 Dom 2012-05-30.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2012-10 Dom 2011-11-02.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2079-15 Dom 2016-05-11.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2085-11 Dom 2012-04-17.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2123-15 Dom 2015-12-17.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2128-15 Dom 2016-09-23.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2186-14 Dom 2015-07-02.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2186-15 Dom 2016-04-20.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2197-15 Dom 2015-11-16.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2205-10 Dom 2011-06-13.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2205-12 Dom 2013-07-04.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2211-15 Dom 2016-06-01.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 223-14 Dom 2015-01-08.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2243-11 Dom 2012-05-30.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2263-13 Dom 2014-10-28.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2277-13 Dom 2014-10-16.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2285-10 Dom 2011-04-13.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2299-15 Dom 2016-12-13.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2383-11 Dom 2012-04-25.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2396-11 Dom 2012-01-30.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2397-10 Dom 2011-11-11.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2401-10 Dom 2011-07-26.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2443-12 Dom 2013-01-28.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 249-07 Dom 2008-12-17.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 249-16 Dom 2016-10-21.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2533-13 Dom 2014-04-25.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 257-12 Dom 2013-09-16.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2595-13 Dom 2014-03-11.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2609-18 Dom 2019-04-08.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2623-13 Dom 2014-01-29.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2694-18 Dom 2019-03-19.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2715-14 Dom 2015-01-22 2.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2767-11 Dom 2011-12-13.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2816-09 Dom 2011-02-16.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2860-12 Dom 2013-10-22.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2861-11 Dom 2012-06-26.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2886-11 Dom 2012-07-06.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 2921-10 Dom 2011-07-25.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 3-15 Dom 2015-12-14.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 3140-11 Dom 2012-08-31.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 3274-11 Dom 2012-12-13.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 383-11 Dom 2012-08-31.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 399-14 Dom 2014-07-04.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 434-18 Dom 2018-04-03.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 471-14 Dom 2014-11-20.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 524-14 Dom 2014-12-19.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 546-14 Dom 2014-04-01.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 557-16 Dom 2016-12-20.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 558-16 Dom 2016-07-07.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 575-08 Dom 2009-01-21.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 584-17 Dom 2017-09-19.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 585-16 Dom 2016-07-07.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 590-14 Dom 2014-03-21.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 604-10 Dom 2011-05-05.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 611-19 Deldom 2019-04-26.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 675-10 Dom 2010-10-22.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 684-09 Dom 2010-10-01.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 738-13 Dom 2014-02-04.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 838-14 Deldom 2014-05-14.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 846-15 Dom 2016-04-15.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 860-12 Dom 2012-12-14.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 865-13 Dom 2013-07-23.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 880-12 Dom 2013-10-17.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 929-10 Dom 2010-12-17.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/Umeå TR T 941-14 Dom 2015-03-04.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 1280-12 Dom 2014-02-27.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 2033-18 Deldom 2018-09-21.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 2525-17 Dom 2017-06-16.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 3203-16 Dom 2017-05-26.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 6362-19 Dom 2020-11-18.pdf",	"P:/2020/14/Tingsrätter/Uppsala/Domar/all_cases/Uppsala TR T 8077-10 Dom 2011-09-27.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 1375-12 Dom 2012-06-15.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 2393-19 Dom 2019-12-17.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 2406-08 Dom 2008-11-13.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 2903-17 Dom 2017-09-01.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 3851-19 Dom 2020-04-16.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 617-09 Dom 2009-06-05.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 621-10 Dom 2010-04-29.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 715-10 Dom 2010-04-13.pdf",	"P:/2020/14/Tingsrätter/Vänersborgs/Domar/all_cases/Vänersborgs TR T 892-08 Dom 2008-11-10.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/T 873-08.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR B 5314-17 Dom 2019-05-03.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 1733-11 Dom 2012-03-30.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 3519-17 Dom 2018-03-20.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 3644-08 Dom 2009-07-16.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 3834-19 Dom 2020-09-02.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 3944-15 Dom 2016-02-16.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 4148-16 Dom 2017-05-31.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 4257-18 Dom 2019-11-05.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 4914-14 Dagboksblad 2021-09-22.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 4983-19 Dom 2020-10-23.pdf",	"P:/2020/14/Tingsrätter/Västmanlands/Domar/all_cases/Västmanlands TR T 585-15 Dom 2015-07-08.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 1257-14 Dom 2014-06-18.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 1412-15 Dom 2015-11-20.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 1662-10 Dom 2010-08-20.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 2061-20 Dom 2020-06-15.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 232-19 Dom 2019-10-02.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 349-09 Dom 2010-10-06.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 3886-17 Deldom 2018-07-06.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 4190-15 Dom 2016-01-12.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 4985-16 Dom 2017-10-26.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 740-11 Dom 2013-10-31.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 966-11 Dom 2011-05-24.pdf",	"P:/2020/14/Tingsrätter/Ystads/Domar/all_cases/Skåne HR T 2829-19 Slutligt beslut (ej särskilt uppsatt) 2019-10-11.pdf",	"P:/2020/14/Tingsrätter/Ystads/Domar/all_cases/Ystads TR T 1452-16 Dom 2017-01-19.pdf",	"P:/2020/14/Tingsrätter/Ångermanlands/Domar/all_cases/Ångermanlands TR T 495-18 Dom 2019-02-20.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1057-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1101-02.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1117-02.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1160-02.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1162-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1180-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1206-97.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1216-98 (2).pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1216-98.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/122-98.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1228-00.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1269-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1271-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1279-04.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1326-04.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1408-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/141-00.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1466-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1469-02.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1473-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1474-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1475-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1483-00.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1493-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1494-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1495-99.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1501-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/157-00.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1600-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1620-02.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1622-99.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1641-97.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1669-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1755-97.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1822-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1866-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1927-99.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1949-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/1953-00.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/200-96.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2013-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2078-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2098-98.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2119-99 (2).pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2119-99.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2176-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2208-00.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2210-97.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2216-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2240-02.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/225-00.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/225-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/227-97.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2302-04.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2303-02.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2320-02.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2361-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2381-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2448-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2457-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2470-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2499-00.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2503-97.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2542-02.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2550-01 (2).pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2550-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2583-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2585-00.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2590-02.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2625-06.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2670-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2671-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2702-98.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2726-02.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2766-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2780-97.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2817-98.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2865-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2960-02.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2993-07.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/3054-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/3066-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/3067-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/308-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/3121-02.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/3232-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/3247-02.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/3255-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/3256-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/3264-02.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/3270-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/3297-02.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/3310-02.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/3316-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/3344-02.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/3372-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/3373-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/3386-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/3441-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/3521-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/3521-02.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/3620-02.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/363-04.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/420-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/455-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/494-00.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/496-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/560-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/562-02.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/571-04.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/587-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/608-04.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/651-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/658-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/66-02.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/664-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/674-04.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/68-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/681-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/686-98.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/727-96.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/74-99.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/750-02.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/760-98.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/760-99.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/80-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/809-00.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/814-00.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/825-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/830-97.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/834-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/839-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/850-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/864-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/915-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/93-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/947-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/958-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/979-99.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 1399-09 Dom 2009-07-06.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 1877-19 Dom 2020-03-06 2.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 2647-18 Dom 2019-04-01.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 2926-11 Dom 2012-06-27.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 3129-10 Dom 2011-09-21.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 411-17 Dom 2017-02-03.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 4250-13 Dom 2013-12-19.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 4476-15 Dom 2017-01-17.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 4520-12 Dom 2014-01-29.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 4684-09 Dom 2011-10-17.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 5183-15 Dom 2016-04-21.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 5598-15 Dom 2016-04-21.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 5701-11 Dom 2012-10-15.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 6102-18 Dom 2019-06-28.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 798-15 Dom 2015-05-27.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/Örebro TR T 814-11 Dom 2012-04-23.pdf",	"P:/2020/14/Tingsrätter/Östersunds/Domar/all_cases/Östersunds TR T 603-17 Dom 2017-06-01.pdf"]
                
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




        
    
        
        
            
