# -*- coding: utf-8 -*-
"""
@author: Stella Canessa

This is the main code for creating the datasets for the ifo/IFAU custody research
project. Outputs are: 
    1) Dataset of rulings outcomes incl. controls of digital and scanned documents, identifying variable child ID
    2) Dataset of all court records available, identifying variable case number, court, date
    l

"""
import re
import time
import io
import os
import pandas as pd
import itertools
from fuzzywuzzy import process
from fuzzywuzzy import fuzz

from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter


#os.chdir("P:/2020/14/Kodning/Code/custodyproject/")

from searchterms import OCR_CORR, appendix_start, defend_search, caseno_search, id_pattern
from searchterms import date_search, judgetitle_search, judgesearch, judgesearch_noisy
from searchterms import ruling_search, legalguardian_terms, lawyer_key, citizen, contest_key
from searchterms import cities, countries, nocontant, separation_key, remind_key, residence_key
from searchterms import reject_outcome, visitation_key, reject, exclude_phys, physicalcust_list
from searchterms import agreement_key, agreement_add, no_vard, agreement_excl, past, fastinfo_key
from searchterms import cooperation_key, reject_invest, invest_key, outcomes_key, reject_mainhearing
from searchterms import mainhearing_key, exclude_judge

from OCR import ocr_main

#General settings
ROOTDIR = "P:/2020/14/Kodning/Scans/"
OUTPUT_REGISTER = "P:/2020/14/Kodning/Scans/case_register_data.csv"
OUTPUT_RULINGS = "P:/2020/14/Kodning/Scans/rulings_data.csv"
JUDGE_LIST = "P:/2020/14/Data/Judges/list_of_judges_cleaned.xls"

DATA_RULINGS = {
    
    'child_id':[], 'case_no':[], 'court':[], 'date':[], 'deldom':[],
    'divorce_only': [] , 'joint_application_custody': [],'plaintiff_id':[],
    'defendant_id':[], 'plaintiff_lawyer':[], 'defendant_lawyer':[],
    'defendant_address_secret': [], 'plaintiff_address_secret':[],
    'defendant_abroad':[], 'defendant_unreachable':[], 'outcome':[],
    'visitation':[], 'physical_custody':[], 'alimony':[],
    'agreement_legalcustody':[], 'agreement_any':[], 'fastinfo':[],
    'cooperation_talks':[], 'investigation':[], 'mainhearing':[],
    'separation_year': [], 'judge':[], 'page_count': [],
    'correction_firstpage': [], 'flag': [],'file_path': []
    
    }

DATA_REGISTER = {
    
    'caseid':[], 'type':[], 'casetype':[], 'court':[], 'date':[], 'plaintiff':[],
    'defendant':[], 'judge':[], 'judgetitle':[], 'filepath':[], 'flag': []

    }


#Specify folders to search PDFs in
EXCLUDE = set(['others', 'works'])
INCLUDE = set(['all_cases','all_scans'])
COUNT = 1
start_time = time.time()
flag = []

SAVE = 1
PRINT = 0



#Helper functions

def print_output(label, var):
    """
    If constant variable PRINT == 1 all output will be printed
    Label should be passed as string
    """
    if PRINT == 1 and var != "":
        print("-----" + label + ": ", var)
    elif PRINT == 1 and var == "":
        print("-----" + label, var)



def searchkey(string, part, g):
    finder = re.compile(string)
    match = finder.search(part)
    if match is not None:
        searchResult = match.group(g)
    else:
        searchResult = None
    return searchResult



def dictloop(dictionary, part, g, exclude_terms):
    for i in dictionary:
        result = searchkey(dictionary[i], part, g)
        if result is None or any([x in result.lower() for x in exclude_terms]):
            continue
        else:
            break
    return result



def findterms(stringlist, part):
    sentenceRes = []
    split = re.split('(?=[.]{1}\s[A-ZÅÐÄÖÉÜ]|\s\d\s)', part)
    for sentence in split:
        sentence = sentence.lower() + '.'
        if all([x in sentence for x in stringlist]):
            sentenceRes.append(sentence)
    sentenceString = '.'.join(sentenceRes)
    return sentenceString



def findfirst(stringlist, part):
    sentenceRes = []
    split = re.split('(?=[.]{1}\s[A-ZÅÐÄÖÉÜ1-9]|\s\d\s)', part)
    for sentence in split:
        sentence = sentence.lower()
        if all([x in sentence for x in stringlist]):
            sentenceRes.append(sentence)
    if sentenceRes:
        sentenceString = sentenceRes[0]
    else:
        sentenceString = ''
    return sentenceString



#Main functions
def paths():
    pdf_files = []
    for subdir, dirs, files in os.walk(ROOTDIR, topdown=True):
        for term in EXCLUDE:
            if term in dirs:
                dirs.remove(term)
        for file in files: 
            for term in INCLUDE:
                if term in subdir and file.endswith('.pdf'):
                    
                    (f"Dealing with file {subdir}/{file}")
                    pdf_dir = (os.path.join(subdir, file))
                    pdf_files.append(pdf_dir)
                
    return pdf_files



def topwords_from_jpd(text):
    top = itertools.takewhile(lambda x: len(x) < 50, text)
    out = list(top)

    return out



def cases_from_imgs():
    """
    Retrieve text information from "scanned" documents in JPG (picture) form
    Assumes documents in folder are in order, meaning first page of case is 
    followed by second page etc (like docs named Sodertorns1, Sodertorns2,...)
    Returns list of dictionaries through which execution loops and passes each
    dictionary to main function
    
    Notes:
    - Initialize case within loop to clear fulltext_form column, otherwise text
    of previous cases is still saved in fulltext_form
    - Take start == 1 as condition into elif statements so that pages are only processed
    if the code already found a first page, this is to not process PROTOKOLL or other
    non-DOM pages
    """
    start = 0
    cases = []

    for subdir, dirs, files in os.walk(ROOTDIR, topdown=True):
        for term in EXCLUDE:
            if term in dirs:
                dirs.remove(term)
        for file in files:
            for term in INCLUDE:
                if term in subdir and file.endswith('.JPG'):
                    print(f"\nReading file {subdir}/{file}")

                    pdf_dir = (os.path.join(subdir, file))
                    text, _, judge_small, judge_large = ocr_main(file)
                    text = [item for sublist in text for item in sublist]
                    
                    #First page
                    if (
                            start == 0
                            and len([x for x in text if "DOMSLUT" in x]) >= 1
                        ):
                        
                        start = 1
                        page_count = 1
                        case = {'fulltext_form': [], 'topwords': []}
                        case['fulltext_form'].append(text.copy())
                        case['firstpage_form'] = text.copy()
                        case['topwords'].append(topwords_from_jpd(text).copy())
                   
                    #Last page
                    elif (
                            start == 1
                            and len([x for x in text if "ÖVERKLAG" in x]) >= 1
                            and not 'notfinal' in file
                            or start == 1
                            and 'last' in file
                          ):
                        
                        start = 0
                        page_count += 1
                        case['fulltext_form'].append(text.copy())
                        case['lastpage_form'] = text.copy()
                        case['judge_string'] = text[-2:]
                        case['filepath'] = pdf_dir
                        case['page_count'] = page_count
                        case['topwords'].append(topwords_from_jpd(text).copy())
                        
                        cases.append(case.copy())
                    
                    #In between page
                    elif start == 1:
                        
                        page_count += 1
                        case['fulltext_form'].append(text.copy())
                        case['topwords'].append(topwords_from_jpd(text).copy())

    return cases



def read_file(file):
    pages_text_formatted = []
    page_count= 0
    
    def filereader_params():
        rsrcmgr = PDFResourceManager()
        retstr = io.StringIO()
        laparams = LAParams(line_margin=3)
        device = TextConverter(rsrcmgr, retstr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        return retstr,interpreter

    def appendix_pages(no_of_firstpage):      
        appendix_pageno = appendix[-1]
        fulltext_form = pages_text_formatted[no_of_firstpage:(appendix_pageno)]
        return appendix_pageno, fulltext_form
    
    def text_parts(no_of_firstpage):
        firstpage_form = pages_text_formatted[no_of_firstpage]
        fulltext_form = pages_text_formatted[no_of_firstpage:]
        return fulltext_form, firstpage_form
        
    retstr, interpreter = filereader_params()
    
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,caching=True,check_extractable=True):
            read_position = retstr.tell()
            interpreter.process_page(page)
            retstr.seek(read_position, 0)
            page_text = retstr.read()
            pages_text_formatted.append(page_text)
            page_count += 1
    
    firstpage_form = pages_text_formatted[0]
    appendix = [k for k, item in enumerate(pages_text_formatted) if re.search(appendix_start, item)]
    appendix_pageno = len(pages_text_formatted)
    lastpage_form = pages_text_formatted[appendix_pageno-1]
    
    if "Rättelse" in firstpage_form:
        correction = 1
        firstpage_form = ''.join(pages_text_formatted[1])
        fulltext_form, firstpage_form = text_parts(1)
        if appendix:
            appendix_pageno, fulltext_form= appendix_pages(1)
            lastpage_form = pages_text_formatted[appendix_pageno-1]
    else:
        correction = 0
        fulltext_form, firstpage_form = text_parts(0)
        if appendix:
            appendix_pageno, fulltext_form = appendix_pages(0)
            lastpage_form = pages_text_formatted[appendix_pageno-1]

    return correction, appendix_pageno, fulltext_form, firstpage_form, lastpage_form, page_count



def get_ocrtext(full_text, header):
    """
    Use OCR fulltext and header to return first page, topwords, judge, fulltext formatted and cleaned
    """
    firstpage_form = ''.join(full_text[0])
    page_count = len(full_text)
    judge_string = ''.join(full_text[-1][-2:]) if len(full_text[-1]) >= 2 else full_text[-1][-1]
    lastpage_form = ''.join(full_text[-1])
    fulltext_form = ''.join(list(itertools.chain.from_iterable(full_text)))
    topwords_form = ''.join(list(itertools.chain.from_iterable(header)))
    topwords_form, firstpage_form, fulltext_form, judge_string = clean_ocr(topwords_form, firstpage_form, fulltext_form, judge_string)
    topwords_og, topwords = format_text(topwords_form)
    
    return fulltext_form, firstpage_form, judge_string, topwords, page_count, lastpage_form



def clean_ocr(topwords, firstpage_form, fulltext_form, judge_string):
    """
    Correct common spelling mistakes that OCR outputs
    Correct topwords for first 20 words of first page if bounding boxes on first page are the entire text
    """
    topwords_list = topwords.split()
    topwords = ' '.join(topwords_list[:100]) if len(topwords_list) > 100 else topwords
    
    for old, new in OCR_CORR.items():
        topwords = topwords.replace(old, new)
        firstpage_form = firstpage_form.replace(old, new)
        fulltext_form = fulltext_form.replace(old, new)
        judge_string = judge_string.replace(old, new)

    return topwords, firstpage_form, fulltext_form, judge_string



def format_text(unformatted):
    og = ' '.join((''.join(unformatted)).split())
    lower = og.lower()

    return og, lower



def get_header(firstpage_form):
    
    """
    Splits first page into a header, ie the part after topwords and before ruling starts
    Notes:
    - header2.insert(1, 'Kärande') for rulings without 'Parter', otherwise defendant 
    string includes ruling
    """
    try:
        header1 = (re.split('(DOMSLUT|Domslut\n|SAKEN\n)', firstpage_form))[0]
        for term in ['PARTER','Parter', 'Kärande', 'KÄRANDE']:
            header2 = header1.split(term)
            if any([x in term for x in ['Kärande', 'KÄRANDE']]) and len(header2) > 1:
                header2.insert(1, 'Kärande')
            if len(header2) != 1:
                break
        header = ''.join(header2[1:])
    except IndexError:                
        try:
            header = re.split('Mål ', re.split('_{10,40}', firstpage_form)[0])[1] 
        except IndexError:
            try:
                header = ''.join(firstpage_form.split('')[0:20])
            except IndexError:
                header = ''.join(firstpage_form)

    return header



def get_topwords(firstpage_form):
    try:
        topwords = ' '.join(firstpage_form.split()[0:20]).lower()
    except IndexError:
        topwords = ''.join(firstpage_form.lower())

    return topwords



def get_lastpage(fulltext_form, lastpage_form):
    for page in fulltext_form:
        for term in ['\nÖVERKLAG','\nÖverklag','\nHUR MAN ÖVERKLAG',
                     '\nHur man överklag','\nHur Man Överklag',
                     'Anvisning för överklagande']:
            if term in page:
                lastpage_sorted = page
                break
            else: 
                lastpage_sorted = '.'.join(lastpage_form.split("."))
        else:
            continue
        break
    return lastpage_sorted



def get_plaint_defend(part, readable):
    """
    Extract plaintiff and defendant boxes from first page (including lawyer info if applicable)
    for readable and scanned docs
    """
    
    print_output("Part for parties", part)
    
    try:
        defend_og = re.split('Svarande|SVARANDE', part)[1] 
        plaint_og = re.split('Kärande|KÄRANDE', (re.split('Svarande|SVARANDE', part)[0]))[1]
        if defend_og == "":
            defend_og = re.split('Svarande|SVARANDE', part)[2] 
        elif len(plaint_og.split()) < 4:
            defend_og = re.split("(?i)SVARANDE och KÄRANDE|SVARANDE OCH GENKÄRANDE ", part)[1]
            plaint_og = re.split('(?i)KÄRANDE och SVARANDE|KÄRANDE OCH GENSVARANDE', 
                                       (re.split("SVARANDE och KÄRANDE|SVARANDE OCH GENKÄRANDE ", part)[0]))[1]
    except IndexError:
        try:
            defend_og = re.split(defend_search, part)[1]
            plaint_og = re.split('Kärande|KÄRANDE|Hustrun|HUSTRUN', (re.split(defend_search, part)[0]))[1]
            if defend_og == "":
                defend_og = re.split(defend_search, part)[2]
        except IndexError:
            try:
                first = part.split('1.')[1]
                defend_og = first.split('2.')[1]
                plaint_og = first.split('2.')[0]
            except IndexError:
                try:
                    if readable == 0 and 'Kärande' not in part or 'KÄRANDE' not in part:
                        defend_og = re.split('Svarande|SVARANDE', part)[1]
                        plaint_og = re.split('Svarande|SVARANDE', part)[0]
                except IndexError:
                    defend_og = plaint_og = 'not found, not found'
                    flag.append('plaintiff_and_defendant_not_found')

    defend_og = defend_og.strip(' _\n')
    defend = defend_og.lower()
    plaint = plaint_og.lower()

    return defend, defend_og, plaint, plaint_og



def party_id(party_og):
    """
    Get full name, first name, ID number for plaintiff and defendant
    """
    if ',' in party_og:
        full = (party_og.split(",")[0]).lower()
    else:
        full = (party_og.split("\n")[1]).lower()
    first = [x.strip('\n') for x in re.split('-|[(]|[)|\s]', full)[:-1]]
    first = [x for x in first if x] #delete empty strings from list
    try:
        number = ''.join(searchkey(id_pattern, party_og.lower(), 2).split())
    except AttributeError:
        number = "-"
    
    print_output("Party OG",party_og.split("."))
    print_output("First",first)
    print_output("Number",number)

    return full, first, number



def get_judge(doc_type, fulltext_og, fulltext, lastpage_form):
    """
    Extracts judge name and title from readable documents
    """
    if doc_type == 'slutligt beslut' or doc_type == 'protokoll':
        judge_name = dictloop(judgetitle_search, fulltext_og, 2, ['telefon','telefax'])
        judge_title = dictloop(judgetitle_search, fulltext_og, 1, ['telefon','telefax'])
        if judge_name is None:
            try:
                judge_name = (((dictloop(judgesearch, lastpage_form, 1,['telefon','telefax'])).split('\n'))[0])
            except:
                judge_name = fulltext.split('.')[-1]

    elif doc_type == 'dom' or doc_type == 'deldom':
        judge_title = "N/A"

        try:
            judge_name = ((dictloop(judgesearch, lastpage_form, 1, exclude_judge)).split('\n'))[0]
            judge_name = judge_name.lower().strip()

        except AttributeError:
            try:
                finalpart = re.split('ÖVERKLAG|Överklag|överklag', lastpage_form)[-1]
                judge_name = ((dictloop(judgesearch_noisy, finalpart, 1, exclude_judge)).split('\n'))[0]
                judge_name = re.split('\s{4,}|,', judge_name)[0]
                judge_name = judge_name.lower().strip().strip('/').strip('|')
            except:
                judge_name = 'Not found'

    else:
        judge_name = "Not found" 

    return judge_name, judge_title



def get_judge_scans(judge1, judge2, judge3):
    """
    Gets judges name from scanned documetn by going through different text
    parts, judge1 = judge_string, judge2 draws tight bounding boxes wiht 9x9
    kernal in OCR module around text and parses the text in those tight boxes,
    judge3 parses as much text as it can get from the whole page without any
    boxes.
    
    Code then takes list of digital judges generated with STATA, compares string
    in judge1/2/3 list with each name and at similarity CUTOFF = 70 AND 
    assigns judge_name = match
    """
    alljudges = judge1.split(',') + judge2 + judge3 # THIS SPLITS TOO MUCH
    judge_title = 'N/A'
    found = 0
    cutoff = 70
    
    print("Judge String: ", alljudges)

    digital_judges = pd.read_excel(JUDGE_LIST)
    
    for _, row in digital_judges.iterrows():
        
        match = row['judge']
        match1 = process.extract(match, alljudges)
        highest_match = sorted(match1, key=lambda x: x[1], reverse = True)
        highest_match = highest_match[0] #isolate score of highest match
        
        if highest_match[1] > cutoff and len(highest_match[0]) > 5:
            comp_match = fuzz.partial_ratio(match, highest_match[0])
            if comp_match > cutoff:
                judge_name = match
                found = 1
                print(match, highest_match)

    if found == 0:
        try:
            print("try1")
            judge_name = ((dictloop(judgesearch, judge1, 1,
                                 exclude_judge)).split('\n'))[0]
            judge_name = judge_name.lower().strip()
        except:
            print("except1")
            judgepage = ' '.join(judge2)
            judge_name = judgepage.replace("\n", " ")

    print("Judge name: ", judge_name)
    return judge_name, judge_title



def basic_caseinfo(file, topwords):
    """
    Extracts information relevant to all types of documents: 
        1) case id 
        2) doc type (dom,deldom,slutligt beslut, dagbok, protokoll) 
        3) court name
        4) case date, case year
    """
    courtname = re.split('\W',file.split('/')[4])[0]
    try:
        date = dictloop(date_search, topwords, 1, [])
        year = re.sub('[^0-9]', '', date[:4])
        if year[0] == "0" and len(year) == 3:
            year = "2" + year
        elif year[0] == "0" and len(year) == 2:
            year = "20" + year
    except:
        date = "Not found"
        year = 0
    print_output("Getting Case No",topwords.split("."))

    try:
        caseno = ''.join((dictloop(caseno_search, topwords, 2, [date])).split())
        print_output("Case No 1",caseno)
    except AttributeError:
        caseno = searchkey('T.?\s*(\d*-\d*)', file, 1)
        if not caseno:
            caseno = "Not found"
        print_output("Case No 2",caseno)

    return caseno, courtname, date, year



def get_doctype(file, topwords, fulltext_og):
    filename = file.lower() 

    if 'dagbok' in topwords:
        doc_type = 'dagbok'
    elif 'protokol' in topwords:
        doc_type = 'protokoll'
    elif 'TLIGT BESLUT' in fulltext_og or 'slutligt beslut' in filename:
        doc_type = 'slutligt beslut'
    elif 'deldom' in topwords or 'deldom' in filename or 'mellandom' in filename or 'mellandom' in topwords:
        doc_type = 'deldom'
    elif ' dom ' in filename or ' dom.' in filename or ' dom;' in filename or 'dom ' in topwords:
        doc_type = 'dom'
    elif 'all_scans' in filename:
        doc_type = 'dom'
    else:
        doc_type = 'Not found'
    return doc_type



def get_casetype(defend, plaint, fulltext_og, ruling, firstpage_form):
    """
    Get type of custody ruling:
    1216A = custody battles of non-divorcing parents
    1216B = legal guardian case
    1217A = divorce with custody battles
    1217B = divorce only cases
    """
    fulltext = fulltext_og.lower()
    firstpage = firstpage_form.lower()
    
    if (
            any([x in defend for x in legalguardian_terms])
            or any([x in plaint for x in legalguardian_terms])
            or any([x in fulltext for x in ['overflyttas','ensamkommande flyktingbarn']])
            or 'vårdnadshavare' in findterms(['förordnad'], fulltext_og)
            ):
        
        case_type = '1216B'
        
    elif (
            'de har inga gemensamma barn' in fulltext
            or list(filter(lambda x:'äktenskaps' in x, [ruling, firstpage]))
            and any([x in findterms(['vård'], firstpage) for x in remind_key])
            ):

        case_type = '1217B'
    
    elif list(filter(lambda x:'äktenskaps' in x, [ruling, firstpage])):
        case_type = '1217A'

    elif any([x in ruling for x in ['vård', 'umgänge', 'umgås']]):
        case_type = '1216A'
        
    else:
        case_type = 'Not found'

    return case_type



def get_ruling(fulltext_form):
    """
    Extract only ruling text headed usually 'Domslut'
    """
    try:
        ruling_form = ''.join(re.split('MSLUT|Domslut\n', ''.join(fulltext_form))[1:])
        print_output("Ruling 1","")
    except AttributeError:
        ruling_form = ''.join(re.split('_{10,40}\s*', ''.join(fulltext_form))[1:])
        print_output("Ruling 2","")
    try:
        ruling_form = ''.join(re.split('[A-ZÅÄÖÜ]{4,}\s*\n*TINGSRÄTT',ruling_form))
        print_output("Ruling 1a","")
    except AttributeError:
        ruling_form = ''.join(re.split('\n\n[A-ZÅÄÖÜ]{1}[a-zåäüö]{3,]\s*\n*Tingsrätt',ruling_form))
        print_output("Ruling 2a","")
    ruling_form = ''.join(re.split('DELDOM|DOM',ruling_form))
    ruling_form = re.split(dictloop(ruling_search,ruling_form,0,[]), ruling_form)[0]
    
    try:
        if searchkey('\d\d\s*–\s*\d\d', ruling_form, 0):
            ruling1 = re.sub('\s*–\s*','–',ruling_form)
            ruling2 = re.sub('\s*–\n','–',ruling_form)
            print_output("Ruling 3", "")
        else:
            ruling1 = re.sub('\s*-\s*','-',ruling_form)
            ruling2 = re.sub('\s*-\n','-',ruling_form)
            print_output("Ruling 4","")
        ruling_og = ' '.join(''.join(ruling2).split())
        
    except AttributeError:
        ruling_og = ' '.join(''.join(re.split('(YRKANDEN|Yrkanden)', ruling_form)[0].lower() ).split())
        if searchkey('\d\d\s*–\s*\d\d', ruling1, 0):
            ruling_og = re.sub('\s*–\s*','–',ruling_og)
            ruling_og = re.sub('\s*–\n','–',ruling_og)
            print_output("Ruling 3a","")
        else:
            ruling_og = re.sub('\s*-\s*','-',ruling_og)
            ruling_og = re.sub('\s*-\n','-',ruling_og)
            print_output("Ruling 4","")
            
    ruling = ruling_og.lower()
    print_output("Ruling",ruling)
    
    return ruling_form, ruling_og, ruling



def get_domskal(fulltext_og, ruling_form):
    """
    Extract domskal chapter from ruling which gives reasoning for ruling,
    if there is no domskal chapter get most similar background chapter
    """
    try:
        domStart = re.split('DOMSKÄL|Domskäl', fulltext_og)[1]
    except IndexError:
        try:
            domStart = re.split('BEDÖMNING|Tingsrättens bedömning', fulltext_og)[1]
        except IndexError:
            try:
                domStart = re.split('Yrkanden |Parternas Begäran M.M.|Yrkande M.M.|YRKANDEN |YRKANDE M.M.|PARTERNAS BEGÄRAN ', fulltext_og)[1]
            except IndexError:
                try:
                    domStart = re.split('\nSkäl\s*\n', ruling_form)[1]
                except IndexError:
                    domStart = ruling_form

    domskal_og = re.split('överklag|Överklag|ÖVERKLAG', domStart)[0]
    domskal = domskal_og.lower()
    
    return domskal_og, domskal



def get_childnos(ruling_og, year):
    """
    Search for ID numbers in ruling (would only be given for kids) and return
    dict with ID as index, names for each index added in get_childname
    """
    childid_name = {}

    childnos = re.findall('\d{6,8}\s?.\s?\d{3,4}', ruling_og.lower())
    childnos = [x.replace(' ', '') for x in childnos]
    childnos = set(childnos)

    for num in childnos:
        if len(re.split('\D', num)[0]) == 8:
            childyear = num[:4]
        else:
            childyear = '19'+num[:2] if int(num[:2])>40 else '20'+num[:2]
        age = int(year) - int(childyear)
        
        if 0 < age < 18:
            childid_name[num] = ''

        print_output("childid_name",childid_name)

    return childid_name



def get_childname(year, ruling_og, defend_full, plaint_full):
    """
    Extract child ID's first from ruling, if not found there from full text,
    otherwise get child's name and use that as ID
    """
    childid_name = get_childnos(ruling_og, year)
    names = []
    
    if childid_name:

        sentence_parts = re.split('(?=[.]{1}\s[A-ZÅÐÄÖÉÜ])..|\d\s*,|\s[a-z]', ruling_og)

        for i in childid_name:
            sentence = ''.join([x for x in sentence_parts if i[:-1] in x])
            childid_name[i] = ''
            for word in sentence.split():
                if (
                    word[0].isupper()
                    and not any([x in word.lower() for x in defend_full.split()])
                    and not any([x in word.lower() for x in plaint_full.split()])
                    ):

                    names.append(word)

            child_first = [x for x in names if x[0:3].upper() == x[0:3]]

            if not child_first:
                child_first = names[0].lower()
            else:
                child_first = child_first[0].lower()

            child_first = child_first.replace(',', '')
            childid_name[i] = child_first
            names.clear()

    if not childid_name:

        custody_sentences = []
        sentence_parts = re.split('(?=[.]{1}\s[A-ZÅÐÄÖÉÜ])..', ruling_og)
        for sentence in sentence_parts:
            if 'vård' in sentence or 'Vård' in sentence:
                custody_sentences.append(sentence)

        custody_sentences = ('.'.join(custody_sentences)).split(' ')[1:]
        custody_sentences = [x for x in custody_sentences if x]

        for word in custody_sentences:
            word = word.strip()

            if (
                word[0].isupper()
                and not any([x in word.lower() for x in defend_full.split()])
                and not any([x in word.lower() for x in plaint_full.split()])
                or word == 'och'
                ):
                names.append(word)

            elif word[-1] == ',':
                names.append(word.strip()[-1])

        names = re.split(',|och', ' '.join(names))
        names = [x for x in names if x.strip()]

        for name in names:
            name = name.split()[0]
            childid_name[name] = name

    childid_name = {'not found':'not found'} if not childid_name else childid_name

    return childid_name



def part_ruling(topwords):
    part_rul = 1 if 'deldom' in topwords else 0
    print_output("Topwords",topwords.split("."))

    return part_rul



def lawyer(plaint, defend, defend_first, fulltext_og, domskal_og):
    """
    Get dummies for whether plaintaiff and defendant have a lawyer
    If defendant has a lawyer get defendant's adress, city, and dummy for whether lawyer is a god man (legal representative)
    """
    plaint_lawyer = 1 if any([x in plaint for x in lawyer_key]) else 0
    
    for term in lawyer_key:
        if term in defend:
            defend_godman = 1 if 'god man' in term else 0
            defend_lawyer = 1 
            defend_address = re.split(term, defend)[0]
            if 'medbor' in defend_address:
                defend_address = ' '.join(re.split(citizen,defend_address))
            defend_city = ''.join((defend_address.strip(' _\n')).split(' ')[-1])
            break
        else:
            defend_godman = 1 if 'c/o' in defend else 0
            defend_lawyer = 0
            defend_address = defend
            defend = defend.split('\nsaken ')[0] if '\nsaken ' in defend else defend
            defend_city = ''.join((defend.strip(' _\n')).split(' ')[-1])
            
    def get_defendabroad():
        """
        Get information on whether defendant is located abroad
        - didnt include defend_first because defend might be referred to by Han
        """
        if (
                any([x in defend_city for x in cities]) 
                and not any([x in defend_address.lower() for x in lawyer_key])
                ):
            
            print_output("Abroad 0","")
            defend_abroad = 0
            
        elif (
                any([x in defend_city for x in countries]) or 'okänd' in defend
                or defend_godman == 1  and 'saknar kän' in defend
                or defend_city.isdecimal() or '@' in defend_city
                or defend_godman == 1 and any(x in findterms(['inte', 'sverige'], fulltext_og) for x in defend_first)
                or defend_godman == 1 and findterms(['befinn', 'sig','utomlands'], fulltext_og)
                or defend_godman == 1 and any([x in findterms(['befinn', 'sig'], fulltext_og) for x in countries])
                or any([x in findterms(['befinn', 'sig', 'sedan'], domskal_og) for x in countries])
                or any(x in findterms(['flytta', 'till', 'inte', 'sverige'], fulltext_og) for x in defend_first)
                or defend_godman == 1 and any([x in findterms(['återvänt', 'till'], fulltext_og) for x in countries])
                or any(x in findterms(['försvunnen'], fulltext_og) for x in defend_first)
                or any(x in findterms(['bortavarande', 'varaktigt'], fulltext_og) for x in defend_first)
                or any(x in findterms([' bor ', ' i '], fulltext_og) for x in defend_first)
                and any(x in findterms([' bor ', ' i '], fulltext_og) for x in countries) 
                and not findterms([' bor ', ' i ', 'barn'], fulltext_og)
                ):
            
            print_output("Abroad 1 (defend city)",defend_city)
            print_output("Abroad 2",defend_godman == 1  and 'saknar kän' in defend)
            print_output("Abroad 3",defend_city.isdecimal() or '@' in defend_city)
            print_output("Abroad 4",any(x in findterms(['inte', 'sverige'], fulltext_og) for x in defend_first))
            print_output("Abroad 5",findterms(['befinn', 'sig','utomlands'], fulltext_og))
            print_output("Abroad 6",any([x in findterms(['befinn', 'sig'], fulltext_og) for x in countries]))
            print_output("Abroad 7",any([x in findterms(['befinn', 'sig', 'sedan'], domskal_og) for x in countries]))
            print_output("Abroad 8",any(x in findterms(['flytta', 'till', 'inte', 'sverige'], fulltext_og) for x in defend_first))
            print_output("Abroad 9",any([x in findterms(['återvänt', 'till'], fulltext_og) for x in countries]))
            print_output("Abroad 10",any(x in findterms(['försvunnen'], fulltext_og) for x in defend_first))
            print_output("Abroad 11",any(x in findterms(['bortavarande', 'varaktigt'], fulltext_og) for x in defend_first))
            print_output("Abroad 12",any(x in findterms([' bor ', ' i '], fulltext_og) for x in defend_first) and any(x in findterms([' bor ', ' i '], fulltext_og) for x in countries) and not findterms([' bor ', ' i ', 'barn'], fulltext_og))

            defend_abroad = 1

        else:
            defend_abroad = 0

        return defend_abroad

    defend_abroad = get_defendabroad()  

    return plaint_lawyer, defend_lawyer, defend_godman, defend_abroad



def secret_address(party):
    """
    Dummy whether defendant or plaintiff's address is secret
    Input plaint or defend for party
    """
    secret_party = 1 if 'sekretess' in party else 0
    return secret_party



def defend_unreachable(defend_first, defend_godman, fulltext_og):
    """
    Get info whether defendant is reachable
    In reachable: Took out genom sin gode man because this must not mean that SV and God Man were in contact (see 396-15)
    """
    for name in defend_first:
        unreach_key = [['okontaktbar'],['förordnat god man', name],['varken kan bestrida eller medge'],
                      ['någon kontakt', 'huvudman'],['någon kontakt', name],['okän', 'befinn',name],
                      [name, 'avsaknad',' av ',' instruktioner',' från']]    
        
        for term in unreach_key:
            if findterms(term, fulltext_og):
                unreach = 1
                found = 1
                break
            else:
                unreach = 0
                found = 0

        unreach = 1 if defend_godman == 1 else unreach
        reachable = [[name, 'kontakt ', 'med']]

        for part in reachable:
            if found == 0 and findterms(part, fulltext_og) and not any([x in findterms(part, fulltext_og) for x in nocontant]):
                unreach = 0
        else:
            continue
        break

    return unreach



def separation_year(fulltext_og, fulltext):
    separate = searchkey('separerade under (\d{4})', fulltext, 1)
    if not separate:
        for term in separation_key:
            if term in fulltext:
                separate = searchkey('(\d{4})', findterms([term], fulltext_og), 0)
                separate = '-' if separate == None else separate
                break
            else:
                separate = '-'
    return separate



def get_outcome(fulltext_og, ruling_og, ruling, firstpage_form, child_id, child_first, plaint_first, defend_first):
    """
    Get the ruling/outcomeo of the case:
        1 = shared custody
        2 = custody with plaintiff 
        3 = custody with defendant
        4 = case dismissed
    Notes:
    - "lämnas utan bifall" in findVard because if I search in ruling only it picks up when umgange claims or so are dismissed
    - replaces gemensamm with gemensa so that I can search for gemensam. and gemensamt without picking up on gemensamme barn
    """
    findVardn = findterms(['vård', child_id], ruling_og)
    findVardn = findterms(['vård'], ruling_og) if not findVardn else findVardn
    findVardn = findVardn.replace('gemen-sam', 'gemensam') if 'gemen-sam' in findVardn else findVardn
    findVardn = findVardn.replace('gemensamme ', 'gemensa') if 'gemensamm' in findVardn else findVardn
    findVardn = findVardn.strip('2. ') + ' '
    
    #Dismissed or no custody ruling
    if (
            'käromalet ogillas' in ruling_og
            or 'käromålet ogillas' in ruling_og
            or findterms(['avslås', 'vårdn'], ruling_og)
            or findterms([' lämna',' utan ',' bifall'], findVardn)
            or 'avskriv' in findVardn or findterms(['lämnas utan bifall', 'talan'], ruling_og)
            ): 
        
        out = 4  

    elif (
            'vård' not in ruling and 'vård' not in firstpage_form.lower()
            or any([x in findVardn for x in remind_key]) and 'äktenskaps' in ruling
            or 'vård' not in findterms([child_first], ruling_og) and child_first != 'not found'
            ): 
        
        out = 0

    else:
        out = 999

    #One plaint is dismissed and another installed
    if any([ x in findterms([' ensam', 'gemensam ', 'vårdn'], findVardn) for x in reject_outcome]):
        newRuling = []
        out = 999
        for part in re.split(',|;',findVardn):
            if not any([x in part for x in reject_outcome]):
                newRuling.append(part)
        findVardn = ''.join(newRuling)
    
    anyVardn = not any([x in findVardn for x in reject_outcome])

    def outcome_search(searchterms, findwhere, exclude, out):
        for part in searchterms:
            if findterms(part, findwhere) and exclude:
                result = out
                break
            else:
                result = 999
                continue
        return result

    #Shared custody 
    sharedCustody = [
        ['ska','tillkomma','tillsammans'],
        [child_id,'gemensam','ska','tillkomma'], 
        [child_id,'gemensam','ska','om'],
        [child_id,'gemensam','fortsätt','ska'],
        [child_id,'gemensam','alltjämt','ska'],
        [child_id,'gemensam','alltjämt', 'är'],
        [child_id,'gemensam','anförtro'],
        [child_id, 'gemensamma vård']
        ]
    
    if out not in {0,4}: 
        out = outcome_search(sharedCustody, findVardn, anyVardn, 1)
    
    #Sole custody
    if out not in {0,1,4}:
        for name1 in plaint_first:
            soleCustody = [
                [child_id, name1,' ensam'],
                [child_id,'över','flytt', 'till ' + name1],
                [child_id, name1,'tillerkänn'],
                [child_id, name1,'anförtro'],
                [child_id, name1, 'ska','tillkomma'],
                [child_id,name1,' ska',' om ', ' ha ']
                ]  
            out = outcome_search(soleCustody, findVardn, anyVardn, 2) 
            if out == 2:
                break

    if out not in {0,1,2,4}:
        for name in defend_first:
            soleCustody = [
                [child_id, name,' ensam'],
                [child_id,'över','flytt', 'till ' + name],
                [child_id, name,'tillerkänn'],
                [child_id, name,'anförtro'],
                [child_id, name, 'ska','tillkomma'],
                [child_id,name,' ska',' om ', ' ha ']
                ]    
            out = outcome_search(soleCustody, findVardn, anyVardn, 3)  
            if out == 3:
                break

    if out == 999:
        out = 4 if findterms(['avskr','vård'], fulltext_og) or findterms(['skrivs', 'av'], fulltext_og) else out

    return out



def get_visitation(child_first, ruling_og):
    """
    Get ruling on visitation rights
    Notes:
    - Took out summer exclusion because that gave too many false negatives where visitation was defined for the weeks
    AND the summer, could potentially include phys=0 if semester in phys and NOT any weekday term in semester sentence
    """
    for term in [child_first, 'barn']:
        for key in visitation_key:

            if (    
                    findterms(['avslås', key], ruling_og)
                    or findterms([' lämna',' utan ',' bifall', key], ruling_og)
                    or findterms([key, 'avskriv'], ruling_og)
                    ):
                print_output("Visitation 1","")
                visit = 4  
                break

            elif findfirst([key, term], ruling_og) and not any([x in findfirst([key, term], ruling_og) for x in reject]):
                print_output("Visitation 2","")
                visit = 1
                break
            
            else:
                print_output("Visitation 3",findfirst([key, term], ruling_og))
                visit = 0

        else:
            continue
        break
    
    return visit



def get_physicalcustody(ruling_og, ruling, plaint_first, defend_first, child_first):
    """
    Extract ruling outcome on physical custody if present in case
    Notes:
    - searched in first sentences rather than ruling because otherwise code finds a sentence about physical agreement
    that does not directly describe the ruling and where another parent's name is included
    """
    firstsentences = ''.join(ruling.split('.')[:6])
    
    for term in physicalcust_list:
        if (
                findfirst([child_first, 'avslås'], findfirst(term, firstsentences))
                or findfirst([child_first, ' lämna',' utan ',' bifall'], findfirst(term, firstsentences))
                or findfirst([child_first, 'avskriv'], findfirst(term, firstsentences))
                ): 
            phys = 4  
            break
        
        elif (
                child_first in findfirst(term, firstsentences)
                and any([x in findfirst(term, firstsentences) for x in plaint_first])
                and not any([x in findfirst(term, firstsentences) for x in exclude_phys])
                ):
            phys = 1
            break
        
        elif (
                child_first in findfirst(term, firstsentences)
                and any([x in findfirst(term, firstsentences) for x in defend_first])
                and not any([x in findfirst(term, firstsentences) for x in exclude_phys])
                ):
            phys = 2
            break
        
        else:
            phys = 0
            
    return phys



def get_alimony(ruling_og):
    if findterms(['underhåll'], ruling_og) and not any([x in findterms(['underhåll'], ruling_og) for x in reject]):
        alimony = 1
    elif findterms(['bilaga', 'sidorna'],  ruling_og):
        alimony = 999                    
    else:
        alimony = 0
    return alimony



def get_otherrulings(defend_first, plaint_first, fulltext_og):
    """
    Get information on additional potentially related rulings, in this case whether parent has the right
    to stay at the shared residence until the divorce is finalized for instance
    """
    parent_names = defend_first + plaint_first
    
    for name in parent_names:
        if name in findterms(residence_key, fulltext_og):
            otherruling = 1
            break
        else:
            otherruling = 0
            
    return otherruling



def get_agreement(domskal, domskal_og, fulltext, out):
    """
    Returns 2 dummies:
        1) agree_cust = 1 if parties agreed on legal custody ruling
        2) agree_any = 1 if parties agreed on any part of the ruling

    Notes for agreementExclude:
    - potentially include god man and gode mannen, misses cases where the defendant agrees to the ruling through their god man eg Sundsvalls TR T 2022-19 
    - included talan for this case: Eftersom talan har medgetts och då det får anses vara bäst för barnet, ska JCI anförtros ensam vårdnad om sonen.
    - included avgjord for this case: Vid muntlig förberedelse den 26 april 2018 beslutade tingsrätten, i enlighet med en överenskommelse som parterna träffade, att till dess att frågan avgjordes genom dom eller annat beslutades skulle vårdnaden om barnen vara fortsatt gemensam 
    - alla frågor som rör barnen for standard phrasing that expresses this (alternative: föräldrar + inte): Gemensam vårdnad förutsätter inte att föräldrarna är överens om alla frågor som rör barnen, men de måste kunna hantera sina delade meningar på ett sätt som inte drabbar barnen// Joint custody does not require parents to agree on all matters concerning the children, but they must be able to manage their disagreements in a way that is not detrimental to the children
    - potentially include god man and gode mannen, misses cases where the defendant agrees to the ruling through their god man eg Sundsvalls TR T 2022-19 
    """ 
    sentences_domskal = domskal.split('.')
    sentences_all = fulltext.split('.')
    
    # Agreement on legal custody
    for sentence in sentences_domskal:
        if all(any(term in sentence for term in lst) for lst in (agreement_key, agreement_add)) and out not in {0,4}:
            if not any([x in sentence for x in no_vard]) or 'vård' in sentence: #capture sentences (1) that dont refer only to umgange and boende , or (2) referring to vardn, umgange and boende
                
                if any([x in sentence for x in past]) and any([x in sentence for x in agreement_excl]):
                    print_output("Agreement Custody 1",sentence)
                    agree_cust = 1
                    break
                
                if not any([x in sentence for x in agreement_excl]) and not any([x in sentence for x in past]):
                    print_output("Agreement Custody 2",sentence)
                    agree_cust = 1
                    break
        else:
            agree_cust = 0

    # Joint application
    if agree_cust == 0 and findterms(['gemensam', 'ansökan', 'yrkat'], domskal_og):
        agree_cust = 1
    
    # Agreement on any part of the ruling
    for sentence in sentences_all:
        if (
                all(any(term in sentence for term in lst) for lst in (agreement_key, agreement_add)) 
                or all(any(term in sentence for term in lst) for lst in (agreement_key, no_vard))
                ):

            if any([x in sentence for x in past]) and any([x in sentence for x in agreement_excl]):
                print_output("Agreement Any 1",sentence)
                agree_any = 1
                break
            
            if not any([x in sentence for x in agreement_excl]) and not any([x in sentence for x in past]):
                print_output("Agreement Any 2",sentence)
                agree_any = 1
                break
            
        else:
            agree_any = 0
            
    return agree_cust, agree_any



def contested(defend_first, fulltext_og, fulltext):
    """
    Potential alternative to agreement variable; measure whether a true custody battle has taken place
    which means that the plaintiff made a plaint and the defendent contested, rather than agreeing immediately
    """
    for name in defend_first:
        for term in contest_key:
            if name in findterms(term, fulltext_og):
                contested = 1
                break
            else:
                contested = 0

    contested = 1 if not 'medge' in fulltext else contested
    
    return contested
        


def joint_application(firstpage_form, out):
    joint = 1 if 'sökande' in firstpage_form.lower() and 'motpart' not in firstpage_form.lower() and out != 0 else 0
    
    return joint



def get_fastinfo(fulltext, fulltext_og):
    """
    Extract whether fast information has been submitted by a social office
    """
    info = 0
    for term in legalguardian_terms:
        if (
                term in fulltext
                and findterms(['yttra', term], fulltext_og)
                and not any([x in findterms([term], fulltext_og) for x in reject])
                or '6 kap. 20 § andra stycket föräldrabalken' in fulltext
                ): 
            print_output("Fast information 1",findterms(['yttra', term], fulltext_og))
            info = 1
            break
    
    for term in fastinfo_key:
        if (
                any([term in fulltext for term in fastinfo_key])
                and not any([x in findterms([term], fulltext_og) for x in reject])
                ):
            print_output("Fast information 2",term)
            info = 1
            break
        
    return info                       



def get_cooperation(fulltext_og, fulltext):
    for term in cooperation_key:
        sentence = findfirst([term], fulltext_og)
        if term in fulltext and not any([x in sentence for x in reject]):
            coop = 1
            break
        else:
            coop = 0
    return coop



def get_investigation(fulltext, fulltext_og):
    """
    Notes: 
    - search for tingsratt or Tingsratt in fullTextOG to not get the TINGSRATT from header
    """
    found = 0
    invest = 0

    for term in invest_key:
        if (
                term in fulltext
                and not any([x in findterms([term], fulltext_og) for x in reject_invest])
                ):
            print_output("Invest 1",term)
            invest = 1
            found = 1
    
    if (
            found == 0
            and findterms([' utred', 'ingsrätt'], fulltext_og)
            and not any([x in findterms([' utred'], fulltext_og) for x in reject_invest])
            and not findterms(['saknas', 'möjlighet', ' utred'], fulltext_og)
            ):
        print_output("Invest 2","")
        invest = 1
        
    elif (
            found == 0
            and any([x in findterms([' utred'], fulltext_og) for x in legalguardian_terms])
            and not any([x in findterms([' utred'], fulltext_og) for x in reject_invest])
            and not findterms(['saknas', 'möjlighet', ' utred'], fulltext_og)
            ):
        print_output("Invest 3","")
        invest = 1
        
    else:
        for sentence in findterms([' utred'], fulltext_og).split('.'):
            if (
                    found == 0
                    and any([x in sentence for x in outcomes_key])
                    and not any([x in sentence for x in reject_invest])
                    ):
                print_output("Invest 4","")
                invest = 1
                break

    invest = 0 if "11 kap. 1 § so" in fulltext else invest
    
    return invest



def get_mainhearing(fulltext_og):
    
    for term in mainhearing_key:
        if (
                findterms([term], fulltext_og)
                and not any([x in findterms([term], fulltext_og) for x in reject_mainhearing])
                ):
            print_output("Main hearing",term)
            main = 1
            break
        
        else:
            main = 0
    return main



def get_divorce(out, ruling):
    """
    Identify cases that are only about divorce, otherwise a divorce case with no custody
    ruling could not be differentiated from a case where all custody variables are 0
    Notes:
    - potentially also include mellan, used äktenskaps to minimize false 0 because of misspelled äktenskapsskillnad
    """
    if out == 0 and 'äktenskaps' in ruling: 
        divorce = 1
    else:
        divorce = 0
    return divorce



def filldict_rulings(
        data_rulings, child_id, file, page_count, correction, topwords, fulltext_og,
        ruling, plaint_no, defend_no, defend, plaint, defend_first, domskal_og,
        ruling_og, plaint_first, child_first, firstpage_form, domskal, fulltext,
        caseno, courtname, date, year, judge, judgetitle
        ):
    
    # try:
    defend_secret = secret_address(defend)
    plaint_secret = secret_address(plaint)
    part = part_ruling(topwords)
    plaint_lawyer, defend_lawyer, defend_godman, defend_abroad = lawyer(plaint, defend, defend_first, fulltext_og, domskal_og)
    defend_unreach = defend_unreachable(defend_first, defend_godman, fulltext_og)
    out = get_outcome(fulltext_og, ruling_og, ruling, firstpage_form, child_id, child_first, plaint_first, defend_first)
    divorce = get_divorce(out, ruling)
    joint = joint_application(firstpage_form, out)
    visit = get_visitation(child_first, ruling_og)
    phys = get_physicalcustody(ruling_og, ruling, plaint_first, defend_first, child_first)
    alimony = get_alimony(ruling_og)
    agree_cust, agree_any = get_agreement(domskal, domskal_og, fulltext, out)
    fastinfo = get_fastinfo(fulltext, fulltext_og)
    cooperation = get_cooperation(fulltext_og, fulltext)
    investigation = get_investigation(fulltext, fulltext_og)
    separate = separation_year(fulltext_og, fulltext)
    mainhear = get_mainhearing(fulltext_og)
    error = 0

    # except Exception as e:
    #    print_output("Error",e)
    #    error = 1

    data_rulings['file_path'].append(file)
    
    if error == 0:
        child_id = child_id.replace(' ','')
        data_rulings['child_id'].append(child_id)
        data_rulings['page_count'].append(page_count)
        data_rulings['correction_firstpage'].append(correction)
        data_rulings['case_no'].append(caseno)
        data_rulings['judge'].append(judge)
        data_rulings['court'].append(courtname)
        data_rulings['date'].append(date)
        data_rulings['deldom'].append(part)
        data_rulings['divorce_only'].append(divorce)
        data_rulings['joint_application_custody'].append(joint)
        data_rulings['plaintiff_id'].append(plaint_no) 
        data_rulings['defendant_id'].append(defend_no)   
        data_rulings['defendant_address_secret'].append(defend_secret)  
        data_rulings['plaintiff_address_secret'].append(plaint_secret)  
        data_rulings['plaintiff_lawyer'].append(plaint_lawyer) 
        data_rulings['defendant_lawyer'].append(defend_lawyer)
        data_rulings['defendant_abroad'].append(defend_abroad)
        data_rulings['defendant_unreachable'].append(defend_unreach)
        data_rulings['outcome'].append(out)   
        data_rulings['visitation'].append(visit)
        data_rulings['physical_custody'].append(phys)
        data_rulings['alimony'].append(alimony)                
        data_rulings['agreement_legalcustody'].append(agree_cust)    
        data_rulings['agreement_any'].append(agree_any)  
        data_rulings['fastinfo'].append(fastinfo)          
        data_rulings['cooperation_talks'].append(cooperation)
        data_rulings['investigation'].append(investigation)
        data_rulings['separation_year'].append(separate)
        data_rulings['mainhearing'].append(mainhear)
        data_rulings['flag'].append(flag)

    else: 
        for i in data_rulings:
            data_rulings[i].append('error')

    return data_rulings



def filldict_register(
        data_register, case_type, defend_no, plaint_no, date,
        courtname, doc_type, caseno, judge, judgetitle, file
        ):
    data_register['casetype'].append(case_type)
    data_register['filepath'].append(file)
    data_register['judge'].append(judge)   
    data_register['judgetitle'].append(judgetitle) 
    data_register['defendant'].append(defend_no)            
    data_register['plaintiff'].append(plaint_no)
    data_register['date'].append(date)
    data_register["court"].append(courtname)
    data_register['type'].append(doc_type)  
    data_register['caseid'].append(caseno)
    data_register['flag'].append(flag)
    
    return data_register



def save(dictionary, SAVE, COUNT, location):
    df = pd.DataFrame(dictionary)
    with pd.option_context('display.max_rows', None, 'display.max_columns', None): 
        print_output("Output saved:",df)
    if SAVE == 1:
        if COUNT == 1:
            df.to_csv(location, sep = ',', encoding='utf-8-sig', header=True)
        else:
            df.to_csv(location, mode = 'a', sep = ',', encoding='utf-8-sig', header=False)



def main(file, jpgs):
    
    if jpgs == 1:
        outpath = file['filepath'].split('\\')[0]
    else:
        outpath = file.split('\\')[0]
    os.chdir(outpath)
    
    if 'all_cases' in file:
        print('\nReadable: ', file)
        
        correction, appendix_pageno, fulltext_form, firstpage_form, lastpage_form, page_count = read_file(file)
        topwords = get_topwords(firstpage_form)
        readable = 1
        
    elif jpgs == 1:
        print('\nImage file: ',file['filepath'])

        fulltext_form = file['fulltext_form']
        fulltext_form = ' '.join([item for sublist in fulltext_form for item in sublist])        
        firstpage_form = ' '.join(file['firstpage_form'])
        judge_string = ' '.join(file['judge_string'])

        topwords = file['topwords']
        topwords = (' '.join([item for sublist in topwords for item in sublist])).lower()        
        page_count = file['page_count']
        lastpage_form = ' '.join(file['lastpage_form'])
        file = file['filepath']

        topwords, firstpage_form, fulltext_form, judge_string = clean_ocr(topwords, firstpage_form, fulltext_form, judge_string)
        correction = 0
        readable = 0

    elif 'all_scans' in file:
        print('\nScan: ', file)

        full_text, header, judge_small, judge_large = ocr_main(file)
        fulltext_form, firstpage_form, judge_string, topwords, page_count, lastpage_form = get_ocrtext(full_text, header)
        correction = 0
        readable = 0

    header_form = get_header(firstpage_form)
    defend, defend_og, plaint, plaint_og = get_plaint_defend(header_form, readable)
    plaint_full, plaint_first, plaint_no = party_id(plaint_og)
    defend_full, defend_first, defend_no = party_id(defend_og)
    fulltext_og, fulltext = format_text(fulltext_form)
    caseno, courtname, date, year = basic_caseinfo(file, topwords)
    doc_type = get_doctype(file, topwords, fulltext_og)

    if readable == 1:
        judge, judgetitle = get_judge(doc_type, fulltext_og, fulltext, lastpage_form)
    else:
        judge, judgetitle = get_judge_scans(judge_string, judge_small, judge_large)
    
    if doc_type == 'dom' or doc_type == 'deldom':
        ruling_form, ruling_og, ruling = get_ruling(fulltext_form)
        case_type = get_casetype(defend, plaint, fulltext_og, ruling, firstpage_form)

        if not case_type == '1216B':
            domskal_og, domskal = get_domskal(fulltext_og, ruling_form)
            
            # try:
            id_name = get_childname(year, ruling_og, defend_full, plaint_full)
            for child_id in id_name:
                child_first = id_name[child_id]
                
                # Save rulings data to file
                dict_rulings = filldict_rulings(
                    DATA_RULINGS,  child_id, file, page_count, correction, topwords, fulltext_og,
                    ruling, plaint_no, defend_no, defend, plaint, defend_first, domskal_og,
                    ruling_og, plaint_first, child_first, firstpage_form, domskal, fulltext,
                    caseno, courtname, date, year, judge, judgetitle
                    )
                save(dict_rulings, SAVE, COUNT, OUTPUT_RULINGS)

            # except Exception as e:
            #    print_output("Error",e)
            
    else:
        case_type = 'N/A'
    
    # Save case register to csv
    dict_register = filldict_register(
        DATA_REGISTER, case_type, defend_no, plaint_no, date,
        courtname, doc_type, caseno, judge, judgetitle, file
        )
    
    save(dict_register, SAVE, COUNT, OUTPUT_REGISTER)



#Execute
files = paths()
pics = cases_from_imgs()

#For scanned pdfs
for file in files:
    jpgs = 0
    main(file, jpgs)
    flag = []
    
#For scans as photos (jpgs)
for case in pics:
    jpgs = 1
    main(case, jpgs)
    flag = []
    
