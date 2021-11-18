# -*- coding: utf-8 -*-
"""
Created on Mon Oct 18 17:50:55 2021

@author: ifau-SteCa


Purpose of the code is to read in all pdfs from a specified folder path, extract information (child ID, case ID, etc.),
save the extracted info as a dictionary and output it as a dataframe/csv file

Note: For uncertain cases a variable is set to 999 (eg. if it is not clear whether the plaintiff or defendant was granted physical custody, Stadigvarande boende = 999)
    
"""

import re, glob, io, pandas as pd

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

#Read in PDFs
pdf_files = glob.glob("%s/*.pdf" % pdf_dir)
print(pdf_files)

#Initialize variables
noOfFiles = 0
noUnreadable = 0
countries = 'okänd  u.s.a. u.s.a usa sekretess afghanistan  albanien  algeriet  andorra  angola  antigua och barbuda  argentina  armenien  australien  azerbajdzjan  bahamas  bahrain  bangladesh  barbados  belgien  belize  benin  bhutan  bolivia  bosnien och hercegovina  botswana  brasilien  brunei  bulgarien  burkina faso  burundi  centralafrikanska republiken  chile  colombia  costa rica  cypern  danmark  djibouti  dominica  dominikanska republiken  ecuador  egypten  ekvatorialguinea  elfenbenskusten  el salvador  eritrea  estland  etiopien  fiji  filippinerna  finland  frankrike  förenade arabemiraten  gabon  gambia  georgien  ghana  grekland  grenada  guatemala  guinea  guinea-bissau  guyana  haiti  honduras  indien  indonesien  irak  iran  irland  island  israel  italien  jamaica  japan  jemen  jordanien  kambodja  kamerun  kanada  kap verde  kazakstan  kenya  kina  kirgizistan  kiribati  komorerna  kongo-brazzaville  kongo-kinshasa  kroatien  kuba  kuwait  laos  lesotho  lettland  libanon  liberia  libyen  liechtenstein  litauen  luxemburg  madagaskar  malawi  malaysia  maldiverna  mali  malta  marocko  marshallöarna  mauretanien  mauritius  mexiko  mikronesiska federationen  moçambique  moldavien  monaco  mon-tenegro  mongoliet  myanmar  namibia  nauru  nederländerna  nepal  nicaragua  niger  nigeria  nordkorea  nordmakedonien  norge  nya zeeland  oman  pakistan  palau  panama  papua nya guinea  paraguay  peru  polen  portugal  qatar  rumänien  rwanda  ryssland  saint kitts och nevis  saint lucia  saint vincent och grenadinerna  salo-monöarna  samoa  san marino  são tomé och príncipe  saudiarabien  schweiz  senegal  seychellerna  serbien  sierra leone  singapore  slovakien  slovenien  somalia  spanien  sri lanka  storbritannien  sudan  surinam  sverige  swaziland  sydafrika  sydkorea  sydsudan  syrien  tadzjikistan  tanzania  tchad  thailand  tjeckien  togo  tonga  trinidad och tobago  tunisien  turkiet  turkmenistan  tuvalu  tyskland  uganda  ukraina  ungern  uruguay  usa  uzbekistan  vanuatu  vatikanstaten  venezuela  vietnam  vitryssland  zambia  zimbabwe  österrike  östtimor  '
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
fastInfoKey = ['snabbupplysning', 'upplysning', 'upplysningar', 'yttrande']
corpTalksKey = ['samarbetssamtal','medlingssamtal','medling', 'medlare']
mainHearingKey = ['huvudförhandling' , 'rättegång' , 'sakframställning' , 'förhör' ]
lawyerKey = ["ombud:", 'god man:',  'advokat:']
investigationKey = ['vårdnadsutredning','boendeutredning','umgängesutredning']
agreementKey = ['samförståndslösning',  'överenskommelse', 'överens']
agreementAdd = ['parterna' ,'framgår' ,'enlighet' ,'följer','fastställa', 'kommit','barnets','bästa']

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
    
    #Prepare splitting the text into different parts and extracting only the ruling
    courtNameCaps = searchKey('([A-ZÅÄÖ]{3,})\s*TINGSRÄTT', fullTextOG, 1)
    excludeFromSplit = ['DOMSLUT','TINGSRÄTT', 'DOM', courtNameCaps]
    splitTextOG = re.split('_{10,40}', fullTextOG)                                                     
    headerOG = re.split('_{10,40}', firstPage)[0]   
    header = headerOG.lower()    
    appendixPage = [i for i, item in enumerate(pages_text) if re.search(appendixStart, item)]
    if not appendixPage:
        appendixPageNo = len(pages_text)
    else:
        appendixPageNo = appendixPage[0]
    lastPageFormatted = '.'.join((pages_text_formatted[appendixPageNo-1]).split(".")) + '.'.join((pages_text_formatted[appendixPageNo-2]).split("."))
    lastPageFormatted1 = (pages_text_formatted[appendixPageNo-1]).split(".")
    lastPageOG = pages_text[appendixPageNo-1]
    lastPage = lastPageOG.lower()                       
    fullTextOG = (re.split(appendixStart, fullTextOG)[0])  
    fullText = fullTextOG.lower()
    rulingString = ''.join(re.split('_{10,40}',fullTextOG)[1:])
    headings = re.findall(nameCaps, rulingString)
    splitBackground = [item for item in headings if item not in excludeFromSplit][0]
    rulingOnly = (re.split(splitBackground, rulingString)[0]).lower()
    
    #Extract the plaintiff's and defendant's addresses
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
        try:
            childNameKey = ('(([A-Z]\w+ )+([A-Z]\w+))[,]?[)]?\s*' + i )
            childNameFirst = searchKey(childNameKey, fullTextOG, 2).lower()
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
                defOmbud = 1 
                defAddress = re.split(term, svarandeString)[0]
                cityString = ''.join(city(defAddress, 1))
                break
            else:
                defOmbud = 0
                cityString = ''.join(city(svarandeString, 1))
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

        if 'okontaktbar' in fullText:
            if svNameFirst in findSentence('förordnat god man', fullText):
                dummyUnreach = 1
            else:
                dummyUnreach = 0
        elif svUnreach1 is not None or svUnreach2 is not None:
            dummyUnreach = 1
        elif 'förordnat god man' in fullText:
            if svNameFirst in findSentence('förordnat god man', fullText):
                dummyUnreach = 1
            else:
                dummyUnreach = 0
        elif 'varken kan bestrida eller medge' in fullText:
            dummyUnreach = 1
        elif 'inte fått någon kontakt' in fullText:
            if 'huvudman' in findSentence('någon kontakt', fullText) or svNameFirst in findSentence('någon kontakt', fullText):
                dummyUnreach = 1
            else:
                dummyUnreach = 999
        elif cityString == 'okänd': #CHECK ACCURACY OF THIS 
            dummyUnreach = 1
        else:
            dummyUnreach = 0
        data['Sv okontaktbar'].append(dummyUnreach)
        
        #Outcome
        findGemensam = findSentence('gemensam', rulingOnly)
        vardnInGemensam = 'vårdn' in findGemensam
        findEnsam = findSentence('ensam', rulingOnly)
        findVardn = findSentence('vårdn', rulingOnly)
        transferToDef = 'till ' + svNameFirst
        transferToPlaint = 'till ' + plaintNameFirst
        vardnInRuling = 'vårdn' in rulingOnly
                    
        if 'vårdn' not in rulingOnly or vardnInRuling and 'påminn' in findVardn or vardnInRuling and 'erinrar' in findVardn:
            #No custody ruling in this court record
            dummyOut = 0
        elif 'ska' in findGemensam and 'om' in findGemensam and vardnInGemensam:
            dummyOut = 1
        elif 'vårdn' in rulingOnly and 'fortsätt' in findGemensam and 'ska' in findGemensam:
            dummyOut = 1
        elif vardnInGemensam and 'alltjämt ska' in findGemensam:
            dummyOut = 1
        elif vardnInGemensam and'ska alltjämt' in rulingOnly:
            dummyOut = 1
        elif vardnInGemensam and 'skall tillkomma' in rulingOnly: 
            dummyOut = 1
        elif 'vårdn' in findEnsam and plaintNameFirst in findEnsam and 'utan' not in findEnsam:
            dummyOut = 2
        elif 'vårdn' in findEnsam and svNameFirst in findEnsam and 'utan' not in findEnsam:
            dummyOut = 3
        elif 'käromalet ogillas' in rulingOnly or "lämnas utan bifall" in rulingOnly or 'avskriv' in rulingOnly:
            dummyOut = 4  
        elif 'ensam' in rulingOnly and vardnInRuling and plaintNameFirst in findVardn or plaintNameFirst in findEnsam:
            dummyOut = 2
        elif 'ensam' in rulingOnly and vardnInRuling and  svNameFirst in findVardn or svNameFirst in findEnsam:
            dummyOut = 3
        elif vardnInRuling and 'överflytt' in rulingOnly and transferToDef in findVardn:
            dummyOut = 3
        elif vardnInRuling and 'överflytt' in rulingOnly and transferToPlaint in findVardn:
            dummyOut = 2
        elif vardnInRuling and 'tillerkänn' in findVardn and svNameFirst in findSentence('tillerkänn', rulingOnly):
            dummyOut = 3
        elif vardnInRuling and 'tillerkänn' in findVardn and plaintNameFirst in findSentence('tillerkänn', rulingOnly):
            dummyOut = 2
        elif 'bilaga' in rulingOnly and 'överens' in findSentence('bilaga', rulingOnly):
            dummyOut = 999
        else: 
            dummyOut = 999
        data['Utfall'].append(dummyOut)    
        
        #Visitation rights
        if childNameFirst in findSentence('umgänge', rulingOnly):  
            if childNameFirst == 'not found':
                dummyVisit = 999
            elif 'avslår' in findTwoWords('umgänge', childNameFirst, rulingOnly):
                dummyVisit = 0
            elif findTwoWords('semester', childNameFirst, rulingOnly):
                dummyVisit = 0
            elif 'bilaga' in rulingOnly:
                if 'sidorna' in findSentence('bilaga', rulingOnly):
                    dummyVisit = 999
            #If umgänge is found in rulingOnly but NOT semester or avslar
            else:
                dummyVisit = 1
        else:
            dummyVisit = 0 
        data['Umgänge'].append(dummyVisit)
        
        #Physical custody   
        if plaintNameFirst in findSentence('stadigvarande boende', rulingOnly):
            dummyPhys = 1
        elif svNameFirst in findSentence('stadigvarande boende', rulingOnly):
            dummyPhys = 2
        elif 'bo tillsammans' in rulingOnly: 
            if childNameFirst == 'not found':
                dummyPhys = 999
            elif childNameFirst and plaintNameFirst in findSentence('bo tillsammans', fullText):
                dummyPhys = 1
            elif childNameFirst and svNameFirst in findSentence('bo tillsammans', fullText):
                dummyPhys = 2
            else:
                dummyPhys = 999
        elif 'bilaga' in rulingOnly:
            if 'sidorna' in findSentence('bilaga', fullText):
                dummyPhys = 999
        else:
            dummyPhys = 0
        data['Stadigvarande boende'].append(dummyPhys)
        
        #Alimony
        if 'underhåll' in fullText:
            dummyAlimon = 1 
        #Alimony sum
        elif 'bilaga' in rulingOnly:
            if 'sidorna' in findSentence('bilaga', fullText):
                dummyAlimon = 999
        else:
            dummyAlimon = 0 
        data['Underhåll'].append(dummyAlimon)
             
        #Ruling by agreement
        for termAgree in agreementKey:
            if termAgree in fullText:
                for termHelper in agreementAdd:
                    v = findTwoWords(termAgree, termHelper, fullText)
                    if v is not emptyString and searchKey(yearSearch, v, 0) is year:
                        dummyAgree = 1
                    elif v is not emptyString and searchKey(yearSearch, v, 0) is None:
                        dummyAgree = 1                
            else:
                if svNameFirst in findSentence('yrkandet', fullText) and 'medger' in findSentence('yrkandet', fullText):
                    dummyAgree = 1
                elif svNameFirst in findSentence('yrkandet', fullText) and 'medgett' in findSentence('yrkandet', fullText):
                    dummyAgree = 1
                else:
                    dummyAgree = 0 
        data['Enl överenskommelse'].append(dummyAgree)
        
        #Fast information (snabbupplysningar)
        dummyInfo = termLoop(fastInfoKey, fullText)
        data['Snabbupplysning'].append(dummyInfo)
        
        #Cooperation talks
        dummyCoop = termLoop(corpTalksKey, fullText)
        for term in corpTalksKey:
            if term in fullText:
                v = findSentence(term, fullText)
                if v is not emptyString and searchKey(yearSearch, v, 0) is year:
                    dummyCoop = 1
                elif v is not emptyString and searchKey(yearSearch, v, 0) is None:
                    dummyCoop = 1     
            else:
                dummyCoop = 0
        data['Samarbetssamtal'].append(dummyCoop)
        
        #Investigation
        dummyInvest = termLoop(investigationKey, fullText)
        data['Utredning'].append(dummyInvest)
                    
        #Main hearing 
        for term in mainHearingKey:
            if term in fullText:
                if 'utan' in findSentence(term, fullText) or 'inför' in findSentence(term, fullText):
                    dummyMainHear = 0
                    break
                else:
                    dummyMainHear = 1
                    break
            else:
                dummyMainHear = 0
        data['Huvudförhandling'].append(dummyMainHear)

        #Name of judge
        try:
            judgeName = ((searchLoop(judgeSearch, lastPageFormatted, 1)).split('\n'))[0]
        except:
            judgeName = 'Not found'
        data['Domare'].append(judgeName.lower())
    
#Dataframe created from dictionary
df = pd.DataFrame(data)
with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    print(df)

#Save to csv
#df.to_csv(output_path, sep = ',', encoding='utf-8-sig')

print("---Saved as CSV---")



