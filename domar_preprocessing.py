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
    
"""

import Levenshtein as leven #correct misspelled judge names with this 

import re, shutil, glob, io, pdfminer, pandas as pd

from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.converter import PDFPageAggregator


#Define Paths
pdf_dir = "P:/2020/14/Kodning/Test-round-3/check"
output_path = 'P:/2020/14/Kodning/Test-round-4/custody_data_test4.csv'

#Define key functions

#PDF characteristics
def createPDFDoc(fpath):
    fp = open(fpath, 'rb')
    parser = PDFParser(fp)
    document = PDFDocument(parser, password='')
    # Check if the document allows text extraction. If not, abort.
    if not document.is_extractable:
        raise "Not extractable"
    else:
        return document

def createDeviceInterpreter():
    rsrcmgr = PDFResourceManager()
    laparams = LAParams()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    return device, interpreter

def parse_obj(objs):
    for obj in objs:
        if isinstance(obj, pdfminer.layout.LTTextBox):
            for o in obj._objs:
                if isinstance(o,pdfminer.layout.LTTextLine):
                    text=o.get_text()
                    if text.strip():
                        for c in  o._objs:
                            if isinstance(c, pdfminer.layout.LTChar):
                                if "bold" in c.fontname.lower() and not any([x in text.lower() for x in footer]):
                                    boldWords.append(text)
        elif isinstance(obj, pdfminer.layout.LTFigure):
            parse_obj(obj._objs)
        else:
            pass
    return boldWords

#General functions
def uniqueList(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]

def split(txt, seps):
    default_sep = seps[0]
    for sep in seps[1:]:
        txt = txt.replace(sep, default_sep)
    return [i.strip() for i in txt.split(default_sep)]

#Text search
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
        sentences = findSentence(term, part)
        sentenceList = sentences.split('.')
        for sentence in sentenceList:
            if term in part and not any([x in sentence for x in rejectKey]):
                dummy = 1
                break
            else:
                dummy = 0
                continue
        else:
            continue
        break
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
unread_files = [""]
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
capLetters = '[A-ZÅÐÄÖÉÜÆØÞ]'
lowerLetters = '[a-zåäïüóöéæøßþîčćžđšžůúýëçâêè]'
allLetters = '[A-ZÅÐÄÖÉÜÆØÞ][a-zåäïüóöéæøßþîčćžđšžůúýëçâêè]'
anyLetters = '[A-ZÅÐÄÖÉÜÆØÞa-zåäïüóöéæøßþîčćžđšžůúýëçâêè]'

dateSearch = {
    '1' : 'dom\s+(\d*-\d*-\d*)',
    '2' : 'dom\s+sid\s*1\s*[(][0-9]*[)]\s*(\d*-\d*-\d*)',
    '3' : '(\d{4}-\d{2}-\d{2})'
    }
courtSearch = {
    '1' : '((\w+ ){1})T\s*I\s*N\s*G\s*S\s*R\s*Ä\s*T\s*T',
    '2' : '((\w+){1})[.]?.?T\s*I\s*N\s*G\s*S\s*R\s*A\s*T\s*T',
    '3' : '((\w+){1})\s*tingsrätt'
    }
judgeSearch = {
    '1': '\n\s*\n\s*((' + allLetters + '+\s+){2,4})\n\s*\n', #normal names
    '2': '\n\s*\n\s*(' + allLetters + '+-' + allLetters + '+\s' + allLetters + '+\s+)\n\s*\n', #first name hyphenated
    '3': '\n\s*\n\s*(' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+\s+)\n\s*\n', #last name hypthenated
    '4': '\n\s*\n\s*(' + allLetters + '+-' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+\s+)\n\s*\n', #first and last name hyphenated
    '5': '\n\s*\n\s*(' + allLetters + '+\s' + capLetters + '\s' + allLetters + '+\s+)\n\s*\n', #name with initial as second name
    #if there is a note in the line following the judge's name
    '6': '\n\s*\n\s*((' + allLetters + '+\s+){2,4})\n', #normal names
    '7': '\n\s*\n\s*(' + allLetters + '+-' + allLetters + '+\s' + allLetters + '+\s+)\n', #first name hyphenated
    '8': '\n\s*\n\s*(' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+\s+)\n', #last name hypthenated
    '9': '\n\s*\n\s*(' + allLetters + '+-' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+\s+)\n', #first and last name hyphenated
    '10': '\n\s*\n\s*(' + allLetters + '+\s' + capLetters + 's\s' + allLetters + '+\s+)\n', #name with initial as second name
    #For documents where judge didnt sign
    '11': 'rådmannen\s*((' + allLetters + '+\s+){2,4})',
    '12': 'rådmannen\s*(' + allLetters + '+-' + allLetters + '+\s' + allLetters + '+\s+)', #first name hyphenated
    '13': 'rådmannen\s*(' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+\s+)', #last name hypthenated
    '14': 'rådmannen\s*(' + allLetters + '+-' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+\s+)', #first and last name hyphenated
    '15': 'rådmannen\s*(' + allLetters + '+\s' + capLetters + '\s' + allLetters + '+\s+)', #name with initial as second name
    '16': 'tingsfiskalen\s*(([' + allLetters + '+\s+){2,4})',
    '17': 'tingsfiskalen\s*(' + allLetters + '+-' + allLetters + '+\s' + allLetters + '+\s+)', #first name hyphenated
    '18': 'tingsfiskalen\s*(' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+\s+)', #last name hypthenated
    '19': 'tingsfiskalen\s*(' + allLetters + '+-' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+\s+)', #first and last name hyphenated
    '20': 'tingsfiskalen\s*(' + allLetters + '+\s' + capLetters + '\s' + allLetters + '+\s+)', #name with initial as second name
    #when judge's name ends with . 
    '21': '\n\n((' + allLetters + '+\s+){1,3}' + allLetters + '+).\s*\n\n', #normal names
    '22': '\n\s*\n\s*(' + allLetters + '+-' + allLetters + '+\s' + allLetters + '+).\s*\n', #first name hyphenated
    '23': '\n\s*\n\s*(' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+).\s*\n', #last name hypthenated
    '24': '\n\s*\n\s*(' + allLetters + '+-' + allLetters + '+\s' + allLetters + '+-' + allLetters + ').\s*\n', #first and last name hyphenated
    '25': '\n\s*\n\s*(' + allLetters + '+\s' + capLetters + '\s' + allLetters + '+).\s*\n' #name with initial as second name
    }

nameSearch = {
    '1': '\n((' + allLetters + '+\s+){1,3}' + allLetters + '+)', #normal names
    '2': '\n(' + allLetters + '+-' + allLetters + '+\s' + allLetters + '+)', #first name hyphenated
    '3': '\n(' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+)', #last name hypthenated
    '4': '\n(' + allLetters + '+-' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+)', #first and last name hyphenated
    '5': '\n(' + allLetters + '+\s' + capLetters + '\s' + allLetters + '+)', #name with initial as second name
    '6': '\n(' + capLetters + '+\s' + allLetters + '+\s' + allLetters + '+)', #preferred name capitalized, first
    }

#Define keys for simple word search
fastInfoKey = ['snabbupplysning', 'upplysning', 'snabbyttrande']
corpTalksKey = ['samarbetssamtal','medlingssamtal','medling', 'medlare']
mainHearingKey = ['huvudförhandling' , ' rättegång ' , 'sakframställning' , ' förhör ' ]
lawyerKey = ["ombud:", 'god man:',  'advokat:', "ombud", 'god man',  'advokat']
investigationKey = ['vårdnadsutredning','boendeutredning','umgängesutredning']
investigationHelper = ["vårdn", "umgänge", "boende"]
agreementKey = ['samförståndslösning',  'överens', 'medger', 'medgett', ' ense ']
agreementAdd = ['framgår' ,'enlighet' ,'följer','fastställa', 'kommit','barnets','bästa', 'vård'] #remove partnerna, potentially include again
agreementHelper = ['umgänge', 'boende']
socialOffice = ['social', 'nämnden', 'kommun', 'familjerätt']
umgangeKey = ['umgänge', 'umgås']
separationKey = ['separera', 'relationen tog slut', 'förhållandet tog slut', 'relationen avslutades', 'förhållandet avslutades', 'skildes', 'skiljas', 'skiljer' ]
rejectKey = ['avskriv',' ogilla','utan bifall','avslå',' inte ','skrivs', 'kvarstå', ' inga ']  
excludePhysical = ['jämna' , 'växelvis', 'skyddat']
remindKey = ['bibehålla' ,'påminn' ,'erinra' ,'upply', 'kvarstå']
footer = ['telefax', 'e-post', 'telefon', 'besöksadress', 'postadress', 'expeditionstid', 'dom']

#Intiialize lists and dictionary to fill
data = {'Barn':[], 'Målnr':[], 'Tingsrätt':[], 'År avslutat':[], 'Deldom':[], 'Divorce_only': [] ,'Kärande förälder':[], 'Svarande förälder':[], 'Kär advokat':[], 'Sv advokat':[], 'Defendant_address_secret': [], 'Plaintiff_address_secret':[], 'Sv utlandet':[], 'Sv okontaktbar':[], 'Utfall':[], 'Umgänge':[], 'Stadigvarande boende':[], 'Underhåll':[], 'agreement_legalcustody':[], 'agreement_any':[], 'Snabbupplysning':[], 'Samarbetssamtal':[], 'Utredning':[], 'Huvudförhandling':[], 'SeparationYear': [], 'Domare':[], "Page Count": [], 'Rättelse': [], 'Flag': [],"File Path": []}

#Loop over files and extract data
for file in pdf_files:
    #try:
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
    firstPageFormattedView = (pages_text_formatted[0]).split(".")
    
    if "Rättelse" in firstPage:
        fullTextOG = ''.join(pages_text[1:])
        firstPage = ''.join(pages_text[1])
        fullTextFormatted = ''.join(pages_text_formatted[1:])
        firstPageFormatted = pages_text_formatted[1]
        dummyRat = 1
    else:
        fullTextOG = ''.join(pages_text)
        fullTextFormatted = '.'.join(pages_text_formatted)
        firstPageFormatted = pages_text_formatted[0]
        dummyRat = 0

    splitTextOG = re.split('_{10,40}', fullTextOG)
        
    #Get headings in bold
    print(firstPageFormattedView)
    boldWords = []
    document=createPDFDoc(file)
    device,interpreter=createDeviceInterpreter()
    pages=PDFPage.create_pages(document)
    for i, page in enumerate(PDFPage.create_pages(document)): 
        interpreter.process_page(page)
        layout = device.get_result()
        if i == 0:
            parse_obj(layout._objs)
            boldWordsFirstPage = uniqueList(boldWords)
        else:
            parse_obj(layout._objs)
    boldWordsAllPages = uniqueList(boldWords)  
    
    noOfFiles += 1      
    headerFormatted = re.split(boldWordsFirstPage[0], re.split('_{10,40}', firstPageFormatted)[0])[1]                        
    headerOG = re.split('_{10,40}', firstPage)[0]
    header = headerOG.lower()    
    appendixPage = [i for i, item in enumerate(pages_text) if re.search(appendixStart, item)]
    if not appendixPage:
        appendixPageNo = len(pages_text)
    else:
        appendixPageNo = appendixPage[0]
    lastPageFormatted = '.'.join((pages_text_formatted[appendixPageNo-1]).split(".")) + '.'.join((pages_text_formatted[appendixPageNo-2]).split(".")) + '.'.join((pages_text_formatted[appendixPageNo-3]).split("."))
    lastPageFormattedView = (pages_text_formatted[appendixPageNo-2]).split(".")
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
        rulingOnlyOG1 = re.split('\n\s*\n\s*[A-ZÅÄÖ., ]{3,}(?!DOM)\s*\n', rulingStringFormatted)[0]
        rulingOnlyOG = ' '.join(''.join(rulingOnlyOG1).split())
        rulingOnly = rulingOnlyOG.lower()
    except AttributeError:
        rulingOnlyOG = ' '.join(''.join(re.split('(YRKANDEN)', rulingStringFormatted)[0].lower() ).split())
        rulingOnly = rulingOnlyOG.lower()
    
    sectionsFirstPage = split(headerFormatted, boldWordsFirstPage)
    print(firstPageFormattedView)
    
    nameList = []
    try:
        svarandeStringOG = re.split(svarandeSearch, headerOG)[1] 
        kärandeStringOG = re.split('Kärande|KÄRANDE', (re.split(svarandeSearch, headerOG)[0]))[1]
        if svarandeStringOG == "":
            svarandeStringOG = re.split(svarandeSearch, headerOG)[2] 
        elif len(kärandeStringOG.split()) < 4:
            for i in nameSearch:
                result = re.finditer(nameSearch[i], headerFormatted)
                for n in result:
                    if n.group(0) and not any([x in n.group(0).lower() for x in lawyerKey]):
                        nameList.append(n.group(0))    
    except IndexError:
        try:
            svarandeStringOG = re.split('_{10,40}', (re.split('2[.]\s*', (re.split('1[.]\s*', (re.split('PARTER|Parter', headerOG)[1]))[1]))[1]))[0]
            kärandeStringOG = re.split('2[.]\s*', (re.split('1[.]\s*', (re.split('PARTER|Parter', headerOG)[1]))[1]))[0]
        except IndexError:
            try:
                for i in nameSearch:
                    result = re.finditer(nameSearch[i], headerFormatted)
                    for n in result:
                        if n.group(0) and not any([x in n.group(0).lower() for x in lawyerKey]):
                            nameList.append(n.group(0))
            except IndexError:
                svarandeStringOG = 'not found'
                kärandeStringOG = 'not found'
                #ADD MARKER
    svarandeString = svarandeStringOG.lower()
    kärandeString = kärandeStringOG.lower()
    
    #District Court
    courtName = searchLoop(courtSearch, fullTextOG, 0).lower()
    courtNameList = courtName.split()
    
    #Get DOMSKÄL part
    try:
        domStart = re.split('DOMSKÄL', rulingString)[1].lower()
        domskal = re.split('överklag', domStart)[0]
    except:
        try:
            domStart = re.split('BEDÖMNING', rulingString)[1].lower()
            domskal = re.split('överklag', domStart)[0]
        except:
            domskal = '-'

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
        childNameKey = ('([A-ZÅÐÄÖÉÜÆØÞ][A-ZÅÐÄÖÉÜÆØÞa-zåäïüóöéæøßþîčćžđšžůúýëçâêè]+)\s*[,]?\s*[(]?\s*' + i )
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
                childNameFull = childNameFirst
        else:
            childNameFull = 'not found'
            childNameFirst = 'not found'
        childNameFirst = childNameFirst.lower()
        childTerms = [childNameFirst, 'barn']   
        
        #Case ID for child i
        caseNo = ''.join((searchKey(searchCaseNo, header, 2)).split())

        #Year Closed
        date = searchLoop(dateSearch, header, 1)

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
            if '-' in plaintNameFirst:
                plaintNameFirst = plaintNameFirst.split('-')[0]
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
            print('abroad 1')
        elif cityString.isdecimal():
            dummyAbroad = 1
            print('abroad 2')
        elif svNameFirst in findTwoWords('inte', 'sverige', fullText):
            dummyAbroad = 1
            print('abroad 3')
        elif 'utomlands' in findTwoWords('befinn', 'sig', fullText):
            dummyAbroad = 1 #didnt include svNameFirst because sv might be referred to by Han
            print('abroad 4')
        #elif searchKey(defendantNationality, svarandeString, 0) and 'sverige' not in searchKey(defendantNationality, svarandeString, 0):
            #dummyAbroad = 1
            #print('abroad 5')
            #Refine this: false positives for non-Swedish citizens that do have a Swedish address 
        else:
            dummyAbroad = 0
        
        #Secret address dummy
        if ' sekretess ' in svarandeString:
            dummyDefSecret = 1
        else:
            dummyDefSecret = 0
        if ' sekretess ' in kärandeString:
            dummyPlaintSecret = 1
        else:
            dummyPlaintSecret = 0   
        
        #Defendant unreachable
        print(findSentence('förordnat god man', fullText))
        if 'okontaktbar' in fullText or 'förordnat god man' in fullText and svNameFirst in findSentence('förordnat god man', fullText):
            print('unreach1')
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
            print('unreach8')
            dummyUnreach = 1
        elif svGodMan == 1 and not findTwoWords(svNameFirst, 'genom', findTwoWords('sin', 'gode man', fullText)):
            dummyUnreach = 1
            print('unreach9')    
        else:
            print('unreach10')
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
        vardnInGemensam = 'vård' in findGemensam
        findEnsam = findFirstOccur('ensam', rulingOnly)
        findVardn = findFirstOccur('vård', rulingOnly)
        findEnsamVardn = findTwoWordsFirstOccur('ensam','vård',rulingOnly)
        findGemensamVardn = findTwoWordsFirstOccur('gemensam', 'vård', rulingOnly)
        findVardnBarn = findTwoWordsFirstOccur('barn', 'vård', rulingOnly)
        transferToDef = 'till ' + svNameFirst
        transferToPlaint = 'till ' + plaintNameFirst
        vardnInRuling = 'vård' in rulingOnly
        findChild = findSentence(childNameFirst, rulingOnly)

        print("RULING ONLY: "+rulingOnly)       
                
        if 'vård' not in rulingOnly: #reduced to vård to account for vårdanden
            #No custody ruling in this court record
            print("out1a")
            dummyOut = 0
        elif termLoop(remindKey, findVardn):
            dummyOut = 0
            print("out1b")
        elif 'vård' not in findChild:
            print('out1c')
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
        elif i in findVardn and vardnInGemensam and 'anförtro' in findVardn and not any([x in findGemensamVardn for x in rejectKey]): 
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
        elif i in findVardn and plaintNameFirst in findVardn and not any([x in findVardn for x in rejectKey]):
            dummyOut = 2
            print('out18')
        elif i in findVardn and svNameFirst in findVardn and not any([x in findVardn for x in rejectKey]):
            dummyOut = 3
            print('out19')
        elif 'bilaga' in rulingOnly and 'överens' in findSentence('bilaga', rulingOnly):
            dummyOut = 999
            print("out16")
        else: 
            dummyOut = 999
            print("out17")
        
        #Divorce dummy
        if dummyOut == 0 and 'äktenskapsskill' in rulingOnly: #potentially also include mellan
            dummyDivorce = 1
        else:
            dummyDivorce = 0
                        
        #Visitation rights  
        for term in childTerms:
            for key in umgangeKey:
                findUmg = findTwoWordsFirstOccur(key, term, rulingOnly)
                if childNameFirst == 'not found':
                    dummyVisit = 999
                    print('umg1')
                    break
                elif findTwoWords('semester', term, rulingOnly):
                    print('umg3')
                    dummyVisit = 0
                    break
                elif findTwoWords('sommar', term, rulingOnly):
                    print('umg4')
                    dummyVisit = 0
                    break
                elif findTwoWords('bilaga', 'sidorna', rulingOnly):
                    print('umg5')
                    dummyVisit = 999
                    break
                elif findUmg and not any([x in findUmg for x in rejectKey]):  
                    print('umg2')
                    dummyVisit = 1
                    break 
                else:
                    print('umg5')
                    dummyVisit = 0
                    continue
            else:
                continue
            break

        #N. Physical custody           
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
        if findSentence('underhåll', rulingOnly) and not any([x in findSentence('underhåll', rulingOnly) for x in rejectKey]):
            dummyAlimon = 1
        elif findTwoWords('bilaga', 'sidorna',  rulingOnly):
            dummyAlimon = 999                    
        else:
            dummyAlimon = 0 
                    
        #Ruling by agreement
        for termAgree in agreementKey:
            findAgree1 = findThreeWords(svNameFirst,'yrkande', termAgree, domskal)
            if svNameFirst in findTwoWords('yrkande', termAgree, domskal) and not any([x in findAgree1 for x in agreementHelper]):
                print('agree1: ' + termAgree)
                dummyAgree = 1
                dummyUnreach = 0
                break
            for termHelper in agreementAdd:
                findAgree2 = findTwoWords(termAgree, termHelper, domskal)
                if findAgree2 is not emptyString and not any([x in findAgree2 for x in agreementHelper]):
                    print('agree2: '+ termAgree + termHelper)
                    dummyAgree = 1
                    dummyUnreach = 0
                    break
                elif findAgree2 is not emptyString and any([x in findAgree2 for x in agreementHelper]) and 'vård' in findAgree2:
                    print('agree3: '+ termAgree + termHelper)
                    dummyAgree = 1
                    dummyUnreach = 0
                    break
                else:
                    dummyAgree = 0
                    continue
            else: 
                continue
            break
        if dummyAgree == 0 and 'förlikning' in findTwoWords('framgå', 'träff', domskal):
            print('agree4')
            dummyAgree = 1
            dummyUnreach = 0
        #Now search for any agreement
        if dummyOut == 0 and dummyAgree == 0:
            for termAgree in agreementKey:
                findAgree1 = findThreeWords(svNameFirst,'yrkande', termAgree, fullText)
                if svNameFirst in findTwoWords('yrkande', termAgree, fullText):
                    print('agree any 1: ' + termAgree)
                    dummyAgreeAny = 1
                    dummyUnreach = 0
                    break
                for termHelper in agreementAdd:
                    findAgree2 = findTwoWords(termAgree, termHelper, fullText)
                    if findAgree2 is not emptyString:
                        print('agree any 2: '+ termAgree + termHelper)
                        dummyAgreeAny = 1
                        dummyUnreach = 0
                        break
                    elif findAgree2 is not emptyString and any([x in findAgree2 for x in agreementHelper]):
                        print('agree any 3: '+ termAgree + termHelper)
                        dummyAgreeAny = 1
                        dummyUnreach = 0
                        break
                    else:
                        dummyAgreeAny = 0
                        continue
                else: 
                    print('in else for agree')
                    continue
                break
        else:
            dummyAgreeAny = 0
        #Criteria for exclusion
        if dummyAgree == 1 and len(domskal.split()) > 1700:
            dummyAgree = 0
        if dummyAgree == 1 and pageCount >= 10:
            dummyAgree = 0
           
        #Fast information (snabbupplysningar)
        if termLoop(socialOffice, findSentence('yttra', fullText)):
            print("snabbupply 1")
            dummyInfo = 1
        elif '6 kap. 20 § andra stycket föräldrabalken' in fullText:
            dummyInfo = 1 
            print("snabbupply 3 ")
        else:
            dummyInfo = termLoop(fastInfoKey, fullText)
            print("snabbupply 4" )
              
        #Cooperation talks
        dummyCoop = termLoopFirstOccur(corpTalksKey, fullText)
           
        #Investigation
        dummyInvest = termLoop(investigationKey, fullText)
        if dummyInvest == 0:
            if 'ingsrätt' in findSentence(' utred', fullTextOG) and not any([x in findSentence(' utred', fullTextOG) for x in rejectKey]) and not findThreeWords('saknas', 'möjlighet', ' utred', fullText): #search for tingsratt or Tingsratt in fullTextOG to not get the TINGSRATT from header
                print('invest1')
                dummyInvest = 1
            elif any([x in findSentence(' utred', fullText) for x in socialOffice]) and not any([x in findSentence(' utred', fullTextOG) for x in rejectKey]) and not findThreeWords('saknas', 'möjlighet', ' utred', fullText):
                print('invest2')
                dummyInvest = 1
            elif "11 kap. 1 § socialtjänstlagen" in fullText:
                print('invest3')
                dummyInvest = 1
            else:
                print('invest4')
                for term in investigationHelper:
                    if term in findSentence(' utred', fullText) and not any([x in findSentence(' utred', fullTextOG) for x in rejectKey]):
                        print(term)
                        print('invest5')
                        dummyInvest = 1
                        break
                    else:
                        print('invest6')
                        dummyInvest = 0
                        continue
        
        #Main hearing 
        for term in mainHearingKey:
            if findSentence(term, fullText) and 'utan' not in findSentence(term, fullText) and ' ingen' not in findSentence(term, fullText):
                print('mainhear1: ' + term)
                dummyMainHear = 1
                break
            else:
                dummyMainHear = 0
                continue
                        
        #Name of judge
        try:
            judgeName = ((searchLoop(judgeSearch, lastPageFormatted, 1)).split('\n'))[0]
        except:
            judgeName = 'Not found'
            
        #Flag cases
        flag = []
        livingTerms = [' bo ', 'boende']
        if termLoop(socialOffice, findSentence('uppgett', fullText)):
            flag.append('snabbupplysning')
        if svNameFirst in childNameFull.lower() or plaintNameFirst in childNameFull.lower():
            flag.append('check_all')
        for term in livingTerms:
            if any([x in findSentence(term, rulingOnly) for x in excludePhysical]):
                flag.append('Stadigvarande boende')
            if term in rulingOnly and dummyPhys == 0 and not any([x in findSentence(term, rulingOnly) for x in excludePhysical]):
                flag.append('Stadigvarande boende')
        for term in investigationHelper:
            if term in findSentence(' utred', fullText):
                flag.append('Utredning')
                break
        if findThreeWords('ensam', 'gemensam ', 'vård', rulingOnly):
            flag.append('utfall')
        if svGodMan == 1 and not findTwoWords(svNameFirst, 'genom', findTwoWords('sin', 'gode man', fullText)):
            flag.append('Sv okontaktbar')

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
        data['Divorce_only'].append(dummyDivorce)
        data['Kärande förälder'].append(plaintNo) 
        data['Svarande förälder'].append(svNo)   
        data['Defendant_address_secret'].append(dummyDefSecret)  
        data['Plaintiff_address_secret'].append(dummyPlaintSecret)  
        data['Kär advokat'].append(dummyOmbPlaint)
        data['Sv advokat'].append(defOmbud)
        data['Sv utlandet'].append(dummyAbroad)
        data['Sv okontaktbar'].append(dummyUnreach)
        data['Utfall'].append(dummyOut)   
        data['Umgänge'].append(dummyVisit)
        data['Stadigvarande boende'].append(dummyPhys)
        data['Underhåll'].append(dummyAlimon)                
        data['agreement_legalcustody'].append(dummyAgree)    
        data['agreement_any'].append(dummyAgreeAny)  
        data['Snabbupplysning'].append(dummyInfo)          
        data['Samarbetssamtal'].append(dummyCoop)
        data['Utredning'].append(dummyInvest)
        data['SeparationYear'].append(dummySeparate)
        data['Huvudförhandling'].append(dummyMainHear)
        data['Flag'].append(flag)
"""
    except:
        data['Barn'].append('error')
        data["File Path"].append(file)
        data["Page Count"].append('error')
        data['Rättelse'].append('error')
        data['Målnr'].append('error')
        data['Domare'].append('error')
        data["Tingsrätt"].append('error')
        data['År avslutat'].append('error')
        data['Deldom'].append('error')
        data['Divorce_only'].append('error')
        data['Kärande förälder'].append('error') 
        data['Svarande förälder'].append('error')   
        data['Kär advokat'].append('error')
        data['Sv advokat'].append('error')
        data['Sv utlandet'].append('error')
        data['Sv okontaktbar'].append('error')
        data['Utfall'].append('error')   
        data['Umgänge'].append('error')
        data['Stadigvarande boende'].append('error')
        data['Underhåll'].append('error')                
        data['agreement_legalcustody'].append('error')    
        data['agreement_any'].append('error')  
        data['Snabbupplysning'].append('error')          
        data['Samarbetssamtal'].append('error')
        data['Utredning'].append('error')
        data['SeparationYear'].append('error')
        data['Huvudförhandling'].append('error')
        data['Flag'].append('error')
"""        
#Dataframe created from dictionary
df = pd.DataFrame(data)
with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    print(df)

#Save to csv
#df.to_csv(output_path, sep = ',', encoding='utf-8-sig')

print("---Saved as CSV---")
print('Unreadable: ')
print(noUnreadable)




