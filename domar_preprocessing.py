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

import re, glob, io, pdfminer, pandas as pd

from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.converter import PDFPageAggregator

#Runtime
import time
start_time = time.time()

#Define Paths
pdf_dir = 'P:/2020/14/Kodning/Test-round-4/files'
output_path = 'P:/2020/14/Kodning/Test-round-4/custody_data_test4_v03.csv'

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

#General functions
def splitParts(txt, seps):
    default_sep = seps[0]
    for sep in seps[1:]:
        txt = txt.replace(sep, default_sep)
    return [i.strip() for i in txt.split(default_sep)]

#Text search
def findTerms(stringlist, part):
    sentenceRes = []
    split = re.split('(?=[.]{1}\s[A-ZÅÐÄÖÉÜ])', part)
    for sentence in split:
        sentence = sentence.lower() + '.'
        if all([x in sentence for x in stringlist]):
            sentenceRes.append(sentence)
    sentenceString = '.'.join(sentenceRes)
    return sentenceString

def firstOccurance(stringlist, part):
    sentenceRes = []
    split = re.split('(?=[.]{1}\s[A-ZÅÐÄÖÉÜ1-9])', part)
    for sentence in split:
        sentence = sentence.lower()
        if all([x in sentence for x in stringlist]):
            sentenceRes.append(sentence)
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

def city(string,m):
    stringList = (string.strip()).split(" ")
    return stringList[-m]

#Variables
def party_id(party_stringOG, string2, part2, g2):
    if ',' in party_stringOG:
        full = (party_stringOG.split(",")[0]).lower()
    else:
        full = (party_stringOG.split("\n")[1]).lower()
    first = [x.strip('\n') for x in re.split('-|[(]|[)|\s]', full)[:-1]]
    first = [x for x in first if x] #delete empty strings from list
    try:
        number = ''.join(searchKey(string2, part2, g2).split())
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

def party_strings(): 
    sectionsFirstPage = list(filter(None, splitParts(headerFormatted, boldWordsFirstPage)))
    kärandeStringOG = ' '.join(sectionsFirstPage[0].split('\n'))
    svarandeStringOG = ' '.join(sectionsFirstPage[1].split('\n'))
    strangePartyLabel = 1
    return kärandeStringOG, svarandeStringOG, strangePartyLabel

def childNos(part, caseyear):
    result = []
    childNo =[]
    childNoNoisy = re.findall('\d{6,8}\s?.\s?\d{3,4}', part)
    for k in childNoNoisy:
        k = k.replace(' ','')
        clean = [x for x in re.split('(\D)',k) if x]            
        clean = ''.join(clean)
        childNo.append(clean)
    childNo = set(childNo)
    for i in childNo:
        if len(re.split('\D', i)[0]) == 8:
            yearChild = i[:4]
            age = int(caseyear) - int(yearChild)
        else:
            yearChild = i[:2]
            age = int(caseyear[2:]) - int(yearChild)
        if age < 18: 
            result.append(i)
    return result

"""
with open('P:/2020/14/Kodning/all_files/filepaths1.txt','r') as f:
    pdf_files = f.read().splitlines() 
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
allLetters = '[A-ZÅÐÄÖÉÜÆØÞ][a-zåäáïüóöéæøßþîčćžđšžůúýëçâêè]'

dateSearch = {
    '1' : 'dom\s+(\d*-\d*-\d*)',
    '2' : 'dom\s+sid\s*1\s*[(][0-9]*[)]\s*(\d*-\d*-\d*)',
    '3' : '(\d{4}-\d{2}-\d{2})'
    }

judgeSearch = {
    '1': '\n\s*\n\s*((' + allLetters + '+\s+){2,4})\n\s*\n', #normal names
    '2': '\n\s*\n\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s+)\n\s*\n', #first name hyphenated
    '3': '\n\s*\n\s*(' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+\s+)\n\s*\n', #last name hypthenated
    '4': '\n\s*\n\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s*-\s*' + allLetters + '+\s+)\n\s*\n', #first and last name hyphenated
    '5': '\n\s*\n\s*(' + allLetters + '+\s' + capLetters + '\s' + allLetters + '+\s+)\n\s*\n', #name with initial as second name
    '6': '\n\s*\n\s*(' + capLetters + '\s' + capLetters + '\s' + allLetters + '+\s+)\n\s*\n', #first and second name as initial
    #if there is a note in the line following the judge's name
    '7': '\n\s*\n\s*((' + allLetters + '+\s+){2,4})\n', #normal names
    '8': '\n\s*\n\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s+)\n', #first name hyphenated
    '9': '\n\s*\n\s*(' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+\s+)\n', #last name hypthenated
    '10': '\n\s*\n\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s*-\s*' + allLetters + '+\s+)\n', #first and last name hyphenated
    '11': '\n\s*\n\s*(' + allLetters + '+\s' + capLetters + 's\s' + allLetters + '+\s+)\n', #name with initial as second name
    '12': '\n\s*\n\s*(' + capLetters + '\s' + capLetters + '\s' + allLetters + '+\s+)\n', #name with initial as second name
    #For documents where judge didnt sign
    '13': 'rådmannen\s*((' + allLetters + '+\s+){2,4})',
    '14': 'rådmannen\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s+)', #first name hyphenated
    '15': 'rådmannen\s*(' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+\s+)', #last name hypthenated
    '16': 'rådmannen\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s*-\s*' + allLetters + '+\s+)', #first and last name hyphenated
    '17': 'rådmannen\s*(' + allLetters + '+\s' + capLetters + '\s' + allLetters + '+\s+)', #name with initial as second name
    '18': 'rådmannen\s*(' + capLetters + '\s' + capLetters + '\s' + allLetters + '+\s+)', #name with initial as second name  
    '19': 'tingsfiskalen\s*(([' + allLetters + '+\s+){2,4})',
    '20': 'tingsfiskalen\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s+)', #first name hyphenated
    '21': 'tingsfiskalen\s*(' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+\s+)', #last name hypthenated
    '22': 'tingsfiskalen\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s*-\s*' + allLetters + '+\s+)', #first and last name hyphenated
    '23': 'tingsfiskalen\s*(' + allLetters + '+\s' + capLetters + '\s' + allLetters + '+\s+)', #name with initial as second name
    '24': 'tingsfiskalen\s*(' + capLetters + '\s' + capLetters + '\s' + allLetters + '+\s+)', #name with initial as second name
    #when judge's name ends with .
    '25': '\n\s*\n\s*((' + allLetters + '+\s+){1,3}' + allLetters + '+).\s*\n\n', #normal names
    '26': '\n\s*\n\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+).\s*\n', #first name hyphenated
    '27': '\n\s*\n\s*(' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+).\s*\n', #last name hypthenated
    '28': '\n\s*\n\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s*-\s*' + allLetters + ').\s*\n', #first and last name hyphenated
    '29': '\n\s*\n\s*(' + allLetters + '+\s' + capLetters + '\s' + allLetters + '+).\s*\n', #name with initial as second name
    '30': '\n\s*\n\s*(' + capLetters + '\s' + capLetters + '\s' + allLetters + '+\s+).\s*\n', #name with initial as second name
    #Only one new line before judge's name
    '31': '\n\s*((' + allLetters + '+\s+){2,4})\n\s*\n', #normal names
    '32': '\n\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s+)\n\s*\n', #first name hyphenated
    '33': '\n\s*(' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+\s+)\n\s*\n', #last name hypthenated
    '34': '\n\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s*-\s*' + allLetters + '+\s+)\n\s*\n', #first and last name hyphenated
    '35': '\n\s*(' + allLetters + '+\s' + capLetters + '\s' + allLetters + '+\s+)\n\s*\n', #name with initial as second name
    '36': '\n\s*(' + capLetters + '\s' + capLetters + '\s' + allLetters + '+\s+)\n\s*\n' #name with initial as second name
    }
judgeSearchNoisy = {
    '1': '\n\s*\n(.*)'
    }

#Define keys for simple word search
fastInfoKey = ['snabbupplysning', 'upplysning', 'snabbyttrande']
corpTalksKey = ['samarbetssamtal','medlingssamtal',' medling', ' medlare']
mainHearingKey = ['huvudförhandling' , ' rättegång ' , 'sakframställning' , ' förhör ', 'tingsrättens förhandling','huvud- förhandling' ]
lawyerKey = ["ombud:", 'god man:',  'advokat:', "ombud", 'god man',  'advokat']
investigationKey = ['vårdnadsutredning','boendeutredning','umgängesutredning']
allOutcomes = ["vård", "umgänge", "boende"]

socialOffice = ['social', 'nämnden', 'kommun', 'familjerätt']
umgangeKey = ['umgänge', 'umgås']
separationKey = ['separera', 'relationen tog slut', 'förhållandet tog slut', 'relationen avslutades', 'förhållandet avslutades', 'skildes', 'skiljas', 'skiljer' ]
countries = ['saknas', 'u.s.a.', 'u.s.a', 'usa', 'afghanistan', 'albanien', 'algeriet', 'andorra', 'angola', 'antigua och barbuda', 'argentina', 'armenien', 'australien', 'azerbajdzjan', 'bahamas', 'bahrain', 'bangladesh', 'barbados', 'belgien', 'belize', 'benin', 'bhutan', 'bolivia', 'bosnien och hercegovina', 'botswana', 'brasilien', 'brunei', 'bulgarien', 'burkina faso', 'burundi', 'centralafrikanska republiken', 'chile', 'colombia', 'costa rica', 'cypern', 'danmark', 'djibouti', 'dominica', 'dominikanska republiken', 'ecuador', 'egypten', 'ekvatorialguinea', 'elfenbenskusten', 'el salvador', 'eritrea', 'estland', 'etiopien', 'fiji', 'filippinerna', 'finland', 'frankrike', 'förenade arabemiraten', 'gabon', 'gambia', 'georgien', 'ghana', 'grekland', 'grenada', 'guatemala', 'guinea', 'guinea-bissau', 'guyana', 'haiti', 'honduras', 'indien', 'indonesien', 'irak', 'iran', 'irland', 'island', 'israel', 'italien', 'jamaica', 'japan', 'jemen', 'jordanien', 'kambodja', 'kamerun', 'kanada', 'kap verde', 'kazakstan', 'kenya', 'kina', 'kirgizistan', 'kiribati', 'komorerna', 'kongo-brazzaville', 'kongo-kinshasa', 'kroatien', 'kuba', 'kuwait', 'laos', 'lesotho', 'lettland', 'libanon', 'liberia', 'libyen', 'liechtenstein', 'litauen', 'luxemburg', 'madagaskar', 'malawi', 'malaysia', 'maldiverna', 'mali', 'malta', 'marocko', 'marshallöarna', 'mauretanien', 'mauritius', 'mexiko', 'mikronesiska federationen', 'moçambique', 'moldavien', 'monaco', 'montenegro', 'mongoliet', 'myanmar', 'namibia', 'nauru', 'nederländerna', 'nepal', 'nicaragua', 'niger', 'nigeria', 'nordkorea', 'nordmakedonien', 'norge', 'nya zeeland', 'oman', 'pakistan', 'palau', 'panama', 'papua nya guinea', 'paraguay', 'peru', 'polen', 'portugal', 'qatar', 'rumänien', 'rwanda', 'ryssland', 'saint kitts och nevis', 'saint lucia', 'saint vincent och grenadinerna', 'salo-monöarna', 'samoa', 'san marino', 'são tomé och príncipe', 'saudiarabien', 'schweiz', 'senegal', 'seychellerna', 'serbien', 'sierra leone', 'singapore', 'slovakien', 'slovenien', 'somalia', 'spanien', 'sri lanka', 'storbritannien', 'sudan', 'surinam', 'sverige', 'swaziland', 'sydafrika', 'sydkorea', 'sydsudan', 'syrien', 'tadzjikistan', 'tanzania', 'tchad', 'thailand', 'tjeckien', 'togo', 'tonga', 'trinidad och tobago', 'tunisien', 'turkiet', 'turkmenistan', 'tuvalu', 'tyskland', 'uganda', 'ukraina', 'ungern', 'uruguay', 'usa', 'uzbekistan', 'vanuatu', 'vatikanstaten', 'venezuela', 'vietnam', 'vitryssland', 'zambia', 'zimbabwe', 'österrike', 'östtimor']

excludePhysical = ['jämna' , 'växelvis', 'skyddat']
rejectKey = ['avskriv',' ogilla','utan bifall','avslå',' inte ','skrivs', 'kvarstå', ' inga '] 
rejectInvest = ['avskriv',' ogilla','utan bifall','avslå',' inte ',' inga ', ' utöva '] 
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
        appendixPage = [k for k, item in enumerate(pages_text) if re.search(appendixStart, item)]
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
            rulingStringFormatted = ''.join(re.split('[A-ZÅÄÖÜ]{4,}\s*\n*TINGSRÄTT',rulingStringFormatted))
        except:
            rulingStringFormatted = ''.join(re.split('\n\n[A-ZÅÄÖÜ]{1}[a-zåäüö]{3,]\s*\n*Tingsrätt',rulingStringFormatted))
        rulingStringFormatted = ''.join(re.split('DELDOM|DOM',rulingStringFormatted))
        try:
            rulingOnlyOG1 = re.split('\n\s*\n\s*[A-ZÅÄÖ., ]{3,}\s*\n', rulingStringFormatted)[0]
            rulingOnlyOG1 = re.sub('\s*-\s*','-',rulingOnlyOG1)
            rulingOnlyOG = ' '.join(''.join(rulingOnlyOG1).split())
        except AttributeError:
            rulingOnlyOG = ' '.join(''.join(re.split('(YRKANDEN|Yrkanden)', rulingStringFormatted)[0].lower() ).split())
            rulingOnlyOG = re.sub('\s*-\s*','-',rulingOnlyOG)
        rulingOnly = rulingOnlyOG.lower() 
    
        #Get domskäl or yrkanden
        try:
            domStart = re.split('DOMSKÄL|Domskäl', fullTextOG)[1]
        except IndexError:
            try:
                domStart = re.split('BEDÖMNING|Bedömning', fullTextOG)[1]
            except IndexError:
                try:
                    domStart = re.split('Yrkanden |Parternas Begäran M.M.|Yrkande M.M.|YRKANDEN |YRKANDE M.M.|PARTERNAS BEGÄRAN ', fullTextOG)[1]
                except IndexError:
                    try:
                        domStart = re.split('\nSkäl\s*\n', rulingStringFormatted)[1]
                    except IndexError:
                        domStart = re.split('(_|-){10,40}\s*', rulingStringFormatted)[1]
        domskalOG = re.split('överklag|Överklag|ÖVERKLAG', domStart)[0]
        domskal = domskalOG.lower()
                
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
                        svarandeStringOG, kärandeStringOG = 'not found, not found', 'not found, not found'
        #print('PARTY9: ',svarandeStringOG)
        svarandeString = svarandeStringOG.lower()
        kärandeString = kärandeStringOG.lower()
        
        #Variables that are constant for all children in court doc
        date = searchLoop(dateSearch, header, 1, [])    
        year = date[:4]
        
        #List of children's numbers
        childNoRes = childNos(rulingOnly, year)  
        if not childNoRes:
            childNoRes = childNos(fullText, year) 
            if not childNoRes:       
                childNoRes = ['not found']  
            
        #Loop to create dictionary with one row per child
        for i in childNoRes:
            #Variables that are constant for all children in court doc       
            caseNo = ''.join((searchKey(searchCaseNo, header, 2)).split())
            courtName = file.split('/')[4]
            dummyDel = 1 if 'deldom' in header else 0
            plaintNameFull, plaintNameFirst, plaintNo = party_id(kärandeStringOG, idNo, kärandeString, 2)
            defNameFull, defNameFirst, defNo = party_id(svarandeStringOG, idNo, svarandeString, 2)   
            dummyLawyerPlaint = 1 if 'ombud' in kärandeString or "god man" in kärandeString or "advokat" in kärandeString else 0
            
            
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
                try:
                    b = []
                    a = re.split('(?=[.]{1}\s[A-ZÅÐÄÖÉÜ])..', rulingOnlyOG)
                    for sentence in a:
                        if all([x in sentence for x in ['vård']]):
                            b.append(sentence)
                    sentenceString = '.'.join(b)
                    wordList = sentenceString.split(' ')[1:]
                    for word in wordList:
                        if word[0].isupper() and not any([x in word.lower() for x in defNameFull.split()]) and word[0].isupper() and not any([x in word.lower() for x in plaintNameFull.split()]):
                            childNameFirst = childNameFull = word
                            break
                    i = childNameFirst.lower() if not i else i
                except:
                    childNameFull = 'not found'
                    childNameFirst = 'not found'
                if childNameFirst is None:
                    childNameFull = 'not found'
                    childNameFirst = 'not found'
            childNameFirst = childNameFirst.lower()
            
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
                    svarandeString = svarandeString.split('\nsaken ')[0] if '\nsaken ' in svarandeString else svarandeString
                    cityString = ''.join(city(svarandeString, 1))
                    svGodMan = 0
                    continue
    
            #Defendant abroad            
            if any([x in cityString for x in countries]) or 'okänd' in svarandeString:
                dummyAbroad = 1
                print('abroad 1')
            elif cityString.isdecimal():
                dummyAbroad = 1
                print('abroad 2')
            elif any(x in findTerms(['befinn','inte', 'sverige'], fullTextOG) for x in defNameFirst):
                dummyAbroad = 1
                print('abroad 3')
            elif findTerms(['befinn', 'sig','utomlands'], fullTextOG):
                dummyAbroad = 1 #didnt include defNameFirst because sv might be referred to by Han
                print('abroad 4')
            elif any([x in findTerms(['befinn', 'sig'], fullTextOG) for x in countries]):
                dummyAbroad = 1 #didnt include defNameFirst because sv might be referred to by Han
                print('abroad 5')    
            elif any(x in findTerms(['försvunnen'], fullTextOG) for x in defNameFirst):
                dummyAbroad = 1 
                print('abroad 6')
            elif any(x in findTerms(['bortavarande', 'varaktigt'], fullTextOG) for x in defNameFirst):
                dummyAbroad = 1 
                print('abroad 7')
            elif any(x in findTerms([' bor ', 'i'], fullTextOG) for x in defNameFirst) and any(x in findTerms([' bor ', 'i'], fullTextOG) for x in countries):
                dummyAbroad = 1 
                print('abroad 8')
            else:
                dummyAbroad = 0
            
            #Secret address dummy
            dummyDefSecret = 1 if 'sekretess' in svarandeString else 0
            dummyPlaintSecret = 1 if 'sekretess' in kärandeString else 0
    
            #Defendant unreachable 
            for name in defNameFirst:
                unreachKey = [['okontaktbar'],['förordnat god man', name],['varken kan bestrida eller medge'],
                              ['någon kontakt', 'huvudman'],['någon kontakt', name],['okän', 'befinn',name],
                              [name, 'avsaknad',' av ',' instruktioner',' från']]    
                for term in unreachKey:
                    if findTerms(term, fullTextOG):
                        print('Unreach 1: ', term)
                        dummyUnreach = 1
                        found1 = 1
                        break
                    else:
                        dummyUnreach = 0
                        found1 = 0
                        continue
                dummyUnreach = 1 if svGodMan == 1 else dummyUnreach
                print('Unreach 2: ', dummyUnreach)
                noContactKey = ['någon', 'inte']
                reachable = [[name, 'genom', 'sin', 'gode man'],[name, 'kontakt ', 'med']]
                for part in reachable:
                    if found1 == 0 and findTerms(part, fullTextOG) and not any([x in findTerms(part, fullTextOG) for x in noContactKey]):
                        print('Unreach 3: ', part)
                        dummyUnreach = 0
                else:
                    continue
                break
                    
            #Year of Separation of Unmarried Parents
            for term in separationKey:
                if term in fullText:
                    dummySeparate = searchKey('(\d\d\d\d)', findTerms([term], fullTextOG), 0)
                    break
                else:
                    dummySeparate = '-'
                    continue
            #Outcome
            findVardn = findTerms(['vård',i], rulingOnlyOG)
            findVardn = findTerms(['vård'], rulingOnlyOG) if not findVardn else findVardn
            print('FIND VARDN: ', findVardn)
            
            #Dismissed
            if 'käromalet ogillas' in rulingOnly or 'käromålet ogillas' in rulingOnly or findTerms(['avslås', 'vårdn'], rulingOnlyOG) or findTerms([' lämna',' utan ',' bifall'], findVardn) or 'avskriv' in findVardn or findTerms(['lämnas utan bifall', 'talan'], rulingOnlyOG): #"lämnas utan bifall" in findVard because if I search in ruling only it picks up when umgange claims or so are dismissed
                dummyOut = 4  
                print("out4")
            else:
                dummyOut = 999
    
            #No custody ruling
            if dummyOut != 4:
                if 'vård' not in rulingOnly and 'vård' not in firstPage.lower(): 
                    print("out1")
                    dummyOut = 0
                elif any([x in findVardn for x in remindKey]) and 'äktenskaps' in rulingOnly:
                    dummyOut = 0
                    print("out2")
                elif 'vård' not in findTerms([childNameFirst], rulingOnlyOG) and childNameFirst != 'not found':
                    print('out3')
                    dummyOut = 0
                else:
                    dummyOut = 999
                
            #One plaint is dismissed and another installed
            if dummyOut == 4 and findTerms([' ensam', 'gemensam ', 'vårdn'], rulingOnlyOG):
                newRuling = []
                dummyOut = 999
                for part in re.split(',|;',findTerms([' ensam', 'gemensam', 'vård'], rulingOnlyOG)):
                    if not any([x in part for x in rejectKeyOutcome]):
                        newRuling.append(part)
                findVardn = ''.join(newRuling)
            
            anyVardn = not any([x in findVardn for x in rejectKeyOutcome])
                
            #Shared custody 
            if len(childNoRes)> 1:
                sharedCustody = [['ska','tillkomma','tillsammans'],[i,'ska','tillkomma', 'gemensam '], [i,'ska','om','gemensam '],[i,'gemensam ','fortsätt','ska'],[i,'alltjämt','ska','gemensam '],[i,'gemensam ','alltjämt', 'är'],[i,'gemensam ','anförtro'],['gemensamma vård',i],
                                 [i,'ska','tillkomma', 'gemensam.'],[i,'ska','om','gemensam.'],[i,'gemensam.','fortsätt','ska'],[i,'alltjämt','ska','gemensam.'],[i,'gemensam.','alltjämt', 'är'],[i,'gemensam.','anförtro']]
                if dummyOut not in {0,4}: 
                    dummyOut = outcome_search(sharedCustody, findVardn, anyVardn, 1)
                print('Shared1: ', dummyOut)
                
                #Sole custody
                if dummyOut not in {0,1,4}:
                    for name1 in plaintNameFirst:
                        soleCustody = [
                            [i,' ensam', name1],[i,'över','flytt', 'till ' + name1],[i, name1,'tillerkänn'],[i, name1,'anförtro'],
                            ['ska','tillkomma', i, name1],[i,name1,' ska ',' om ', ' ha ']]  
                        dummyOut = outcome_search(soleCustody, findVardn, anyVardn, 2) 
                        if dummyOut == 2:
                            break
                        else:
                            continue
    
                if dummyOut not in {0,1,2,4}:
                    for name in defNameFirst:
                        soleCustody = [
                            [i,' ensam', name],[i,'över','flytt', 'till ' + name],[i, name,'tillerkänn'],[i, name,'anförtro'],
                            ['ska','tillkomma', i, name],[i,name,' ska ',' om ', ' ha ']]  
                        dummyOut = outcome_search(soleCustody, findVardn, anyVardn, 3)  
                        if dummyOut == 3:
                            break
                        else:
                            continue
                print('Sole1: ', dummyOut)
                    
            else:
                #Shared custody
                sharedCustody = [['ska','tillkomma','tillsammans'],['ska','tillkomma', 'gemensam '], ['ska','om','gemensam '],['gemensam ','forts','ska'],['alltjämt','ska','gemensam '],['gemensam ','alltjämt', 'är'],['gemensam ','anförtro'],['gemensamma vård'],
                                 ['ska','tillkomma', 'gemensam.'],['ska','om','gemensam.'],['gemensam.','fortsätt','ska'],['alltjämt','ska','gemensam.'],['gemensam.','alltjämt', 'är'],['gemensam.','anförtro']]
                if dummyOut not in {0,4}: 
                    dummyOut = outcome_search(sharedCustody, findVardn, anyVardn, 1)
                print('Shared2: ', dummyOut)
                
                #Sole custody
                if dummyOut not in {0,1,4}:
                    for name1 in plaintNameFirst:
                        soleCustody = [
                            [i,' ensam', name1],[i,'över','flytt', 'till ' + name1],[i, name1,'tillerkänn'],[i, name1,'anförtro'],
                            ['ska','tillkomma', i, name1],[i,name1,' ska ',' om ', ' ha ']]  
                        dummyOut = outcome_search(soleCustody, findVardn, anyVardn, 2)  
                        if dummyOut == 2:
                            break
                        else:
                            continue
                        
                if dummyOut not in {0,1,2,4}:
                    for name in defNameFirst:
                        soleCustody = [
                            [i,' ensam', name],[i,'över','flytt', 'till ' + name],[i, name,'tillerkänn'],[i, name,'anförtro'],
                            ['ska','tillkomma', i, name],[i,name,' ska ',' om ', ' ha ']]  
                        dummyOut = outcome_search(soleCustody, findVardn, anyVardn, 3)  
                        if dummyOut == 3:
                            break
                        else:
                            continue
                print('Sole2: ', dummyOut)
            
            if dummyOut == 999:
                dummyOut = 4 if findTerms(['avskr','vård'], fullTextOG) or findTerms(['skrivs', 'av'], fullTextOG) else dummyOut
            
            #Visitation rights  
            for term in [childNameFirst, 'barn']:
                for key in umgangeKey:
                    if findTerms(['avslås', key], rulingOnlyOG) or findTerms([' lämna',' utan ',' bifall', key], rulingOnlyOG) or findTerms([key, 'avskriv'], rulingOnlyOG): #"lämnas utan bifall" in findVard because if I search in ruling only it picks up when umgange claims or so are dismissed
                        dummyVisit = 4  
                        print("visitation 1")
                        break
                    elif findTerms(['semester', term], rulingOnlyOG) or findTerms(['sommar', term], rulingOnlyOG):
                        print('visitiation 2')
                        dummyVisit = 0
                        break
                    elif firstOccurance([key, term], rulingOnlyOG) and not any([x in firstOccurance([key, term], rulingOnlyOG) for x in rejectKey]):  
                        print('visitation 3: ', key)
                        dummyVisit = 1
                        break 
                    else:
                        print('visitation 4')
                        dummyVisit = 0
                        continue
                else:
                    continue
                break
    
            #N. Physical custody  
            physCust1 = ['boende','bo tillsammans',' bo ',' ska ','bosatt'] 
            if any([x in findTerms([childNameFirst], rulingOnlyOG) for x in physCust1]):
                physicalCustodyKey = [['boende', childNameFirst],['bo tillsammans', childNameFirst],[' ska ',' bo ', childNameFirst],[' ska ','bosatt', childNameFirst]] 
            else:
                physicalCustodyKey = [['boende', 'barn'],['bo tillsammans', 'barn'],[' ska ',' bo ', 'barn'],[' ska ','bosatt', 'barn']]      
            for term2 in physicalCustodyKey:
                print('Physical Custody: ',firstOccurance(term2, rulingOnlyOG))
                if firstOccurance(['avslås'], firstOccurance(term2, rulingOnlyOG)) or firstOccurance([' lämna',' utan ',' bifall'], firstOccurance(term2, rulingOnlyOG)) or firstOccurance(['avskriv'], firstOccurance(term2, rulingOnlyOG)): #"lämnas utan bifall" in findVard because if I search in ruling only it picks up when umgange claims or so are dismissed
                    dummyPhys = 4  
                    print("physical custody 0: ", term2, firstOccurance(term2, rulingOnly))
                    break
                elif firstOccurance(term2, rulingOnlyOG) and any([x in firstOccurance(term2, rulingOnlyOG) for x in plaintNameFirst]) and not any([x in firstOccurance(term2, rulingOnlyOG) for x in excludePhysical]):
                    dummyPhys = 1
                    print("phsical custody 1: ", term2, firstOccurance(term2, rulingOnly))
                    break
                elif firstOccurance(term2, rulingOnlyOG) and any([x in firstOccurance(term2, rulingOnly) for x in defNameFirst]) and not any([x in firstOccurance(term2, rulingOnlyOG) for x in excludePhysical]):
                    dummyPhys = 2
                    print("phsical custody 2: ", term2, firstOccurance(term2, rulingOnlyOG))
                    break
                else:
                    dummyPhys = 0
    
            #Alimony
            if findTerms(['underhåll'], rulingOnlyOG) and not any([x in findTerms(['underhåll'], rulingOnlyOG) for x in rejectKey]):
                dummyAlimon = 1
            elif findTerms(['bilaga', 'sidorna'],  rulingOnlyOG):
                dummyAlimon = 999                    
            else:
                dummyAlimon = 0 
            
            #Custody agreement
            agreementKey = ['samförståndslösning',  'överens ', 'medger', 'medgett', ' ense ', 'överenskommelse',
                            'medgivande', 'överenskommit', 'över- ens ', 'medgivit', 'enats ']
            agreementAdd = ['framgår' ,'följer','fastställa', 'bäst', 'vård', 'fastställa', 'yrkande']
            noVard = ['umgänge', 'boende', ' bo ']
            agreementExclude = ['med sin', 'bestr', ' talan ', 'avgjord', 'inte ', 'alla frågor som rör barnen'] 
            past = ['inledningsvis']
            
            """
            "Defendant har därefter medgivit plaintiff yrkande om ensam vårdnad."
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
                if all(any(term in sentence for term in lst) for lst in (agreementKey, agreementAdd)) and dummyOut not in {0,4}:
                    
                    #Take this out for final code
                    for p in agreementKey:
                        for j in agreementAdd:
                            if p in sentence and j in sentence:
                                print('Agreement: ', p, j, sentence)
                    if not any([x in sentence for x in noVard]) or 'vård' in sentence: #capture sentences (1) that dont refer only to umgange and boende , or (2) referring to vardn, umgange and boende
                        if any([x in sentence for x in past]) and any([x in sentence for x in agreementExclude]):
                            dummyAgree = 1
                            break
                        if not any([x in sentence for x in agreementExclude]) and not any([x in sentence for x in past]): 
                            dummyAgree = 1
                            break
                else:
                    dummyAgree = 0
    
            if dummyAgree == 0:
                if findTerms(['gemensam', 'ansökan', 'yrkat'], domskalOG):
                    # they have applied jointly for
                    dummyAgree = 1
            
            for sentence in sentences_all:
                if all(any(term in sentence for term in lst) for lst in (agreementKey, agreementAdd)) or all(any(term in sentence for term in lst) for lst in (agreementKey, noVard)):
                    
                    #Take this out for final code
                    for p in agreementKey:
                        for j in agreementAdd:
                            if p in sentence and j in sentence:
                                print('Agreement Any: ', p, j, sentence)
                    
                    if any([x in sentence for x in past]) and any([x in sentence for x in agreementExclude]):
                        dummyAgreeAny = 1
                        print('Agree any 1')
                        break
                    if not any([x in sentence for x in agreementExclude]) and not any([x in sentence for x in past]): 
                        dummyAgreeAny = 1
                        print('Agree any 2')
                        break
                else:
                    dummyAgreeAny = 0
    
            print('DUMMYAGREE', dummyAgreeAny)
    
    
            #Joint application
            jointApp = 1 if 'sökande' in firstPage.lower() and 'motpart' not in firstPage.lower() and dummyOut != 0 else 0
    
            #Fast information (snabbupplysningar)
            if any([term in fullText for term in socialOffice]) and findTerms(['yttra', term], fullTextOG) and not any([x in findTerms([term], fullTextOG) for x in rejectKey]): 
                print('fast info 1')
                dummyInfo = 1
            elif '6 kap. 20 § andra stycket föräldrabalken' in fullText:
                dummyInfo = 1 
                print('fast info 2')
            else:
                dummyInfo = 1 if any([term in fullText for term in fastInfoKey]) and not any([x in findTerms([term], fullTextOG) for x in rejectKey]) else 0
                print('fast info 3')
                  
            #Cooperation talks
            for term in corpTalksKey:
                sentence = firstOccurance([term], fullTextOG)
                if term in fullText and not any([x in sentence for x in rejectKey]):
                    dummyCoop = 1
                    print('Cooperation: ', term)
                    break
                else:
                    dummyCoop = 0
                    continue
                
            #Investigation
            dummyInvest = 1 if any([term in fullText for term in investigationKey]) and not any([x in findTerms([term], fullTextOG) for x in rejectInvest]) else 0
            if dummyInvest == 0:
                if findTerms([' utred', 'ingsrätt'], fullTextOG) and not any([x in findTerms([' utred'], fullTextOG) for x in rejectInvest]) and not findTerms(['saknas', 'möjlighet', ' utred'], fullTextOG): #search for tingsratt or Tingsratt in fullTextOG to not get the TINGSRATT from header
                    print('invest1')
                    dummyInvest = 1
                elif any([x in findTerms([' utred'], fullTextOG) for x in socialOffice]) and not any([x in findTerms([' utred'], fullTextOG) for x in rejectInvest]) and not findTerms(['saknas', 'möjlighet', ' utred'], fullTextOG):
                    print('invest2')
                    dummyInvest = 1
                else:
                    for sentence in findTerms([' utred'], fullTextOG).split('.'):
                        if any([x in sentence for x in allOutcomes]) and not any([x in sentence for x in rejectInvest]):
                            dummyInvest = 1
                            print('invest3')
                            break
                        else:
                            dummyInvest = 0
                            continue
            dummyInvest = 0 if "11 kap. 1 § so" in fullText else dummyInvest
            
            #Main hearing 
            rejectMainHearKey = ['skulle ', 'utan', ' ingen']
            for term in mainHearingKey:
                if findTerms([term], fullTextOG) and not any([x in findTerms([term], fullTextOG) for x in rejectMainHearKey]):
                    print('mainhear1: ', term)
                    dummyMainHear = 1
                    break
                else:
                    dummyMainHear = 0
                    continue
    
            #Divorce dummy
            if dummyOut == 0 and 'äktenskaps' in rulingOnly: #potentially also include mellan, used äktenskaps to minimize false 0 because of misspelled äktenskapsskillnad
                dummyDivorce = 1
            else:
                dummyDivorce = 0
    
            #Name of judge
            try:
                judgeName = ((searchLoop(judgeSearch, lastPageFormatted, 1, ['telefon','telefax', 'svarande'])).split('\n'))[0]
                judgeName = judgeName.lower()
                judgeName = judgeName.strip()
            except AttributeError:
                try:
                    print((lastPageFormatted).split("."))
                    lastPageFormatted = re.split('ÖVERKLAG|Överklag|överklag', lastPageFormatted)[-1]
                    judgeName = ((searchLoop(judgeSearchNoisy, lastPageFormatted, 1, ['telefon','telefax', 'svarande', 't'])).split('\n'))[0]
                    judgeName = re.split('\s{4,}|,', judgeName)[0]
                    judgeName = judgeName.lower()
                    judgeName = judgeName.strip().strip('/').strip('|')
                except:
                    judgeName = 'Not found'
            
            #Corrections
            dummyAgree = 0 if dummyAgree == 1 and len(domskal.split(' ')) > 500 or dummyAgree == 1 and pageCount > 10 else dummyAgree                          
            dummyUnreach = 0 if dummyOut == 3 or dummyMainHear == 1 else dummyUnreach
            
            #Flag cases
            #Loose definition
            flag = []
            livingTerms = [' bo ', 'boende']
            if any([x in findTerms(['uppgett'], fullTextOG) for x in socialOffice]):
                flag.append('fastinfo')
            if any([x in childNameFull for x in defNameFirst]) or any([x in childNameFull for x in plaintNameFirst]):
                flag.append('agreement, outcome, physical_custody')
            for term in livingTerms:
                if any([x in findTerms([term], rulingOnlyOG) for x in excludePhysical]):
                    flag.append('physical_custody')
                if term in rulingOnly and dummyPhys == 0 and not any([x in findTerms([term], rulingOnlyOG) for x in excludePhysical]):
                    flag.append('physical_custody')
            for term in allOutcomes:
                if term in findTerms([' utred'], fullTextOG):
                    flag.append('investigation')
                    break
            if svGodMan == 1 and not any([x in findTerms([ 'genom','sin', 'gode man'], fullTextOG) for x in defNameFirst]):
                flag.append('defendant_unreachable')
            if strangePartyLabel == 1:
                flag.append('party_labelling')
            
            #Strict definition
            if childNameFirst == 'not found' or findTerms(['bilaga', 'sidorna'], rulingOnlyOG):
                flag.append('physical_custody')    
                flag.append('visitation')   
            if dummyVisit == 0 and dummyPhys == 0 and dummyAlimon == 0 and dummyOut != 0 and dummyAgreeAny == 1 and dummyAgree == 0:
                flag.append('agreement_legalcustody')
    
            #Print controls
            print('\nKEY FACTS')
            print("Child first name: ", childNameFirst)
            print("Defendant first name: ", defNameFirst)
            print("Plaint first name: ", plaintNameFirst)
            print('Defendant city string: ', cityString)
            print('\n')
            
            print('Text: ', (lastPageFormatted).split(".")) #(lastPageFormatted).split(".")
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




