"""
Attempting to clean up the different scripts

"""
import re
import io
import os
import subprocess
import pandas as pd
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter

#General settings
ROOTDIR = "P:/2020/14/Tingsrätter/Case_Sorting_SC/"
OCR_SCRIPT = "P:/2020/14/Kodning/Code/custodyproject/OCR.py"
output_register = "P:/2020/14/Kodning/Data/case_register_data.csv"
output_rulings = "P:/2020/14/Kodning/Data/rulings_data.csv"
#Specify folders to search PDFs in
EXCLUDE = set([])
SAVE = 0

#Define search terms
legalGuardingTerms = ["social", "kommun", "nämnden", "stadsjurist", 'stadsdel', 'familjerätt']
nameCaps = '[A-ZÅÄÖ]{3,}'
svarandeSearch = ' Svarande|SVARANDE|Motpart|MOTPART|SVARANDE och KÄRANDE |MANNEN|Mannen'
idNo ='((\d{6,10}.?.?(\d{4})?)[,]?\s)'
appendix_start = '((?<!se )Bilaga 1|(?<!se )Bilaga A|sida\s+1\s+av)'
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
    '13': '(rådmannen|tingsfiskalen)\s*((' + allLetters + '+\s+){2,4})',
    '14': '(rådmannen|tingsfiskalen)\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s+)', #first name hyphenated
    '15': '(rådmannen|tingsfiskalen)\s*(' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+\s+)', #last name hypthenated
    '16': '(rådmannen|tingsfiskalen)\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s*-\s*' + allLetters + '+\s+)', #first and last name hyphenated
    '17': '(rådmannen|tingsfiskalen)\s*(' + allLetters + '+\s' + capLetters + '\s' + allLetters + '+\s+)', #name with initial as second name
    '18': '(rådmannen|tingsfiskalen)\s*(' + capLetters + '\s' + capLetters + '\s' + allLetters + '+\s+)', #name with initial as second name
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
separationKey = ['separera', 'relationen tog slut', 'förhållandet tog slut', 'relationen avslutades', 
                 'förhållandet avslutades', 'skildes', 'skiljas', 'skiljer' ]
excludePhysical = ['jämna' , 'växelvis', 'skyddat']
rejectKey = ['avskriv',' ogilla','utan bifall','avslå',' inte ','skrivs', 'kvarstå', ' inga '] 
rejectInvest = ['avskriv',' ogilla','utan bifall','avslå',' inte ',' inga ', ' utöva '] 
rejectKeyOutcome = ['avskriv',' ogilla','utan bifall','avslå',' inte ','skrivs', 'kvarstå', ' inga ', 'utan']  
remindKey = ['bibehålla' ,'påminn' ,'erinra' ,'upply', 'kvarstå', 'fortfarande ']
footer = ['telefax', 'e-post', 'telefon', 'besöksadress', 'postadress', 'expeditionstid', 'dom']
headerSplit = ['PARTER','Parter']
countries = ['saknas', 'u.s.a.', 'u.s.a', 'usa', 'afghanistan', 'albanien', 'algeriet', 'andorra', 'angola', 'antigua och barbuda', 'argentina', 'armenien', 'australien', 'azerbajdzjan', 'bahamas', 'bahrain', 'bangladesh', 'barbados', 'belgien', 'belize', 'benin', 'bhutan', 'bolivia', 'bosnien och hercegovina', 'botswana', 'brasilien', 'brunei', 'bulgarien', 'burkina faso', 'burundi', 'centralafrikanska republiken', 'chile', 'colombia', 'costa rica', 'cypern', 'danmark', 'djibouti', 'dominica', 'dominikanska republiken', 'ecuador', 'egypten', 'ekvatorialguinea', 'elfenbenskusten', 'el salvador', 'eritrea', 'estland', 'etiopien', 'fiji', 'filippinerna', 'finland', 'frankrike', 'förenade arabemiraten', 'gabon', 'gambia', 'georgien', 'ghana', 'grekland', 'grenada', 'guatemala', 'guinea', 'guinea-bissau', 'guyana', 'haiti', 'honduras', 'indien', 'indonesien', 'irak', 'iran', 'irland', 'island', 'israel', 'italien', 'jamaica', 'japan', 'jemen', 'jordanien', 'kambodja', 'kamerun', 'kanada', 'kap verde', 'kazakstan', 'kenya', 'kina', 'kirgizistan', 'kiribati', 'komorerna', 'kongo-brazzaville', 'kongo-kinshasa', 'kroatien', 'kuba', 'kuwait', 'laos', 'lesotho', 'lettland', 'libanon', 'liberia', 'libyen', 'liechtenstein', 'litauen', 'luxemburg', 'madagaskar', 'malawi', 'malaysia', 'maldiverna', 'mali', 'malta', 'marocko', 'marshallöarna', 'mauretanien', 'mauritius', 'mexiko', 'mikronesiska federationen', 'moçambique', 'moldavien', 'monaco', 'montenegro', 'mongoliet', 'myanmar', 'namibia', 'nauru', 'nederländerna', 'nepal', 'nicaragua', 'niger', 'nigeria', 'nordkorea', 'nordmakedonien', 'norge', 'nya zeeland', 'oman', 'pakistan', 'palau', 'panama', 'papua nya guinea', 'paraguay', 'peru', 'polen', 'portugal', 'qatar', 'rumänien', 'rwanda', 'ryssland', 'saint kitts och nevis', 'saint lucia', 'saint vincent och grenadinerna', 'salo-monöarna', 'samoa', 'san marino', 'são tomé och príncipe', 'saudiarabien', 'schweiz', 'senegal', 'seychellerna', 'serbien', 'sierra leone', 'singapore', 'slovakien', 'slovenien', 'somalia', 'spanien', 'sri lanka', 'storbritannien', 'sudan', 'surinam', 'swaziland', 'sydafrika', 'sydkorea', 'sydsudan', 'syrien', 'tadzjikistan', 'tanzania', 'tchad', 'thailand', 'tjeckien', 'togo', 'tonga', 'trinidad och tobago', 'tunisien', 'turkiet', 'turkmenistan', 'tuvalu', 'tyskland', 'uganda', 'ukraina', 'ungern', 'uruguay', 'usa', 'uzbekistan', 'vanuatu', 'vatikanstaten', 'venezuela', 'vietnam', 'vitryssland', 'zambia', 'zimbabwe', 'österrike', 'östtimor']
cities = ['alingsås', 'arboga', 'arvika', 'askersund', 'avesta', 'boden', 'bollnäs', 'borgholm', 'borlänge', 'borås', 'djursholm', 'eksjö', 'enköping', 'eskilstuna', 'eslöv', 'fagersta', 'falkenberg', 'falköping', 'falsterbo', 'falun', 'filipstad', 'flen', 'gothenburg', 'gränna', 'gävle', 'hagfors', 'halmstad', 'haparanda', 'hedemora', 'helsingborg', 'hjo', 'hudiksvall', 'huskvarna', 'härnösand', 'hässleholm', 'höganäs', 'jönköping', 'kalmar', 'karlshamn', 'karlskoga', 'karlskrona', 'karlstad', 'katrineholm', 'kiruna', 'kramfors', 'kristianstad', 'kristinehamn', 'kumla', 'kungsbacka', 'kungälv', 'köping', 'laholm', 'landskrona', 'lidingö', 'lidköping', 'lindesberg', 'linköping', 'ljungby', 'ludvika', 'luleå', 'lund', 'lycksele', 'lysekil', 'malmö', 'mariefred', 'mariestad', 'marstrand', 'mjölby', 'motala', 'nacka', 'nora', 'norrköping', 'norrtälje', 'nybro', 'nyköping', 'nynäshamn', 'nässjö', 'oskarshamn', 'oxelösund', 'piteå', 'ronneby', 'sala', 'sandviken', 'sigtuna', 'simrishamn', 'skanör', 'skanör med falsterbo', 'skara', 'skellefteå', 'skänninge', 'skövde', 'sollefteå', 'solna', 'stockholm', 'strängnäs', 'strömstad', 'sundbyberg', 'sundsvall', 'säffle', 'säter', 'sävsjö', 'söderhamn', 'söderköping', 'södertälje', 'sölvesborg', 'tidaholm', 'torshälla', 'tranås', 'trelleborg', 'trollhättan', 'trosa', 'uddevalla', 'ulricehamn', 'umeå', 'uppsala', 'vadstena', 'varberg', 'vaxholm', 'vetlanda', 'vimmerby', 'visby', 'vänersborg', 'värnamo', 'västervik', 'västerås', 'växjö', 'ystad', 'åmål', 'ängelholm', 'örebro', 'öregrund', 'örnsköldsvik', 'östersund', 'östhammar']

def paths(include):
    pdf_files = []
    for subdir, dirs, files in os.walk(ROOTDIR, topdown=True):
        for term in EXCLUDE:
            if term in dirs:
                dirs.remove(term)
        for file in files: 
            if include in subdir and file.endswith('.pdf'):
                print(f"Dealing with file {subdir}/{file}\n")
                pdf_dir = (os.path.join(subdir, file))
                pdf_files.append(pdf_dir)
                continue
    return pdf_files

def read_file(file):
    pages_text, pages_text_formatted = [],[]
    page_count= 0
    
    def filereader_params():
        rsrcmgr = PDFResourceManager()
        retstr = io.StringIO()
        laparams = LAParams(line_margin=3)
        device = TextConverter(rsrcmgr, retstr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        return rsrcmgr,retstr,device,interpreter

    def appendix_pages(no_of_firstpage):      
        appendix_pageno = appendix[-1]
        fulltext_form = pages_text_formatted[no_of_firstpage:(appendix_pageno)]
        fulltext_caps = ''.join(pages_text[no_of_firstpage:(appendix_pageno)])
        return appendix_pageno, fulltext_form, fulltext_caps
    
    def text_parts(no_of_firstpage):
        firstpage_form = pages_text_formatted[no_of_firstpage]
        fulltext_caps = ''.join(pages_text[no_of_firstpage:])
        fulltext_form = pages_text_formatted[no_of_firstpage:]
        return fulltext_caps, fulltext_form, firstpage_form
        
    rsrcmgr,retstr,device,interpreter = filereader_params()
    
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,caching=True,check_extractable=True):
            read_position = retstr.tell()
            interpreter.process_page(page)
            retstr.seek(read_position, 0)
            page_text = retstr.read()
            page_text_clean = ' '.join((''.join(page_text)).split())
            pages_text.append(page_text_clean)
            pages_text_formatted.append(page_text)
            page_count += 1
    
    firstpage = pages_text[0]
    appendix = [k for k, item in enumerate(pages_text) if re.search(appendix_start, item)]
    appendix_pageno = len(pages_text)
    
    if "Rättelse" in firstpage:
        correction = 1
        firstpage = ''.join(pages_text[1])
        fulltext_caps, fulltext_form, firstpage_form = text_parts(1)
        if appendix:
            appendix_pageno, fulltext_form, fulltext_caps= appendix_pages(1)
    else:
        correction = 0
        fulltext_caps, fulltext_form, firstpage_form = text_parts(0)
        if appendix:
            appendix_pageno, fulltext_form, fulltext_caps = appendix_pages(0)    
    return correction, appendix_pageno, fulltext_form, fulltext_caps, firstpage, firstpage_form

def random_df(firstpage_form,file):    
    data = {'dummy':[], 'file': []}
    data['file'].append(file.split('/')[-1])
    if '5059-00' in firstpage_form:
        data['dummy'].append(1)
    else:
        data['dummy'].append(0)
    df = pd.DataFrame(data)
    return df

readable_files = paths('all_cases')
scanned_files = paths('all_scans')

for file in readable_files:
    correction, appendix_page_no, fulltext_form, fulltext_caps, firstpage, firstpage_form = read_file(file)
for file in scanned_files:
    subprocess.call(['python', OCR_SCRIPT])
    from OCR import firstpage_form
    # from OCR import lastpage_form
    # from OCR import fulltext_form
    # from OCR import judge_string
    from OCR import header
    topwords = header


print(random_df(firstpage_form,file))



         