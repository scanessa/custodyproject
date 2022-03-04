# -*- coding: utf-8 -*-
"""
Created on Tue Nov  2 15:04:16 2021

@author: ifau-SteCa

"""
import re
import time
import io
import os

from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter

from searchterms import OCR_CORR, appendix_start, defend_search, caseno_search, id_pattern
from searchterms import date_search, judgetitle_search, judgesearch, judgesearch_noisy
from searchterms import ruling_search

from OCR import ocr_main

#General settings
ROOTDIR = "P:/2020/14/Kodning/Scans/"
OUTPUT_REGISTER = "P:/2020/14/Tingsrätter/Case_Sorting_SC/case_register_data.csv"
OUTPUT_RULINGS = "P:/2020/14/Tingsrätter/Case_Sorting_SC/rulings_data.csv"

#Specify folders to search PDFs in
EXCLUDE = set([])
INCLUDE = set(['all_cases','all_scans'])
SAVE = 1
COUNT = 1
start_time = time.time()



#Helper functions
def searchkey(string, part, g):
    finder = re.compile(string)
    match = finder.search(part)
    if match is not None:
        searchResult = match.group(g)
    else:
        searchResult = None
    return searchResult



def dictloop(dictionary, part, g, excludeTerms):
    for i in dictionary:
        result = searchkey(dictionary[i], part, g)
        if result is None or any([x in result.lower() for x in excludeTerms]):
            continue
        else: 
            break
    return result



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
                    print(f"Dealing with file {subdir}/{file}")
                    pdf_dir = (os.path.join(subdir, file))
                    pdf_files.append(pdf_dir)
    return pdf_files



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
    else:
        correction = 0
        fulltext_form, firstpage_form = text_parts(0)
        if appendix:
            appendix_pageno, fulltext_form = appendix_pages(0)    
    return correction, appendix_pageno, fulltext_form, firstpage_form, lastpage_form



def clean_ocr(topwords, firstpage_form, fulltext_form):
    for old, new in OCR_CORR.items():
        topwords = topwords.replace(old, new)
        firstpage_form = firstpage_form.replace(old, new)
        fulltext_form = fulltext_form.replace(old, new)
    return topwords, firstpage_form, fulltext_form



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
        for term in ['PARTER','Parter', 'Kärande']:
            header2 = header1.split(term)
            if term == 'Kärande':
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



def get_plaint_defend(part):
    """
    Extract plaintiff and defendant boxes from first page (including lawyer info if applicable)
    for readable and scanned docs
    """
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
                defend_og = plaint_og = 'not found, not found'
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
        
    return full, first, number



def judge(doc_type, fulltext_og, fulltext, lastpage_form):
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
            judge_name = ((dictloop(judgesearch, lastpage_form, 1, ['telefon','telefax', 'svarande'])).split('\n'))[0]
            judge_name = judge_name.lower().strip()
        except AttributeError:
            try:
                finalpart = re.split('ÖVERKLAG|Överklag|överklag', lastpage_form)[-1]
                judge_name = ((dictloop(judgesearch_noisy, finalpart, 1, ['telefon','telefax', 'svarande', 't'])).split('\n'))[0]
                judge_name = re.split('\s{4,}|,', judge_name)[0]
                judge_name = judge_name.lower().strip().strip('/').strip('|')
            except:
                judge_name = 'Not found'
    else:
        judge_name = "Not found" 

    return judge_name, judge_title

    

def basic_caseinfo(file, topwords, fulltext_og):
    """
    Extracts information relevant to all types of documents: 
        1) case id 
        2) doc type (dom,deldom,slutligt beslut, dagbok, protokoll) 
        3) court name
        4) case date, case year
    """
    try:
        caseno = ''.join((searchkey(caseno_search, topwords, 2)).split())
    except AttributeError:
        try:
            caseno = searchkey('T.?\s*(\d*-\d*)', file, 1)
        except:
            caseno = "Not found"

    filename = file.lower() 
    print(topwords)
    
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

    courtname = re.split('\W',file.split('/')[4])[0]

    try:
        date = dictloop(date_search, topwords, 1, [])    
        year = date[:4]
    except:
        date = "Not found"

    return caseno, doc_type, courtname, date, year
  


def get_ruling(fulltext_form):
    """
    Extract only ruling text headed usually 'Domslut'
    """
    try:
        ruling_form = ''.join(re.split('DOMSLUT|Domslut\n', ''.join(fulltext_form))[1:])
    except AttributeError:
        ruling_form = ''.join(re.split('_{10,40}\s*', ''.join(fulltext_form))[1:])
    try:
        ruling_form = ''.join(re.split('[A-ZÅÄÖÜ]{4,}\s*\n*TINGSRÄTT',ruling_form))
    except AttributeError:
        ruling_form = ''.join(re.split('\n\n[A-ZÅÄÖÜ]{1}[a-zåäüö]{3,]\s*\n*Tingsrätt',ruling_form))
        
    ruling_form = ''.join(re.split('DELDOM|DOM',ruling_form))
    ruling_form = re.split(dictloop(ruling_search,ruling_form,0,[]), ruling_form)[0]
    
    try:
        if searchkey('\d\d\s*–\s*\d\d', ruling_form, 0):
            ruling1 = re.sub('\s*–\s*','–',ruling_form)
            ruling2 = re.sub('\s*–\n','–',ruling_form)
        else:
            ruling1 = re.sub('\s*-\s*','-',ruling_form)
            ruling2 = re.sub('\s*-\n','-',ruling_form)
        ruling_og = ' '.join(''.join(ruling2).split())
        
    except AttributeError:
        ruling_og = ' '.join(''.join(re.split('(YRKANDEN|Yrkanden)', ruling_form)[0].lower() ).split())
        if searchkey('\d\d\s*–\s*\d\d', ruling1, 0):
            ruling_og = re.sub('\s*–\s*','–',ruling_og)
            ruling_og = re.sub('\s*–\n','–',ruling_og)
        else:
            ruling_og = re.sub('\s*-\s*','-',ruling_og)
            ruling_og = re.sub('\s*-\n','-',ruling_og)
            
    ruling = ruling_og.lower()
    
    return ruling_form, ruling_og, ruling



def main(file):
    outpath = file.split('\\')[0]
    os.chdir(outpath)
    
    if 'all_cases' in file:
        print('\nReadable: ', file)
        correction, appendix_pageno, fulltext_form, firstpage_form, lastpage_form = read_file(file)
        topwords = get_topwords(firstpage_form)
    elif 'all_scans' in file:
        print('\nScan: ', file)
        firstpage_form, lastpage_form, fulltext_form, judge_string, topwords_form = ocr_main(file)
        topwords_form, firstpage_form, fulltext_form = clean_ocr(topwords_form, firstpage_form, fulltext_form)
        topwords_og, topwords = format_text(topwords_form)
    
    header_form = get_header(firstpage_form)
    defend, defend_og, plaint, plaint_og = get_plaint_defend(header_form)
    
    plaint_full, plaint_first, plaint_no = party_id(plaint_og)
    defend_full, defend_first, defend_no = party_id(defend_og)
    fulltext_og, fulltext = format_text(fulltext_form)
    
    caseno, doc_type, courtname, date, year = basic_caseinfo(file, topwords, fulltext_og)
    
    if doc_type == 'dom' or doc_type == 'deldom':
        ruling_form, ruling_og, ruling = get_ruling(fulltext_form)
    else:
        case_type = 'N/A'
    
    return ruling

#Execute
files = paths()
for file in files:
    print(main(file))
