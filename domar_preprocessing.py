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

import re, shutil, glob, io, pdfminer, pandas as pd

from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.converter import PDFPageAggregator

#Runtime
import time
start_time = time.time()

#Define Paths
pdf_dir = 'P:/2020/14/Kodning/Test-round-4/files/'
output_path = 'P:/2020/14/Kodning/Test-round-4/custody_data_test4_v02.csv'

#Define key functions
#PDF characteristics
def filereader_params():
    rsrcmgr = PDFResourceManager()
    retstr = io.StringIO()
    codec = 'utf-8-sig'
    laparams = LAParams(line_margin=3)
    device1 = PDFPageAggregator(rsrcmgr, laparams=laparams)
    device2 = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    interpreter1 = PDFPageInterpreter(rsrcmgr, device1)
    interpreter2 = PDFPageInterpreter(rsrcmgr, device2)
    return rsrcmgr,retstr,device1,device2,interpreter1,interpreter2

def createPDFDoc(fpath):
    fp = open(fpath, 'rb')
    parser = PDFParser(fp)
    document = PDFDocument(parser, password='')
    return document

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

def splitParts(txt, seps):
    default_sep = seps[0]
    for sep in seps[1:]:
        txt = txt.replace(sep, default_sep)
    return [i.strip() for i in txt.split(default_sep)]

#Text search
def findTerms(stringlist, part):
    sentenceRes = [sentence + '.' for sentence in part.split('.') if all([x in sentence for x in stringlist])]
    sentenceString = ''.join(sentenceRes)
    return sentenceString

def firstOccurance(stringlist, part):
    sentenceRes = [sentence + '.' for sentence in part.split('.') if all([x in sentence for x in stringlist])]
    if sentenceRes:
        sentenceString = sentenceRes[0]
    else:
        sentenceString = ''
    return sentenceString

def searchKey(string, part, g):
    finder = re.compile(string)
    match = finder.search(part)
    if match is not None:
        searchResult = match.group(g)
    else:
        searchResult = None
    return searchResult
        
def searchLoop(searchDict, part, g, excludeTerms):
    for i in searchDict:
        result = searchKey(searchDict[i], part, g)
        if result is None or any([x in result.lower() for x in excludeTerms]):
            continue
        else: 
            break
    return result

def termLoop(termList, part):
    for term in termList:
        sentences = findTerms([term], part)
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

def city(string,i):
    stringList = (string.strip()).split(" ")
    return stringList[-i]

#Variables
def party_id(party_stringOG, string1, g1, string2, part2, g2):
    if ',' in party_stringOG:
        full = party_stringOG.split(",")[0]
    else:
        full = party_stringOG.split("\n")[1]
    #print('full name 1: ',full)
    try:
        first = searchKey(string1, full, g1).lower()
        #print('first name 1: ',first)
    except AttributeError:
        first = full.split()[0].lower()
        #print('first name 2: ',first)
        if '-' in first:
            first = first.split('-')[0]
            #print('first name 3: ',first)
    try:
        number = ''.join(searchKey(string2, part2, g2).split())
        #print('ID: ',number)
    except AttributeError:
        number = "-"
    return full, first, number

def outcome_search(searchterms, findwhere, exclude, out):
    for part in searchterms:
        if findTerms(part, findwhere) and exclude:
            print('Outcome: ',part)
            result = out
            break
        else:
            result = 999
            continue
    return result

def party_strings(): #Aadapt this with try catch so that it looks for capitalized words after bold words
    sectionsFirstPage = list(filter(None, splitParts(headerFormatted, boldWordsFirstPage)))
    kärandeStringOG = ' '.join(sectionsFirstPage[0].split('\n'))
    svarandeStringOG = ' '.join(sectionsFirstPage[1].split('\n'))
    strangePartyLabel = 1
    return kärandeStringOG, svarandeStringOG, strangePartyLabel

"""
with open('P:/2020/14/Kodning/all_files/filepaths1.txt','r') as f:
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
noUnreadable = 0
    
#Define search terms
nameCaps = '[A-ZÅÄÖ]{3,}'
svarandeSearch = ' Svarande|SVARANDE|Motpart|MOTPART|SVARANDE och KÄRANDE |MANNEN|Mannen'
idNo ='((\d{6,10}.?.?(\d{4})?)[,]?\s)'
appendixStart = '((?<!se )Bilaga 1|(?<!se )Bilaga A|sida\s+1\s+av)'
searchCaseNo = 'må.\s*(nr)?[.]?\s*t\s*(\d*\s*.?.?\s*\d*)'
word = '(\w+ )+'
capLetters = '[A-ZÅÐÄÖÉÜÆØÞ]'
allLetters = '[A-ZÅÐÄÖÉÜÆØÞ][a-zåäïüóöéæøßþîčćžđšžůúýëçâêè]'

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

#Define keys for simple word search
fastInfoKey = ['snabbupplysning', 'upplysning', 'snabbyttrande']
corpTalksKey = ['samarbetssamtal','medlingssamtal','medling', 'medlare']
mainHearingKey = ['huvudförhandling' , ' rättegång ' , 'sakframställning' , ' förhör ' ]
lawyerKey = ["ombud:", 'god man:',  'advokat:', "ombud", 'god man',  'advokat']
investigationKey = ['vårdnadsutredning','boendeutredning','umgängesutredning']
investigationHelper = ["vårdn", "umgänge", "boende"]

socialOffice = ['social', 'nämnden', 'kommun', 'familjerätt']
umgangeKey = ['umgänge', 'umgås']
separationKey = ['separera', 'relationen tog slut', 'förhållandet tog slut', 'relationen avslutades', 'förhållandet avslutades', 'skildes', 'skiljas', 'skiljer' ]
countries = ['saknas', 'okänd', 'adress', 'u.s.a.', 'u.s.a', 'usa', 'afghanistan', 'albanien', 'algeriet', 'andorra', 'angola', 'antigua och barbuda', 'argentina', 'armenien', 'australien', 'azerbajdzjan', 'bahamas', 'bahrain', 'bangladesh', 'barbados', 'belgien', 'belize', 'benin', 'bhutan', 'bolivia', 'bosnien och hercegovina', 'botswana', 'brasilien', 'brunei', 'bulgarien', 'burkina faso', 'burundi', 'centralafrikanska republiken', 'chile', 'colombia', 'costa rica', 'cypern', 'danmark', 'djibouti', 'dominica', 'dominikanska republiken', 'ecuador', 'egypten', 'ekvatorialguinea', 'elfenbenskusten', 'el salvador', 'eritrea', 'estland', 'etiopien', 'fiji', 'filippinerna', 'finland', 'frankrike', 'förenade arabemiraten', 'gabon', 'gambia', 'georgien', 'ghana', 'grekland', 'grenada', 'guatemala', 'guinea', 'guinea-bissau', 'guyana', 'haiti', 'honduras', 'indien', 'indonesien', 'irak', 'iran', 'irland', 'island', 'israel', 'italien', 'jamaica', 'japan', 'jemen', 'jordanien', 'kambodja', 'kamerun', 'kanada', 'kap verde', 'kazakstan', 'kenya', 'kina', 'kirgizistan', 'kiribati', 'komorerna', 'kongo-brazzaville', 'kongo-kinshasa', 'kroatien', 'kuba', 'kuwait', 'laos', 'lesotho', 'lettland', 'libanon', 'liberia', 'libyen', 'liechtenstein', 'litauen', 'luxemburg', 'madagaskar', 'malawi', 'malaysia', 'maldiverna', 'mali', 'malta', 'marocko', 'marshallöarna', 'mauretanien', 'mauritius', 'mexiko', 'mikronesiska federationen', 'moçambique', 'moldavien', 'monaco', 'montenegro', 'mongoliet', 'myanmar', 'namibia', 'nauru', 'nederländerna', 'nepal', 'nicaragua', 'niger', 'nigeria', 'nordkorea', 'nordmakedonien', 'norge', 'nya zeeland', 'oman', 'pakistan', 'palau', 'panama', 'papua nya guinea', 'paraguay', 'peru', 'polen', 'portugal', 'qatar', 'rumänien', 'rwanda', 'ryssland', 'saint kitts och nevis', 'saint lucia', 'saint vincent och grenadinerna', 'salo-monöarna', 'samoa', 'san marino', 'são tomé och príncipe', 'saudiarabien', 'schweiz', 'senegal', 'seychellerna', 'serbien', 'sierra leone', 'singapore', 'slovakien', 'slovenien', 'somalia', 'spanien', 'sri lanka', 'storbritannien', 'sudan', 'surinam', 'sverige', 'swaziland', 'sydafrika', 'sydkorea', 'sydsudan', 'syrien', 'tadzjikistan', 'tanzania', 'tchad', 'thailand', 'tjeckien', 'togo', 'tonga', 'trinidad och tobago', 'tunisien', 'turkiet', 'turkmenistan', 'tuvalu', 'tyskland', 'uganda', 'ukraina', 'ungern', 'uruguay', 'usa', 'uzbekistan', 'vanuatu', 'vatikanstaten', 'venezuela', 'vietnam', 'vitryssland', 'zambia', 'zimbabwe', 'österrike', 'östtimor']

excludePhysical = ['jämna' , 'växelvis', 'skyddat']
rejectKey = ['avskriv',' ogilla','utan bifall','avslå',' inte ','skrivs', 'kvarstå', ' inga '] 
rejectKeyOutcome = ['avskriv',' ogilla','utan bifall','avslå',' inte ','skrivs', 'kvarstå', ' inga ', 'utan']  
remindKey = ['bibehålla' ,'påminn' ,'erinra' ,'upply', 'kvarstå', 'fortfarande ']
footer = ['telefax', 'e-post', 'telefon', 'besöksadress', 'postadress', 'expeditionstid', 'dom']

#Intiialize lists and dictionary to fill
data = {'child_id':[], 'case_no':[], 'court':[], 'date':[], 'deldom':[], 'divorce_only': [] , 'joint_application_custody': [],'plaintiff_id':[], 'defendant_id':[], 'plaintiff_lawyer':[], 'defendant_lawyer':[], 'defendant_address_secret': [], 'plaintiff_address_secret':[], 'defendant_abroad':[], 'defendant_unreachable':[], 'outcome':[], 'visitation':[], 'physical_custody':[], 'alimony':[], 'agreement_legalcustody':[], 'agreement_any':[], 'fastinfo':[], 'cooperation_talks':[], 'investigation':[], 'mainhearing':[], 'separation_year': [], 'judge':[], 'page_count': [], 'correction_firstpage': [], 'flag': [],'file_path': []}

#Loop over files and extract data
for file in pdf_files:
    try:
    
        #Read in PDF
        print("\nCurrently reading: ", file)
        pages_text, pages_text_formatted, nameList = [],[],[]
        pageCount, strangePartyLabel = 0,0
        
        rsrcmgr,retstr,device1,device2,interpreter1,interpreter2 = filereader_params()
        with open(file, 'rb') as fh:
            for page in PDFPage.get_pages(fh,caching=True,check_extractable=True):
                read_position = retstr.tell()
                interpreter2.process_page(page)
                retstr.seek(read_position, 0)
                page_text = retstr.read()
                page_text_clean = ' '.join((''.join(page_text)).split())
                pages_text.append(page_text_clean)
                pages_text_formatted.append(page_text)
                pageCount += 1
        
        #Convert full text to clean string
        firstPage = pages_text[0]
        firstPageFormatted = pages_text_formatted[0]
        dummyRat = 0
        appendixPage = [i for i, item in enumerate(pages_text) if re.search(appendixStart, item)]
        appendixPageNo = len(pages_text)
        firstPageFormattedView = (pages_text_formatted[0]).split(".")
        
        if "Rättelse" in firstPage:     
            firstPage = ''.join(pages_text[1])
            firstPageFormatted = pages_text_formatted[1]
            dummyRat = 1
            fullTextFormatted = pages_text_formatted[1:]
            fullTextFormattedJoined = ''.join(pages_text_formatted[1:])
            fullTextOG = ''.join(pages_text[1:])
            if appendixPage:
                appendixPageNo = appendixPage[-1]
                fullTextFormatted = pages_text_formatted[1:(appendixPageNo)]
                fullTextOG = ''.join(pages_text[1:(appendixPageNo)])
                fullTextFormattedJoined = ''.join(pages_text_formatted[1:(appendixPageNo)])
        else:
            fullTextOG = ''.join(pages_text)
            fullTextFormatted = '.'.join(pages_text_formatted)
            fullTextFormattedJoined = ''.join(pages_text_formatted)
            if appendixPage:
                appendixPageNo = appendixPage[-1] #not 0 because of Gotlands 424-18
                fullTextFormatted = pages_text_formatted[0:(appendixPageNo)]
                fullTextOG = ''.join(pages_text[0:(appendixPageNo)])
                fullTextFormattedJoined = ''.join(pages_text_formatted[0:(appendixPageNo)])
                
        #Get headings in bold / note: takes a lot of computing time
        boldWords = []
        boldWordsFirstPage = []
        """
        with open(file, 'rb') as fh:
            document=createPDFDoc(file)
            for i, page in enumerate(PDFPage.create_pages(document)): 
                interpreter1.process_page(page)
                layout = device1.get_result()
                if i == 0:
                    parse_obj(layout._objs)
                    boldWordsFirstPage = uniqueList(boldWords)
                else:
                    parse_obj(layout._objs)
        boldWordsAllPages = uniqueList(boldWords)  
        """
        
        #Get header
        try:
            headerFormatted = re.split(boldWordsFirstPage[0], re.split('_{10,40}', firstPageFormatted)[0])[1]                        
        except IndexError:
            try:
                headerFormatted = re.split('PARTER|Parter', re.split('_{10,40}', firstPageFormatted)[0])[1]          
            except IndexError:
                headerFormatted = re.split('Mål', re.split('_{10,40}', firstPageFormatted)[0])[1] 
        headerOG = re.split('_{10,40}', firstPage)[0]
        header = headerOG.lower()        
    
        #Get last page of ruling with judge name
        for page in fullTextFormatted:
            for m in ['\nÖVERKLAG','\nÖverklag','\nHUR MAN ÖVERKLAG','\nHur man överklag','\nHur Man Överklag','Anvisning för överklagande']:
                if m in page:
                    lastPageFormatted = page
                    break
                elif pageCount>10:
                    lastPageFormatted = '.'.join((pages_text_formatted[appendixPageNo-1]).split(".")) + '.'.join((pages_text_formatted[appendixPageNo-2]).split(".")) + '.'.join((pages_text_formatted[appendixPageNo-3]).split("."))   
                    continue
                else: 
                    lastPageFormatted = '.'.join((pages_text_formatted[appendixPageNo-1]).split("."))
                    continue
            else:
                continue
            break
    
        #Print page formatted with: print((firstPageFormatted).split("."))
       
        #Full text
        fullText = fullTextOG.lower()
        
        #Get ruling
        try:
            rulingStringFormatted = ''.join(re.split('DOMSLUT|Domslut', fullTextFormattedJoined)[1:])
        except:
            rulingStringFormatted = ''.join(re.split('_{10,40}\s*', fullTextFormattedJoined)[1:])
        try:           
            rulingOnlyOG1 = re.split('\n\s*\n\s*[A-ZÅÄÖ., ]{3,}(?!DOM)\s*\n', rulingStringFormatted)[0]
            rulingOnlyOG = ' '.join(''.join(rulingOnlyOG1).split())
            rulingOnly = rulingOnlyOG.lower()
        except AttributeError:
            rulingOnlyOG = ' '.join(''.join(re.split('(YRKANDEN|Yrkanden)', rulingStringFormatted)[0].lower() ).split())
            rulingOnly = rulingOnlyOG.lower() 
    
        #Get domskäl or yrkanden
        try:
            domStart = re.split('DOMSKÄL|Domskäl', fullTextOG)[1].lower()
            domskal = re.split('överklag', domStart)[0]
        except:
            try:
                domStart = re.split('BEDÖMNING|Bedömning', fullTextOG)[1].lower()
                domskal = re.split('överklag', domStart)[0]
            except:
                try:
                    domStart = re.split('yrkanden |parternas begäran m.m.|yrkande m.m.', fullText)[1]
                    domskal = re.split('överklag', domStart)[0]
                except IndexError:
                    domStart = re.split('\nSkäl\s*\n', rulingStringFormatted)[1].lower()
                    domskal = re.split('överklag', domStart)[0]
                
        #Get plaintiff and defendant strings    
        try:
            svarandeStringOG = re.split('Svarande|SVARANDE', headerFormatted)[1] 
            kärandeStringOG = re.split('Kärande|KÄRANDE', (re.split('Svarande|SVARANDE', headerFormatted)[0]))[1]
            #print('PARTY1: ',svarandeStringOG)
            if svarandeStringOG == "":
                svarandeStringOG = re.split('Svarande|SVARANDE', headerFormatted)[2] 
                #print('PARTY2: ',svarandeStringOG)
            elif len(kärandeStringOG.split()) < 4:
                kärandeStringOG, svarandeStringOG, strangePartyLabel = party_strings()
                #print('PARTY3: ',svarandeStringOG)
        except IndexError:
            try:
                kärandeStringOG, svarandeStringOG, strangePartyLabel = party_strings()
                #print('PARTY4: ',svarandeStringOG)
            except IndexError:
                try:
                    svarandeStringOG = re.split(svarandeSearch, headerFormatted)[1] 
                    kärandeStringOG = re.split('Kärande|KÄRANDE|Hustrun|HUSTRUN', (re.split(svarandeSearch, headerFormatted)[0]))[1]
                    #print('PARTY5: ',svarandeStringOG)
                    if svarandeStringOG == "":
                        svarandeStringOG = re.split(svarandeSearch, headerFormatted)[2] 
                        #print('PARTY6: ',svarandeStringOG)
                    elif len(kärandeStringOG.split()) < 4:
                        svarandeStringOG = re.split("(?i)SVARANDE och KÄRANDE|SVARANDE OCH GENKÄRANDE ", headerFormatted)[1]
                        kärandeStringOG = re.split('(?i)KÄRANDE och SVARANDE|KÄRANDE OCH GENSVARANDE', (re.split("SVARANDE och KÄRANDE|SVARANDE OCH GENKÄRANDE ", headerFormatted)[0]))[1]
                        #print('PARTY7: ',svarandeStringOG)
                except IndexError:
                    try:
                        svarandeStringOG = re.split('_{10,40}', (re.split('2[.]\s*', (re.split('1[.]\s*', (re.split('PARTER|Parter', headerFormatted)[1]))[1]))[1]))[0]
                        kärandeStringOG = re.split('2[.]\s*', (re.split('1[.]\s*', (re.split('PARTER|Parter', headerFormatted)[1]))[1]))[0]
                        #print('PARTY8: ',svarandeStringOG)
                    except IndexError:
                        svarandeStringOG = 'not found, not found'
                        kärandeStringOG = 'not found, not found'
        #print('PARTY9: ',svarandeStringOG)
        svarandeString = svarandeStringOG.lower()
        kärandeString = kärandeStringOG.lower()
        
        #List of children's numbers
        childNoRes = []
        childNo = set(re.findall('\d{6,8}\s?-\s?\d{4}', rulingOnly))   
        for i in childNo:
            mistakeChilNos = searchKey("\A197|\A198|\A5|\A6|\A7|\A8", i, 0)
            if mistakeChilNos is None: 
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
            
            #Variables that are constant for all children in court doc       
            caseNo = ''.join((searchKey(searchCaseNo, header, 2)).split())
            date = searchLoop(dateSearch, header, 1, [])     
            courtName = file.split('/')[4]
            dummyDel = 1 if 'deldom' in header else 0
            plaintNameFull, plaintNameFirst, plaintNo = party_id(kärandeStringOG, nameCaps, 0, idNo, kärandeString, 2)
            defNameFull, defNameFirst, defNo = party_id(svarandeStringOG, nameCaps, 0, idNo, svarandeString, 2)   
            dummyLawyerPlaint = 1 if 'ombud' in kärandeString or "god man" in kärandeString or "advokat" in kärandeString else 0
            
            #Defendant representative
            for term in lawyerKey:
                if term in svarandeString:
                    svGodMan = 1 if 'god man' in term else 0
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
            if any([x in cityString for x in countries]):
                dummyAbroad = 1
                print('abroad 1')
            elif cityString.isdecimal():
                dummyAbroad = 1
                print('abroad 2')
            elif findTerms(['inte', 'sverige', defNameFirst], fullText):
                dummyAbroad = 1
                print('abroad 3')
            elif findTerms(['befinn', 'sig','utomlands'], fullText):
                dummyAbroad = 1 #didnt include defNameFirst because sv might be referred to by Han
                print('abroad 4')
            else:
                dummyAbroad = 0
            
            #Secret address dummy
            dummyDefSecret = 1 if ' sekretess ' in svarandeString else 0
            dummyPlaintSecret = 1 if ' sekretess ' in kärandeString else 0
    
            #Defendant unreachable 
            unreachKey = [['okontaktbar'],['förordnat god man', defNameFirst],['varken kan bestrida eller medge'],['någon kontakt', 'huvudman'],['någon kontakt', defNameFirst],['okän', 'befinn',defNameFirst]]
            for term in unreachKey:
                if findTerms(term, fullText):
                    print('Unreach 1: ', term)
                    dummyUnreach = 1
                    break
                else:
                    dummyUnreach = 0
                    continue
            if dummyUnreach != 1 and svGodMan == 1 and not findTerms([defNameFirst, 'genom', 'sin', 'gode man'], fullText):
                dummyUnreach = 1
                print('unreach3')    
    
            #Year of Separation of Unmarried Parents
            for term in separationKey:
                if term in fullText:
                    dummySeparate = searchKey('(\d\d\d\d)', findTerms([term], fullText), 0)
                    break
                else:
                    dummySeparate = '-'
                    continue
            #Outcome
            try:
                findGemensam = firstOccurance([searchKey('(gemensam)[^m]',rulingOnly,1)], rulingOnly)
            except TypeError:
                findGemensam = firstOccurance(['gemen-'], rulingOnly)
            findVardn = firstOccurance(['vård'], rulingOnly)
            
            #No custody ruling
            if 'vård' not in rulingOnly: 
                print("out1")
                dummyOut = 0
            elif termLoop(remindKey, findVardn) and 'äktenskaps' in rulingOnly:
                dummyOut = 0
                print("out2")
            elif 'vård' not in findTerms([childNameFirst], rulingOnly):
                print('out3')
                dummyOut = 0
            else:
                dummyOut = 999
            
            #Dismissed
            if dummyOut != 0:
                if 'käromalet ogillas' in rulingOnly or findTerms(['avslås', 'vårdn'], rulingOnly) or 'lämnas utan bifall' in findVardn or 'avskriv' in findVardn: #"lämnas utan bifall" in findVard because if I search in ruling only it picks up when umgange claims or so are dismissed
                    dummyOut = 4  
                    print("out4")
                else:
                    dummyOut = 999
            
            #One plaint is dismissed and another installed
            if dummyOut == 4 and findTerms(['ensam', 'gemensam', 'vårdn'], rulingOnly):
                newRuling = []
                dummyOut = 999
                for part in re.split(',|;',findTerms(['ensam', 'gemensam', 'vårdn'], rulingOnly)):
                    if not any([x in part for x in rejectKeyOutcome]):
                        newRuling.append(part)
                findGemensam = ''.join(newRuling)
                
            anyGemensam = not any([x in findGemensam for x in rejectKeyOutcome])
            anyVardn = not any([x in findVardn for x in rejectKeyOutcome])
                
            #Shared custody
            sharedCustody = [[i,'ska','om','vård'],[i,'vård','fortsätt','ska'],[i,'alltjämt','ska','vård'],
                             [i,'vård','alltjämt', 'är'],[i,'vård','skall','tillkomma'],[i,'vård','anförtro']]
            if dummyOut not in {0,4}: 
                dummyOut = outcome_search(sharedCustody, findGemensam, anyGemensam, 1)
    
            #Sole custody
            for k in [plaintNameFirst, defNameFirst]:
                soleCustody = [
                    [i,'ensam', k],[i,'över','flytt', 'till ' + k],[i, k,'tillerkänn'],[i, k,'anförtro'],
                    ['ska','tillkomma', i, k],[i,k,' ska ',' om ', ' ha ']]  
                if dummyOut not in {0,1,4} and k == plaintNameFirst:
                    dummyOut = outcome_search(soleCustody, findVardn, anyVardn, 2)  
                if dummyOut not in {0,1,2,4} and k == defNameFirst:
                    dummyOut = outcome_search(soleCustody, findVardn, anyVardn, 3)  
                else: 
                    continue
            
            #Visitation rights  
            for term in [childNameFirst, 'barn']:
                for key in umgangeKey:
                    if findTerms(['semester', term], rulingOnly) or findTerms(['sommar', term], rulingOnly):
                        print('umg1')
                        dummyVisit = 0
                        break
                    elif firstOccurance([key, term], rulingOnly) and not any([x in firstOccurance([key, term], rulingOnly) for x in rejectKey]):  
                        print('umg2: ', key)
                        dummyVisit = 1
                        break 
                    else:
                        print('umg3')
                        dummyVisit = 0
                        continue
                else:
                    continue
                break
    
            #N. Physical custody   
            physicalCustodyKey = [['boende'],['bo tillsammans'],['ska','bo']]        
            for term1 in [childNameFirst, 'barn']:
                for term2 in physicalCustodyKey:
                    if term1 in findTerms(term2, rulingOnly) and plaintNameFirst in findTerms(term2, rulingOnly) and not any([x in findTerms(term2, rulingOnly) for x in excludePhysical]):
                        dummyPhys = 1
                        print("phsical custody 1: ", term2)
                        break
                    elif term1 in findTerms(term2, rulingOnly) and defNameFirst in findTerms(term2, rulingOnly) and not any([x in findTerms(term2, rulingOnly) for x in excludePhysical]):
                        dummyPhys = 2
                        print("phsical custody 2: ", term2)
                        break
                    else:
                        dummyPhys = 0
                else:
                    continue
                break
            
            #Corrections
            if childNameFirst == 'not found' or findTerms(['bilaga', 'sidorna'], rulingOnly):
                dummyPhys = 999
                dummyVisit = 999
                print("phsical custody 1")
            
            #Alimony
            if findTerms(['underhåll'], rulingOnly) and not any([x in findTerms(['underhåll'], rulingOnly) for x in rejectKey]):
                dummyAlimon = 1
            elif findTerms(['bilaga', 'sidorna'],  rulingOnly):
                dummyAlimon = 999                    
            else:
                dummyAlimon = 0 
            
            #Custody agreement
            agreementKey = ['samförståndslösning',  'överens ', 'medger', 'medgett', ' ense ', 'överenskommelse',
                            'medgivande', 'överenskommit', 'över- ens ']
            agreementAdd = ['framgår' ,'enlighet' ,'följer','fastställa', 'bäst', 'vård', 'fastställa', 'yrkande']
            noVard = ['umgänge', 'boende', ' bo ']
            agreementExclude = ['med sin', 'bestr', ' talan ', 'avgjord', 'inte behöver', 'alla frågor som rör barnen'] 
            
            """
            Notes for agreementExclude:
            - potentially include god man and gode mannen, misses cases where the defendant agrees to the ruling through their god man eg Sundsvalls TR T 2022-19 
            - included talan for this case: Eftersom talan har medgetts och då det får anses vara bäst för barnet, ska JCI anförtros ensam vårdnad om sonen.
            - included avgjord for this case: Vid muntlig förberedelse den 26 april 2018 beslutade tingsrätten, i enlighet med en överenskommelse som parterna träffade, att till dess att frågan avgjordes genom dom eller annat beslutades skulle vårdnaden om barnen vara fortsatt gemensam 
            - alla frågor som rör barnen for standard phrasing that expresses this (alternative: föräldrar + inte): Gemensam vårdnad förutsätter inte att föräldrarna är överens om alla frågor som rör barnen, men de måste kunna hantera sina delade meningar på ett sätt som inte drabbar barnen// Joint custody does not require parents to agree on all matters concerning the children, but they must be able to manage their disagreements in a way that is not detrimental to the children
            """
        
            #potentially include god man and gode mannen, misses cases where the defendant agrees to the ruling through their god man eg Sundsvalls TR T 2022-19 
            sentences_domskal = domskal.split('.')
            sentences_all = fullText.split('.')
            
            for sentence in sentences_domskal:
                if all(any(term in sentence for term in lst) for lst in (agreementKey, agreementAdd)) and not any([x in sentence for x in agreementExclude]) and not any([x in sentence for x in noVard]) and dummyOut != 0:
                    dummyAgree = 1
                    for p in agreementKey:
                        for j in agreementAdd:
                            if p in sentence and j in sentence:
                                print('Agreement: ', i, j)
                    break
                else: 
                    dummyAgree = 0
            if dummyAgree == 0:
                if findTerms(['gemensam', 'ansökan', 'yrkat'], domskal):
                    # they have applied jointly for
                    dummyAgree = 1
            
            #Any agreement
            for sentence in sentences_all:
                if all(any(term in sentence for term in lst) for lst in (agreementKey, agreementAdd)) and not any([x in sentence for x in agreementExclude]):
                        dummyAgreeAny = 1
                        
                        for p in agreementKey:
                            for j in agreementAdd:
                                if p in sentence and j in sentence:
                                    print('Agreement Any: ', ' i: ', i, ' j: ', j)
                            
                        break
                else: 
                    dummyAgreeAny = 0
            
            #Correction of agreement
            if dummyAgree == 1 and len(domskal.split(' ')) > 700 or dummyAgree == 1 and pageCount > 10:
                dummyAgree = 0                
                    
            #Joint application
            jointApp = 1 if 'sökande' in firstPage.lower() and 'motpart' not in firstPage.lower() and dummyOut != 0 else 0
    
            #Fast information (snabbupplysningar)
            if termLoop(socialOffice, findTerms(['yttra'], fullText)):
                print("snabbupply 1")
                dummyInfo = 1
            elif '6 kap. 20 § andra stycket föräldrabalken' in fullText:
                dummyInfo = 1 
                print("snabbupply 3 ")
            else:
                dummyInfo = termLoop(fastInfoKey, fullText)
                print("snabbupply 4" )
                  
            #Cooperation talks
            for term in corpTalksKey:
                sentence = firstOccurance([term], fullText)
                if term in fullText and not any([x in sentence for x in rejectKey]):
                    dummyCoop = 1
                    break
                else:
                    dummyCoop = 0
                    continue
            #Investigation
            dummyInvest = termLoop(investigationKey, fullText)
            if dummyInvest == 0:
                if findTerms([' utred', 'ingsrätt'], fullTextOG) and not any([x in findTerms([' utred'], fullTextOG) for x in rejectKey]) and not findTerms(['saknas', 'möjlighet', ' utred'], fullText): #search for tingsratt or Tingsratt in fullTextOG to not get the TINGSRATT from header
                    print('invest1')
                    dummyInvest = 1
                elif any([x in findTerms([' utred'], fullText) for x in socialOffice]) and not any([x in findTerms([' utred'], fullTextOG) for x in rejectKey]) and not findTerms(['saknas', 'möjlighet', ' utred'], fullText):
                    print('invest2')
                    dummyInvest = 1
                elif "11 kap. 1 § socialtjänstlagen" in fullText:
                    print('invest3')
                    dummyInvest = 1
                else:
                    for term in investigationHelper:
                        if term in findTerms([' utred'], fullText) and not any([x in findTerms([' utred'], fullTextOG) for x in rejectKey]):
                            print('invest4: ', term)
                            dummyInvest = 1
                            break
                        else:
                            dummyInvest = 0
                            continue
            if findTerms(['utred','enligt','11','kap'], fullText):
                dummyInvest = 0
            
            #Main hearing 
            for term in mainHearingKey:
                if findTerms([term], fullText) and 'utan' not in findTerms([term], fullText) and ' ingen' not in findTerms([term], fullText):
                    print('mainhear1: ', term)
                    dummyMainHear = 1
                    break
                else:
                    dummyMainHear = 0
                    continue
            
            #Divorce dummy
            if dummyOut == 0 and 'äktenskaps' in rulingOnly: #potentially also include mellan, used äktenskaps to minimize false 0 because of misspelled äktenskapsskillnad
                dummyDivorce = 1
                dummyVisit = 0
                dummyPhys = 0
            else:
                dummyDivorce = 0
            
            #Name of judge
            try:
                judgeName = ((searchLoop(judgeSearch, lastPageFormatted, 1, ['telefon','telefax', 'svarande'])).split('\n'))[0]
                judgeName = judgeName.lower()
                judgeName = judgeName.strip()
            except:
                judgeName = 'Not found'
            
            #Flag cases
            flag = []
            livingTerms = [' bo ', 'boende']
            if termLoop(socialOffice, findTerms(['uppgett'], fullText)):
                flag.append('fastinfo')
            if defNameFirst in childNameFull.lower() or plaintNameFirst in childNameFull.lower():
                flag.append('agreement, outcome, physical_custody')
            for term in livingTerms:
                if any([x in findTerms([term], rulingOnly) for x in excludePhysical]):
                    flag.append('physical_custody')
                if term in rulingOnly and dummyPhys == 0 and not any([x in findTerms([term], rulingOnly) for x in excludePhysical]):
                    flag.append('physical_custody')
            for term in investigationHelper:
                if term in findTerms([' utred'], fullText):
                    flag.append('investigation')
                    break
            if svGodMan == 1 and not findTerms([defNameFirst, 'genom'], findTerms(['sin', 'gode man'], fullText)):
                flag.append('defendant_unreachable')
            if strangePartyLabel == 1:
                flag.append('party_labelling')
            if dummyVisit == 0 and dummyPhys == 0 and dummyAlimon == 0 and dummyOut != 0 and dummyAgreeAny == 1 and dummyAgree == 0:
                flag.append('agreement_legalcustody')
    
            #Print controls
            print('\nKEY FACTS')
            print("Child first name: "+childNameFirst)
            print("Defendant first name: "+defNameFirst)
            print("Plaint first name: "+plaintNameFirst)
            print('Defendant adress: '+ cityString)
            print('Defendant city string: ' + cityString)
            print('\n')
            
            print('Text: ', rulingOnly) #(lastPageFormatted).split(".")
            print('\n')
            
            #Fill dataframe with search results
            i = ''.join(i.split())
            data['child_id'].append(i)
            data['file_path'].append(file)
            data['page_count'].append(pageCount)
            data['correction_firstpage'].append(dummyRat)
            data['case_no'].append(caseNo)
            data['judge'].append(judgeName)
            data['court'].append(courtName)
            data['date'].append(date)
            data['deldom'].append(dummyDel)
            data['divorce_only'].append(dummyDivorce)
            data['joint_application_custody'].append(jointApp)
            data['plaintiff_id'].append(plaintNo) 
            data['defendant_id'].append(defNo)   
            data['defendant_address_secret'].append(dummyDefSecret)  
            data['plaintiff_address_secret'].append(dummyPlaintSecret)  
            data['plaintiff_lawyer'].append(dummyLawyerPlaint)
            data['defendant_lawyer'].append(defOmbud)
            data['defendant_abroad'].append(dummyAbroad)
            data['defendant_unreachable'].append(dummyUnreach)
            data['outcome'].append(dummyOut)   
            data['visitation'].append(dummyVisit)
            data['physical_custody'].append(dummyPhys)
            data['alimony'].append(dummyAlimon)                
            data['agreement_legalcustody'].append(dummyAgree)    
            data['agreement_any'].append(dummyAgreeAny)  
            data['fastinfo'].append(dummyInfo)          
            data['cooperation_talks'].append(dummyCoop)
            data['investigation'].append(dummyInvest)
            data['separation_year'].append(dummySeparate)
            data['mainhearing'].append(dummyMainHear)
            data['flag'].append(flag)
    except:
        data['child_id'].append('error')
        data['file_path'].append(file)
        data['page_count'].append('error')
        data['correction_firstpage'].append('error')
        data['case_no'].append('error')
        data['judge'].append('error')
        data['court'].append('error')
        data['date'].append('error')
        data['deldom'].append('error')
        data['divorce_only'].append('error')
        data['joint_application_custody'].append('error')
        data['plaintiff_id'].append('error') 
        data['defendant_id'].append('error')   
        data['defendant_address_secret'].append('error')  
        data['plaintiff_address_secret'].append('error')  
        data['plaintiff_lawyer'].append('error')
        data['defendant_lawyer'].append('error')
        data['defendant_abroad'].append('error')
        data['defendant_unreachable'].append('error')
        data['outcome'].append('error')   
        data['visitation'].append('error')
        data['physical_custody'].append('error')
        data['alimony'].append('error')                
        data['agreement_legalcustody'].append('error')    
        data['agreement_any'].append('error')  
        data['fastinfo'].append('error')          
        data['cooperation_talks'].append('error')
        data['investigation'].append('error')
        data['separation_year'].append('error')
        data['mainhearing'].append('error')
        data['flag'].append('error')

#Dataframe created from dictionary
df = pd.DataFrame(data)
with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    print(df)

#Runtime    
print("\nRuntime: \n" + "--- %s seconds ---" % (time.time() - start_time))

#Save to csv
df.to_csv(output_path, sep = ',', encoding='utf-8-sig')

print("---Saved as CSV---")
print('Unreadable: ')
print(noUnreadable)




