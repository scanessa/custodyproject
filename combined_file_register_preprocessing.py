# -*- coding: utf-8 -*-
"""
Created on Tue Nov  2 15:04:16 2021

@author: ifau-SteCa

This code extracts case id, court, year, judge for all pdf files

Categories for case type: 

    1217 A - Äktenskapsskillnad\domar; divorce/custody battles (ideal case)
    1217 B - Äktenskapsskillnad\domar utan värdnadstvist; divorce with no custody battles
    1216 A - Vårdnad\domar; custody battles of non-divorcing parents
    1216 B - Vårdnad\domar där socialfärvaltning är kärande eller svarande; legal guardian cases

Courts: "Alingsås",	"Attunda",	"Blekinge",	"Borås",	"Eksjö",	"Eskilstuna",	"Falu",	"Gotlands",	"Gällivare",	"Gävle",	"Göteborgs",	"Halmstads",	"Haparanda",	"Helsingborg",	"Hudiksvall",	"Hässleholms",	"Jönköping",	"Kalmar",	"Kristianstad",	"Linköpings",	"Luleå",	"Lunds",	"Lycksele",	"Malmö",	"Mora",	"Nacka",	"Norrköpings",	"Norrtälje",	"Nyköping",	"Skaraborgs",	"Skellefteå",	"Solna",	"Stockholms",	"Sundsvalls",	"Södertälje",	"Södertörns",	"Uddevalla",	"Umeå",	"Uppsala",	"Varberg",	"Vänersborg",	"Värmland",	"Västmanland",	"Växjö",	"Ystad",	"Ångermanland",	"Örebro",	"Östersund",

Paths for full sample:
rootdir = "P:/2020/14/Tingsrätter/"
output_register = "P:/2020/14/Kodning/Data/case_register_data.csv"
output_rulings = "P:/2020/14/Kodning/Data/rulings_data.csv"
#Specify folders to search PDFs in
exclude = set(["Case_Sorting_SC"
               ])
includes = 'all_cases'  #change back to all cases to loop over all files
save = 1

Paths to check cases:
rootdir = "P:/2020/14/Kodning/Test-round-4/check4/subcheck"
output_register = "P:/2020/14/Kodning/Data/case_register_data.csv"
output_rulings = "P:/2020/14/Kodning/Data/rulings_data.csv"
#Specify folders to search PDFs in
exclude = set(["notdone", 'done'])
includes = 'subcheck'  #change back to all cases to loop over all files
save = 0

"""

import re, io, os, pandas as pd 
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.converter import PDFPageAggregator

#Define Paths
rootdir = "P:/2020/14/Tingsrätter/Stockholms"
output_register = "P:/2020/14/Kodning/Data/case_register_data.csv"
output_rulings = "P:/2020/14/Kodning/Data/rulings_data.csv"
#Specify folders to search PDFs in
exclude = set([])
includes = 'all_cases'  #change back to all cases to loop over all files
save = 0

#Define key functions
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
            yearChild = '19'+i[:2] if int(i[:2])>40 else '20'+i[:2]
        age = int(caseyear) - int(yearChild)
        if age < 18: 
            result.append(i)
    return result
    
#Define search terms
legalGuardingTerms = ["social", "kommun", "nämnden", "stadsjurist", 'stadsdel', 'familjerätt']
nameCaps = '[A-ZÅÄÖ]{3,}'
svarandeSearch = ' Svarande|SVARANDE|Motpart|MOTPART|SVARANDE och KÄRANDE |MANNEN|Mannen'
idNo ='((\d{6,10}.?.?(\d{4})?)[,]?\s)'
appendixStart = '((?<!se )Bilaga 1|(?<!se )Bilaga A|sida\s+1\s+av)'
searchCaseNo = 'må.\s*(nr)?[.]?\s*t\s*(\d*\s*.?.?\s*\d*)'
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

judgeProtokollPreffix = '(Lagmannen|lagmannen|Rådmannen|rådmannen|notarien|Beredningsjuristen|beredningsjuristen|tingsfiskalen|Tingsfiskalen)'
suff1 = '[,|;]?\s*[(]?'
suff2 = '((\w+)?\s*(Protokollförare|protokollförare|ordförande))?'
suff3 = '[)]?\s*([A-ZÅÄÖ]{2,})'
judgeProtokollSuffix = suff1 + suff2+ suff3

judgeSearchProtokoll = {
    '1': judgeProtokollPreffix + '\s*(([A-ZÅÄÖ][a-zåäöé]+\s*){2,4})' + judgeProtokollSuffix, #normal names
    '2': judgeProtokollPreffix + '\s*([A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ][a-zåäöé]+\s+)'+ judgeProtokollSuffix, #first name hyphenated
    '3': judgeProtokollPreffix + '\s*([A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s+)'+ judgeProtokollSuffix, #last name hypthenated
    '4': judgeProtokollPreffix + '\s*([A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s+)'+ judgeProtokollSuffix, #first and last name hyphenated
    '5': judgeProtokollPreffix + '\s*([A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ]\s[A-ZÅÄÖ][a-zåäöé]+\s+)'+ judgeProtokollSuffix, #name with initial as second name
    '6': judgeProtokollPreffix + '\s*(([A-ZÅÄÖ][a-zåäöé]+\s*){1})' + '[,|;]?\s*[(]?((\w+) [p|P]rotokollförare)?[)]?\s*([A-Z])' #only last name 
    }

#Define keys for simple word search
fastInfoKey = ['snabbupplysning', 'upplysning', 'snabbyttrande']
corpTalksKey = ['samarbetssamtal','medlingssamtal',' medling', ' medlare']
mainHearingKey = ['huvudförhandling' , ' rättegång ' , 'sakframställning' , ' förhör ', 'tingsrättens förhandling','huvud- förhandling' ]
lawyerKey = ["ombud:", 'god man:',  'advokat:', "ombud", 'god man',  'advokat']
investigationKey = ['vårdnadsutredning','boendeutredning','umgängesutredning']
allOutcomes = ["vård", "umgänge", "boende"]
umgangeKey = ['umgänge', 'umgås']
separationKey = ['separera', 'relationen tog slut', 'förhållandet tog slut', 'relationen avslutades', 'förhållandet avslutades', 'skildes', 'skiljas', 'skiljer' ]
countries = ['saknas', 'u.s.a.', 'u.s.a', 'usa', 'afghanistan', 'albanien', 'algeriet', 'andorra', 'angola', 'antigua och barbuda', 'argentina', 'armenien', 'australien', 'azerbajdzjan', 'bahamas', 'bahrain', 'bangladesh', 'barbados', 'belgien', 'belize', 'benin', 'bhutan', 'bolivia', 'bosnien och hercegovina', 'botswana', 'brasilien', 'brunei', 'bulgarien', 'burkina faso', 'burundi', 'centralafrikanska republiken', 'chile', 'colombia', 'costa rica', 'cypern', 'danmark', 'djibouti', 'dominica', 'dominikanska republiken', 'ecuador', 'egypten', 'ekvatorialguinea', 'elfenbenskusten', 'el salvador', 'eritrea', 'estland', 'etiopien', 'fiji', 'filippinerna', 'finland', 'frankrike', 'förenade arabemiraten', 'gabon', 'gambia', 'georgien', 'ghana', 'grekland', 'grenada', 'guatemala', 'guinea', 'guinea-bissau', 'guyana', 'haiti', 'honduras', 'indien', 'indonesien', 'irak', 'iran', 'irland', 'island', 'israel', 'italien', 'jamaica', 'japan', 'jemen', 'jordanien', 'kambodja', 'kamerun', 'kanada', 'kap verde', 'kazakstan', 'kenya', 'kina', 'kirgizistan', 'kiribati', 'komorerna', 'kongo-brazzaville', 'kongo-kinshasa', 'kroatien', 'kuba', 'kuwait', 'laos', 'lesotho', 'lettland', 'libanon', 'liberia', 'libyen', 'liechtenstein', 'litauen', 'luxemburg', 'madagaskar', 'malawi', 'malaysia', 'maldiverna', 'mali', 'malta', 'marocko', 'marshallöarna', 'mauretanien', 'mauritius', 'mexiko', 'mikronesiska federationen', 'moçambique', 'moldavien', 'monaco', 'montenegro', 'mongoliet', 'myanmar', 'namibia', 'nauru', 'nederländerna', 'nepal', 'nicaragua', 'niger', 'nigeria', 'nordkorea', 'nordmakedonien', 'norge', 'nya zeeland', 'oman', 'pakistan', 'palau', 'panama', 'papua nya guinea', 'paraguay', 'peru', 'polen', 'portugal', 'qatar', 'rumänien', 'rwanda', 'ryssland', 'saint kitts och nevis', 'saint lucia', 'saint vincent och grenadinerna', 'salo-monöarna', 'samoa', 'san marino', 'são tomé och príncipe', 'saudiarabien', 'schweiz', 'senegal', 'seychellerna', 'serbien', 'sierra leone', 'singapore', 'slovakien', 'slovenien', 'somalia', 'spanien', 'sri lanka', 'storbritannien', 'sudan', 'surinam', 'swaziland', 'sydafrika', 'sydkorea', 'sydsudan', 'syrien', 'tadzjikistan', 'tanzania', 'tchad', 'thailand', 'tjeckien', 'togo', 'tonga', 'trinidad och tobago', 'tunisien', 'turkiet', 'turkmenistan', 'tuvalu', 'tyskland', 'uganda', 'ukraina', 'ungern', 'uruguay', 'usa', 'uzbekistan', 'vanuatu', 'vatikanstaten', 'venezuela', 'vietnam', 'vitryssland', 'zambia', 'zimbabwe', 'österrike', 'östtimor']
cities = ['alingsås', 'arboga', 'arvika', 'askersund', 'avesta', 'boden', 'bollnäs', 'borgholm', 'borlänge', 'borås', 'djursholm', 'eksjö', 'enköping', 'eskilstuna', 'eslöv', 'fagersta', 'falkenberg', 'falköping', 'falsterbo', 'falun', 'filipstad', 'flen', 'gothenburg', 'gränna', 'gävle', 'hagfors', 'halmstad', 'haparanda', 'hedemora', 'helsingborg', 'hjo', 'hudiksvall', 'huskvarna', 'härnösand', 'hässleholm', 'höganäs', 'jönköping', 'kalmar', 'karlshamn', 'karlskoga', 'karlskrona', 'karlstad', 'katrineholm', 'kiruna', 'kramfors', 'kristianstad', 'kristinehamn', 'kumla', 'kungsbacka', 'kungälv', 'köping', 'laholm', 'landskrona', 'lidingö', 'lidköping', 'lindesberg', 'linköping', 'ljungby', 'ludvika', 'luleå', 'lund', 'lycksele', 'lysekil', 'malmö', 'mariefred', 'mariestad', 'marstrand', 'mjölby', 'motala', 'nacka', 'nora', 'norrköping', 'norrtälje', 'nybro', 'nyköping', 'nynäshamn', 'nässjö', 'oskarshamn', 'oxelösund', 'piteå', 'ronneby', 'sala', 'sandviken', 'sigtuna', 'simrishamn', 'skanör', 'skanör med falsterbo', 'skara', 'skellefteå', 'skänninge', 'skövde', 'sollefteå', 'solna', 'stockholm', 'strängnäs', 'strömstad', 'sundbyberg', 'sundsvall', 'säffle', 'säter', 'sävsjö', 'söderhamn', 'söderköping', 'södertälje', 'sölvesborg', 'tidaholm', 'torshälla', 'tranås', 'trelleborg', 'trollhättan', 'trosa', 'uddevalla', 'ulricehamn', 'umeå', 'uppsala', 'vadstena', 'varberg', 'vaxholm', 'vetlanda', 'vimmerby', 'visby', 'vänersborg', 'värnamo', 'västervik', 'västerås', 'växjö', 'ystad', 'åmål', 'ängelholm', 'örebro', 'öregrund', 'örnsköldsvik', 'östersund', 'östhammar']
excludePhysical = ['jämna' , 'växelvis', 'skyddat']
rejectKey = ['avskriv',' ogilla','utan bifall','avslå',' inte ','skrivs', 'kvarstå', ' inga '] 
rejectInvest = ['avskriv',' ogilla','utan bifall','avslå',' inte ',' inga ', ' utöva '] 
rejectKeyOutcome = ['avskriv',' ogilla','utan bifall','avslå',' inte ','skrivs', 'kvarstå', ' inga ', 'utan']  
remindKey = ['bibehålla' ,'påminn' ,'erinra' ,'upply', 'kvarstå', 'fortfarande ']
footer = ['telefax', 'e-post', 'telefon', 'besöksadress', 'postadress', 'expeditionstid', 'dom']
headerSplit = ['PARTER','Parter']

#Intiialize dictionary and helper variables
noOfFiles,rulingCount = 0,0
pdf_files, unreadable_files = [], []

#Read in PDFs
for subdir, dirs, files in os.walk(rootdir, topdown=True):
    for term in exclude:
        if term in dirs:
            dirs.remove(term)
    for file in files:
        if includes in subdir and file.endswith('.pdf'):
            pdf_dir = (os.path.join(subdir, file))
            pdf_files.append(pdf_dir)
            print(f"Dealing with file {subdir}/{file}")
            continue

#Loop over files and extract data
for file in pdf_files:
    data_register = {'caseid':[], 'type':[], 'casetype':[], 'court':[], 'date':[], 'plaintiff':[], 'defendant':[], 'judge':[], 'judgetitle':[], 'filepath':[]}
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
            fullTextFormatted = pages_text_formatted
            fullTextFormattedJoined = ''.join(pages_text_formatted)
            if appendixPage:
                appendixPageNo = appendixPage[-1] #not 0 because of Gotlands 424-18
                fullTextFormatted = pages_text_formatted[0:(appendixPageNo)]
                fullTextOG = ''.join(pages_text[0:(appendixPageNo)])
                fullTextFormattedJoined = ''.join(pages_text_formatted[0:(appendixPageNo)])
                
        #Get header
        headerSplit2 = ['DOMSLUT', 'Domslut']

        try:
            print('header 2')
            headerFormatted1 = (re.split('DOMSLUT', firstPageFormatted))[0]
            for term in headerSplit:
                headerFormatted2 = headerFormatted1.split(term)
                if len(headerFormatted2) != 1:
                    break
                else:
                    continue
            headerFormatted = headerFormatted2[1]
        except IndexError:                
            try:
                print('header 3')
                headerFormatted = re.split('Mål ', re.split('_{10,40}', firstPageFormatted)[0])[1] 
            except:
                print('header 4')
                try:
                    headerFormatted = ''.join(firstPageFormatted.split('')[0:20])
                except:
                    headerFormatted = ''.join(firstPageFormatted)
        headerOG = re.split('_{10,40}', firstPage)[0]
        header = headerOG.lower()  

        try:
            topwords = ' '.join(firstPage.split()[0:20].lower())
        except:
            topwords = ''.join(firstPage.lower())
        
        #Get last page of ruling with judge name 
        for page in fullTextFormatted:
            for m in ['\nÖVERKLAG','\nÖverklag','\nHUR MAN ÖVERKLAG','\nHur man överklag','\nHur Man Överklag','Anvisning för överklagande']:
                if m in page:
                    lastPageFormatted = page
                    break
                else: 
                    lastPageFormatted = '.'.join((pages_text_formatted[appendixPageNo-1]).split("."))
                    continue
            else:
                continue
            break
        #Print page formatted with: print((firstPageFormatted).split("."))
    
        #Full text
        fullText = fullTextOG.lower() 
        
        #Get plaintiff and defendant strings  
        try:
            svarandeStringOG = re.split('Svarande|SVARANDE', headerFormatted)[1] 
            kärandeStringOG = re.split('Kärande|KÄRANDE', (re.split('Svarande|SVARANDE', headerFormatted)[0]))[1]
            #print('PARTY1: ',svarandeStringOG.split('.'))
            if svarandeStringOG == "":
                svarandeStringOG = re.split('Svarande|SVARANDE', headerFormatted)[2] 
                #print('PARTY2: ',svarandeStringOG.split('.'))
            elif len(kärandeStringOG.split()) < 4:
                None.split()
                #print('PARTY3: ',svarandeStringOG.split('.'))
        except IndexError:
            try:
                svarandeStringOG = re.split(svarandeSearch, headerFormatted)[1] 
                kärandeStringOG = re.split('Kärande|KÄRANDE|Hustrun|HUSTRUN', (re.split(svarandeSearch, headerFormatted)[0]))[1]
                #print('PARTY5: ',svarandeStringOG.split('.'))
                if svarandeStringOG == "":
                    svarandeStringOG = re.split(svarandeSearch, headerFormatted)[2] 
                    #print('PARTY6: ',svarandeStringOG.split('.'))
                elif len(kärandeStringOG.split()) < 4:
                    svarandeStringOG = re.split("(?i)SVARANDE och KÄRANDE|SVARANDE OCH GENKÄRANDE ", headerFormatted)[1]
                    kärandeStringOG = re.split('(?i)KÄRANDE och SVARANDE|KÄRANDE OCH GENSVARANDE', (re.split("SVARANDE och KÄRANDE|SVARANDE OCH GENKÄRANDE ", headerFormatted)[0]))[1]
                    #print('PARTY7: ',svarandeStringOG.split('.'))
            except IndexError:
                try:
                    s1 = headerFormatted.split('1.')[1]
                    svarandeStringOG = s1.split('2.')[1]
                    kärandeStringOG = s1.split('2.')[0]
                    #print('PARTY8: ',svarandeStringOG.split('.'))
                except IndexError:
                    svarandeStringOG, kärandeStringOG = 'not found, not found', 'not found, not found'
                    #print('PARTY9: ',svarandeStringOG.split('.'))
        svarandeString = svarandeStringOG.lower()
        kärandeString = kärandeStringOG.lower()

        """
        Information for all docs that is NOT specific to doms
        """
        #Case ID
        try:
            caseNo = ''.join((searchKey(searchCaseNo, fullText, 2)).split())
        except AttributeError:
            try:
                caseNo = searchKey('T.?\s*(\d*-\d*)', file, 1)
            except:
                caseNo = "Not found"
        
        #Document type
        filename = file.lower() 
        if "dagbok" in topwords:
            docType = "dagbok"
        elif "protokol" in topwords:
            docType = "protokoll"
        elif  "TLIGT BESLUT" in fullTextOG:
            docType = "slutligt beslut"
        elif 'deldom' in topwords or 'deldom' in filename or 'mellandom' in filename or 'mellandom' in topwords:
            docType = "deldom"
        elif ' dom ' in filename or ' dom.' in filename or ' dom;' in filename or ' dom ' in topwords:
            docType = "dom"
        elif 'slutligt beslut' in filename:
            docType = "slutligt beslut"
        elif "dom " in topwords:
            docType = 'dom'
        else:
            docType = "Not found"
        
        #District Court
        courtName = re.split('\W',file.split('/')[4])[0]
        
        #Year Closed
        try:
            date = searchLoop(dateSearch, topwords, 1, [])    
            year = date[:4]
        except:
            date = "Not found"
        
        # Plaintiff and Defendant
        if docType == "dagbok":
            plaintNo = '-'
            defNo = '-'
        else:
            plaintNameFull, plaintNameFirst, plaintNo = party_id(kärandeStringOG, idNo, kärandeString, 2)
            defNameFull, defNameFirst, defNo = party_id(svarandeStringOG, idNo, svarandeString, 2)   
      
        #Name of judge
        judgeTitle = "N/A"
        if docType == 'slutligt beslut' or docType == 'protokoll':
            print("judge0")
            judgeName = searchLoop(judgeSearchProtokoll, fullTextOG, 2, ['telefon','telefax'])
            judgeTitle = searchLoop(judgeSearchProtokoll, fullTextOG, 1, ['telefon','telefax'])
            if judgeName is None:
                try:
                    print("judge1")
                    judgeName = (((searchLoop(judgeSearch, lastPageFormatted, 1,['telefon','telefax'])).split('\n'))[0])
                except:
                    print("judge2")
                    judgeName = fullText.split('.')[-1]
        elif docType == 'dom' or docType == 'deldom':
            try:
                judgeName = ((searchLoop(judgeSearch, lastPageFormatted, 1, ['telefon','telefax', 'svarande'])).split('\n'))[0]
                judgeName = judgeName.lower()
                judgeName = judgeName.strip()
            except AttributeError:
                try:
                    lastPageFormatted = re.split('ÖVERKLAG|Överklag|överklag', lastPageFormatted)[-1]
                    judgeName = ((searchLoop(judgeSearchNoisy, lastPageFormatted, 1, ['telefon','telefax', 'svarande', 't'])).split('\n'))[0]
                    judgeName = re.split('\s{4,}|,', judgeName)[0]
                    judgeName = judgeName.lower()
                    judgeName = judgeName.strip().strip('/').strip('|')
                except:
                    judgeName = 'Not found'
        else:
            print("judge5")
            judgeName = "Not found"

        #RULINGS
        if docType == 'dom' or docType == 'deldom':
            
            print("RULING")
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
                if searchKey('\d\d\s*–\s*\d\d', rulingOnlyOG1, 0):
                    rulingOnlyOG1 = re.sub('\s*–\s*','–',rulingOnlyOG1)
                    rulingOnlyOG2 = re.sub('\s*–\n','–',rulingOnlyOG1)
                else:
                    rulingOnlyOG1 = re.sub('\s*-\s*','-',rulingOnlyOG1)
                    rulingOnlyOG2 = re.sub('\s*-\n','-',rulingOnlyOG1)
                rulingOnlyOG = ' '.join(''.join(rulingOnlyOG2).split())
            except AttributeError:
                rulingOnlyOG = ' '.join(''.join(re.split('(YRKANDEN|Yrkanden)', rulingStringFormatted)[0].lower() ).split())
                if searchKey('\d\d\s*–\s*\d\d', rulingOnlyOG1, 0):
                    rulingOnlyOG = re.sub('\s*–\s*','–',rulingOnlyOG)
                    rulingOnlyOG = re.sub('\s*–\n','–',rulingOnlyOG)
                else:
                    rulingOnlyOG = re.sub('\s*-\s*','-',rulingOnlyOG)
                    rulingOnlyOG = re.sub('\s*-\n','-',rulingOnlyOG)
            rulingOnly = rulingOnlyOG.lower() 
        
            #Case type
            # 1216 B: legal guardian cases
            if any([x in svarandeString for x in legalGuardingTerms]) or any([x in kärandeString for x in legalGuardingTerms]):
                print("2")
                caseType = "1216B"
            elif "overflyttas" in fullText:
                print("3")
                caseType = "1216B"
            elif "ensamkommande flyktingbarn" in fullText:
                print("4")
                caseType = "1216B"
            elif 'vårdnadshavare' in findTerms(['förordnad', 'förordnad'], fullTextOG):
                print("4a")
                caseType = "1216B"
            elif 'de har inga gemensamma barn' in fullText:
                print("5")
                caseType = "1217B"
            elif 'äktenskaps' in rulingOnly or 'äktenskaps' in firstPage:
                if "vård" in rulingOnly: 
                    for term in remindKey:
                        if term in findTerms(["vård"], firstPage) or term in findTerms(["Vård"], firstPage):
                            print("7")
                            caseType = "1217B"
                        else:
                            #1217 A: divorce and custody in same case/ruling
                            print("8")
                            caseType = "1217A"
                else:
                    print("9") 
                    caseType = "1217B"
            elif 'vård' in rulingOnly:
                print("10") 
                caseType = "1216A"
            elif "umgänge" or "umgås" in rulingOnly:
                #Physical custody cases
                print("11")
                caseType = "1216A"
            else:
                print("12") 
            
            #Write data of custody and divorce rulings to CSV
            if caseType == '1217B' or caseType == '1217A' or caseType == '1216A':
                print('Ruling data for a case: ', caseType)
                rulingCount += 1
                
                #Split relevant ruling cases further into different sections
                #Get domskäl or yrkanden
                try:
                    domStart = re.split('DOMSKÄL|Domskäl', fullTextOG)[1]
                except IndexError:
                    try:
                        domStart = re.split('BEDÖMNING|Tingsrättens bedömning', fullTextOG)[1]
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
                
                try:

                    #List of children's numbers
                    childNoRes = childNos(rulingOnly, year)  
                    if not childNoRes:
                        childNoRes = childNos(fullText, year) 
                        if not childNoRes:   
                            try:
                                b = []
                                childNames =  []
                                a = re.split('(?=[.]{1}\s[A-ZÅÐÄÖÉÜ])..', rulingOnlyOG)
                                for sentence in a:
                                    if all([x in sentence for x in ['vård']]) or all([x in sentence for x in ['Vård']]):
                                        b.append(sentence)
                                sentenceString = '.'.join(b)
                                wordList = sentenceString.split(' ')[1:]
                                for word in wordList:
                                    if word[0].isupper() and not any([x in word.lower() for x in defNameFull.split()]) and word[0].isupper() and not any([x in word.lower() for x in plaintNameFull.split()]):
                                        childNameFirst = childNameFull = word.strip(',')
                                        childNames.append(childNameFirst.lower())
                                childNoRes = childNames
                            except:
                                childNoRes = ['not found']  
                    
                    
                    
                    
                    
                    
                    
                    #Loop to create dictionary with one row per child
                    for i in childNoRes:
                        data_rulings = {'child_id':[], 'case_no':[], 'court':[], 'date':[], 'deldom':[], 'divorce_only': [] , 'joint_application_custody': [],'plaintiff_id':[], 'defendant_id':[], 'plaintiff_lawyer':[], 'defendant_lawyer':[], 'defendant_address_secret': [], 'plaintiff_address_secret':[], 'defendant_abroad':[], 'defendant_unreachable':[], 'outcome':[], 'visitation':[], 'physical_custody':[], 'alimony':[], 'agreement_legalcustody':[], 'agreement_any':[], 'fastinfo':[], 'cooperation_talks':[], 'investigation':[], 'mainhearing':[], 'separation_year': [], 'judge':[], 'page_count': [], 'correction_firstpage': [], 'flag': [],'file_path': []}
    
                        #Variables that are constant for all children in court doc       
                        dummyDel = 1 if 'deldom' in topwords else 0
                        dummyLawyerPlaint = 1 if 'ombud' in kärandeString or "god man" in kärandeString or "advokat" in kärandeString else 0
    
    
    
    
                        #Get child's name
                        childNameKey = ('([A-ZÅÐÄÖÉÜÆØÞ][A-ZÅÐÄÖÉÜÆØÞa-zåäïüóöéæøßþîčćžđšžůúýëçâêè]+)\s*[,]?\s*[(]?\s*' + i )
                        childNameFirst = searchKey(childNameKey, rulingOnlyOG, 1)
                        print('CHILD NAME : ', childNameFirst, i)
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
                          
                        
                        
                        
                        
                        #Defendant representative
                        for term in lawyerKey:
                            if term in svarandeString:
                                svGodMan = 1 if 'god man' in term else 0
                                defOmbud = 1 
                                defAddress = re.split(term, svarandeString)[0]
                                cityString = ''.join((defAddress.strip(' _\n')).split(' ')[-1])
                                break
                            else:
                                defOmbud = 0
                                defAddress = svarandeString
                                svarandeString = svarandeString.split('\nsaken ')[0] if '\nsaken ' in svarandeString else svarandeString
                                cityString = ''.join((svarandeString.strip(' _\n')).split(' ')[-1])
                                svGodMan = 0
                                continue
                
                        #Defendant abroad
                        svGodMan = 1 if 'c/o' in svarandeString else svGodMan

                        
                        if any([x in cityString for x in cities]) and not any([x in defAddress.lower() for x in lawyerKey]):
                            dummyAbroad = 0
                            print('abroad 0')
                        elif any([x in cityString for x in countries]) or 'okänd' in svarandeString:
                            dummyAbroad = 1
                            print('abroad 1')
                        elif svGodMan ==1  and 'saknar kän' in svarandeString:
                            dummyAbroad = 1
                            print('abroad 1a')
                        elif cityString.isdecimal() or '@' in cityString:
                            dummyAbroad = 1
                            print('abroad 2')
                        elif svGodMan == 1 and any(x in findTerms(['inte', 'sverige'], fullTextOG) for x in defNameFirst):
                            dummyAbroad = 1
                            print('abroad 3')
                        elif svGodMan == 1 and findTerms(['befinn', 'sig','utomlands'], fullTextOG):
                            dummyAbroad = 1 #didnt include defNameFirst because sv might be referred to by Han
                            print('abroad 4')
                        elif svGodMan == 1 and any([x in findTerms(['befinn', 'sig'], fullTextOG) for x in countries]):
                            dummyAbroad = 1 #didnt include defNameFirst because sv might be referred to by Han
                            print('abroad 5')  
                        elif any([x in findTerms(['befinn', 'sig', 'sedan'], domskalOG) for x in countries]):
                            dummyAbroad = 1 #didnt include defNameFirst because sv might be referred to by Han
                            print('abroad 5b')  
                        elif any(x in findTerms(['flytta', 'till', 'inte', 'sverige'], fullTextOG) for x in defNameFirst):
                            dummyAbroad = 1
                            print('abroad 5a')
                        elif svGodMan == 1 and any([x in findTerms(['återvänt', 'till'], fullTextOG) for x in countries]):
                            dummyAbroad = 1 
                            print('abroad 5c')
                        elif any(x in findTerms(['försvunnen'], fullTextOG) for x in defNameFirst):
                            dummyAbroad = 1 
                            print('abroad 6')
                        elif any(x in findTerms(['bortavarande', 'varaktigt'], fullTextOG) for x in defNameFirst):
                            dummyAbroad = 1 
                            print('abroad 7')
                        elif any(x in findTerms([' bor ', ' i '], fullTextOG) for x in defNameFirst) and any(x in findTerms([' bor ', ' i '], fullTextOG) for x in countries) and not findTerms([' bor ', ' i ', 'barn'], fullTextOG):
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
                            reachable = [[name, 'kontakt ', 'med']] #took out genom sin gode man because this must not mean that SV and God Man were in contact (see 396-15)
                            for part in reachable:
                                if found1 == 0 and findTerms(part, fullTextOG) and not any([x in findTerms(part, fullTextOG) for x in noContactKey]):
                                    print('Unreach 3: ', part)
                                    dummyUnreach = 0
                            else:
                                continue
                            break
                        #Year of Separation of Unmarried Parents
                        dummySeparate = searchKey('separerade under (\d{4})', fullText, 1)
                        if not dummySeparate:
                            for term in separationKey:
                                if term in fullText:
                                    dummySeparate = searchKey('(\d{4})', findTerms([term], fullTextOG), 0)
                                    break
                                else:
                                    dummySeparate = '-'
                                    continue
                        #Outcome
                        findVardn = findTerms(['vård',i], rulingOnlyOG)
                        findVardn = findTerms(['vård'], rulingOnlyOG) if not findVardn else findVardn
                        findVardn = findVardn.replace('gemen-sam', 'gemensam') if 'gemen-sam' in findVardn else findVardn
                        
                        findVardn = findVardn.strip('2. ') + ' '
                        
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
                        if any([ x in findTerms([' ensam', 'gemensam ', 'vårdn'], findVardn) for x in rejectKeyOutcome]):
                            newRuling = []
                            dummyOut = 999
                            for part in re.split(',|;',findVardn):
                                if not any([x in part for x in rejectKeyOutcome]):
                                    newRuling.append(part)
                            findVardn = ''.join(newRuling)
                        
                        anyVardn = not any([x in findVardn for x in rejectKeyOutcome])
                        print('FIND VARDN: ', findVardn)

                        #Shared custody 
                        if len(childNoRes)> 1:
                            sharedCustody = [['ska','tillkomma','tillsammans'],[i,'ska','tillkomma', 'gemensam '], [i,'ska','om','gemensam '],[i,'gemensam ','fortsätt','ska'],[i,'alltjämt','ska','gemensam '],[i,'gemensam ','alltjämt', 'är'],[i,'gemensam ','anförtro'],['gemensamma vård',i]]
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
                
                        print('DUMMYAGREE', dummyAgree)
                
                
                        #Joint application
                        jointApp = 1 if 'sökande' in firstPage.lower() and 'motpart' not in firstPage.lower() and dummyOut != 0 else 0
                
                        #Fast information (snabbupplysningar)
                        if any([term in fullText for term in legalGuardingTerms]) and findTerms(['yttra', term], fullTextOG) and not any([x in findTerms([term], fullTextOG) for x in rejectKey]): 
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
                            elif any([x in findTerms([' utred'], fullTextOG) for x in legalGuardingTerms]) and not any([x in findTerms([' utred'], fullTextOG) for x in rejectInvest]) and not findTerms(['saknas', 'möjlighet', ' utred'], fullTextOG):
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
                        
                        #Corrections
                        dummyAgree = 0 if dummyAgree == 1 and len(domskal.split(' ')) > 750 or dummyAgree == 1 and pageCount > 15 else dummyAgree                          
                        dummyUnreach = 0 if dummyOut == 3 or dummyMainHear == 1 and svGodMan == 0 else dummyUnreach
                        
                        #Flag cases
                        #Loose definition
                        flag = []
                        livingTerms = [' bo ', 'boende']
                        if any([x in findTerms(['uppgett'], fullTextOG) for x in legalGuardingTerms]):
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
                        
                        #print('Text: ', rulingOnlyOG) #(lastPageFormatted).split(".")
                        #print('\n')
                        
                        #Fill dataframe with search results
                        i = ''.join(i.split())
                        data_rulings['child_id'].append(i)
                        data_rulings['file_path'].append(file)
                        data_rulings['page_count'].append(pageCount)
                        data_rulings['correction_firstpage'].append(dummyRat)
                        data_rulings['case_no'].append(caseNo)
                        data_rulings['judge'].append(judgeName)
                        data_rulings['court'].append(courtName)
                        data_rulings['date'].append(date)
                        data_rulings['deldom'].append(dummyDel)
                        data_rulings['divorce_only'].append(dummyDivorce)
                        data_rulings['joint_application_custody'].append(jointApp)
                        data_rulings['plaintiff_id'].append(plaintNo) 
                        data_rulings['defendant_id'].append(defNo)   
                        data_rulings['defendant_address_secret'].append(dummyDefSecret)  
                        data_rulings['plaintiff_address_secret'].append(dummyPlaintSecret)  
                        data_rulings['plaintiff_lawyer'].append(dummyLawyerPlaint) 
                        data_rulings['defendant_lawyer'].append(defOmbud)
                        data_rulings['defendant_abroad'].append(dummyAbroad)
                        data_rulings['defendant_unreachable'].append(dummyUnreach)
                        data_rulings['outcome'].append(dummyOut)   
                        data_rulings['visitation'].append(dummyVisit)
                        data_rulings['physical_custody'].append(dummyPhys)
                        data_rulings['alimony'].append(dummyAlimon)                
                        data_rulings['agreement_legalcustody'].append(dummyAgree)    
                        data_rulings['agreement_any'].append(dummyAgreeAny)  
                        data_rulings['fastinfo'].append(dummyInfo)          
                        data_rulings['cooperation_talks'].append(dummyCoop)
                        data_rulings['investigation'].append(dummyInvest)
                        data_rulings['separation_year'].append(dummySeparate)
                        data_rulings['mainhearing'].append(dummyMainHear)
                        data_rulings['flag'].append(flag)
                        
                        df_rulings = pd.DataFrame(data_rulings)
                        with pd.option_context('display.max_rows', None, 'display.max_columns', None): 
                            print(df_rulings) 
                        if save == 1:
                            if rulingCount == 1:
                                df_rulings.to_csv(output_rulings, sep = ',', encoding='utf-8-sig', header=True)
                            else:
                                df_rulings.to_csv(output_rulings, mode = 'a', sep = ',', encoding='utf-8-sig', header=False)
                            
                            
                except Exception as e:
                    print(e)
                    data_rulings['child_id'].append('error')
                    data_rulings['file_path'].append(file)
                    data_rulings['page_count'].append('error')
                    data_rulings['correction_firstpage'].append('error')
                    data_rulings['case_no'].append('error')
                    data_rulings['judge'].append('error')
                    data_rulings['court'].append('error')
                    data_rulings['date'].append('error')
                    data_rulings['deldom'].append('error')
                    data_rulings['divorce_only'].append('error')
                    data_rulings['joint_application_custody'].append('error')
                    data_rulings['plaintiff_id'].append('error') 
                    data_rulings['defendant_id'].append('error')   
                    data_rulings['defendant_address_secret'].append('error')  
                    data_rulings['plaintiff_address_secret'].append('error')  
                    data_rulings['plaintiff_lawyer'].append('error')
                    data_rulings['defendant_lawyer'].append('error')
                    data_rulings['defendant_abroad'].append('error')
                    data_rulings['defendant_unreachable'].append('error')
                    data_rulings['outcome'].append('error')   
                    data_rulings['visitation'].append('error')
                    data_rulings['physical_custody'].append('error')
                    data_rulings['alimony'].append('error')                
                    data_rulings['agreement_legalcustody'].append('error')    
                    data_rulings['agreement_any'].append('error')  
                    data_rulings['fastinfo'].append('error')          
                    data_rulings['cooperation_talks'].append('error')
                    data_rulings['investigation'].append('error')
                    data_rulings['separation_year'].append('error')
                    data_rulings['mainhearing'].append('error')
                    data_rulings['flag'].append('error')
                    
                    df_rulings = pd.DataFrame(data_rulings)
                    with pd.option_context('display.max_rows', None, 'display.max_columns', None): 
                        print(df_rulings) 
                    if save == 1:
                        if rulingCount == 1:
                            df_rulings.to_csv(output_rulings, sep = ',', encoding='utf-8-sig', header=True)
                        else:
                            df_rulings.to_csv(output_rulings, mode = 'a', sep = ',', encoding='utf-8-sig', header=False)
                        
                     
        else:
            print("12")
            caseType = "N/A"
        
        #Save dictionary to csv
        print('\nDoc type: ', docType)
        print('\nCase type: ', caseType)
        
        data_register['casetype'].append(caseType)
        data_register['filepath'].append(file)
        data_register['judge'].append(judgeName.strip())   
        data_register['judgetitle'].append(judgeTitle) 
        data_register['defendant'].append(defNo)            
        data_register['plaintiff'].append(plaintNo)
        data_register['date'].append(date)
        data_register["court"].append(courtName)
        data_register['type'].append(docType)  
        data_register['caseid'].append(caseNo) 
        
        df_register = pd.DataFrame(data_register)
        if save == 1:
            if noOfFiles == 0:
                df_register.to_csv(output_register, sep = ',', encoding='utf-8-sig', header=True)
                noOfFiles += 1
            else:
                df_register.to_csv(output_register, mode = 'a', sep = ',', encoding='utf-8-sig', header=False)
            


    except Exception as e:
        print(e)
        data_register['filepath'].append(file)  
        data_register['caseid'].append('error')
        data_register['type'].append('error')
        data_register['casetype'].append('error')
        data_register['court'].append('error')
        data_register['date'].append('error')
        data_register['plaintiff'].append('error')
        data_register['defendant'].append('error')
        data_register['judge'].append('error')
        data_register['judgetitle'].append('error')
        
        df_register = pd.DataFrame(data_register)
        
        with pd.option_context('display.max_rows', None, 'display.max_columns', None): 
            print(df_register) 
        
        if save == 1:
            if noOfFiles == 0:
                df_register.to_csv(output_register, sep = ',', encoding='utf-8-sig', header=True)
                noOfFiles += 1
            else:
                df_register.to_csv(output_register, mode = 'a', sep = ',', encoding='utf-8-sig', header=False)
            

print('---Done---')







