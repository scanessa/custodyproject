
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
import gender_guesser.detector as gender
import spacy
import numpy as np

from fuzzywuzzy import fuzz
from Levenshtein import distance
from transformers import pipeline

from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter

from searchterms import appendix_start, caseno_search, id_pattern, party_split, appeal, OCR_CORR
from searchterms import date_search, judgetitle_search, judgesearch, party_headings
from searchterms import ruling_search, legalguardian_terms, lawyer_key, citizen, contest_key
from searchterms import cities, countries, nocontant, separation_key, remind_key, residence_key
from searchterms import reject_outcome, visitation_key, reject, exclude_phys, physicalcust_list
from searchterms import agreement_key, agreement_add, no_vard, agreement_excl, past, fastinfo_key
from searchterms import cooperation_key, reject_invest, invest_key, outcomes_key, reject_mainhearing
from searchterms import mainhearing_key, exclude_judge, unwanted_judgeterms, judgesearch_scans,defend_response
from searchterms import plaint_terms, name_pattern, defend_resp_dict, svarande_karande, clean_general
from searchterms import clean_header, clean_partyname, party_city, shared_phys,stay_in_home_key
from searchterms import physicalcust, divorce_terms

#General settings

NLP = pipeline('ner', model='KB/bert-base-swedish-cased-ner', tokenizer='KB/bert-base-swedish-cased-ner')
nlp_spacy = spacy.load('sv_core_news_sm')
gend = gender.Detector(case_sensitive=False)

DATA_RULINGS = {
    
    'child_id':[], 'child_name':[], 'case_no':[], 'court':[], 'date':[], 'casetype_custody':[], 'deldom':[],
    'divorce_only': [], 'divorce': [], 'casetype_divorce':[],'plaintiff_id':[],'plaintiff_name':[],
    'defendant_id':[], 'defendant_name':[],'plaintiff_lawyer':[], 'p_legalguard':[], 
    'defendant_lawyer':[], 'd_legalguard':[], 'p_lawyer_legalaidact':[], 'd_lawyer_legalaidact':[], 
    'p_lawyer_name':[], 'd_lawyer_name':[], 'p_lawyer_title':[], 'd_lawyer_title':[], 
    'defendant_address_secret': [], 'plaintiff_address_secret':[],
    'defendant_abroad':[], 'defendant_unreachable':[], 'plaint_made':[], 
    'plaint_legal':[],'plaint_physical':[],'plaint_visitation':[],'plaint_alimony':[],
    'initial_legal':[],'initial_physical':[],'temp_legal':[],'temp_physical':[],'temp_visitation':[],
    'outcome':[],'visitation':[], 'contactperson':[], 'visitation_type':[], 'physical_custody':[], 'alimony':[],
    'agreement_legalcustody':[], 'agreement_any':[], 'estate_distribution_executor':[], 'fastinfo':[],
    'cooperation_talks':[], 'investigation':[], 'mainhearing':[], 'stay_in_home':[],
    'separation_year': [], 'judge':[], 'judge_gender':[], 'judge_text':[], 'page_count': [],
    'correction_firstpage': [], 'flag': [],'file_path': []
    
    }

DATA_REGISTER = {
    
    'caseid':[], 'type':[], 'casetype':[], 'court':[], 'date':[], 'plaintiff':[],
    'defendant':[], 'judge':[], 'judgetitle':[], 'filepath':[], 'flag': []

    }

start_time = time.time()
flag = []
COUNT = 1

SAVE = 1
PRINT = 0
FULLSAMPLE = 0
APPEND = 0

#Specify folders to search PDFs in
if FULLSAMPLE == 1: #to create actual dataset
    ROOTDIR = "P:/2020/14/Tingsratter/"
    OUTPUT_REGISTER = "P:/2020/14/Kodning/Data/case_register_data.csv"
    OUTPUT_RULINGS = "P:/2020/14/Kodning/Data/rulings_data.csv"
    JUDGE_LIST = "P:/2020/14/Data/Judges/list_of_judges_cleaned.xls"
    EXCLUDE = set(['Sodertorns'])
    INCLUDE = set(['all_scans'])
    LAST = ''

else: #for testing and debugging
    ROOTDIR = "P:/2020/14/Kodning/Test-round-5-Anna/"
    OUTPUT_REGISTER = "P:/2020/14/Kodning/Test-round-5-Anna/case_register_data.csv"
    OUTPUT_RULINGS = "P:/2020/14/Kodning/Test-round-5-Anna/rulings_data.csv"
    JUDGE_LIST = "P:/2020/14/Data/Judges/list_of_judges_cleaned.xls"
    EXCLUDE = set(['exclude','ocr_errors', 'first500'])
    INCLUDE = set(['all_cases','all_scans'])
    LAST = ''
    
    
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
    """
    Takes a searchstring and part, uses regex to search for string in part
    Returns string of search result group
    """
    finder = re.compile(string)
    match = finder.search(part)
    if match is not None:
        searchResult = match.group(g)
    else:
        searchResult = None
    return searchResult



def dictloop(dictionary, part, g, exclude_terms):
    """
    Loops through elements in dictionary and provides each element as string
    input to searchkey function
    If re.search returns result and none of the terms in exclude terms are in the result:
    Returns string of search result group
    """
    for i in dictionary:
        result = searchkey(dictionary[i], part, g)
        if result is None or any([x in result.lower() for x in exclude_terms]):
            continue
        else:
            break
    return result



def findterms(stringlist, part):
    sentenceRes = []
    split = re.split('(?=[.]{1}\s\n*[A-ZÅÐÄÖÉÜ]|\s\d\s)', part)
    stringlist = [x.lower() for x in stringlist]
    for sentence in split:
        sentence = sentence.lower() + '.'
        if all([x in sentence for x in stringlist]):
            sentenceRes.append(sentence)
    sentenceString = '.'.join(sentenceRes)
    return sentenceString



def findfirst(stringlist, part):
    sentenceRes = []
    split = re.split('(?=[.]{1}\s+\n*[A-ZÅÐÄÖÉÜ1-9]|\s\d\s)', part)
    for sentence in split:
        if all([x in sentence.lower() for x in stringlist]):
            sentenceRes.append(sentence)
    if sentenceRes:
        sentenceString = sentenceRes[0]
    else:
        sentenceString = ''
    return sentenceString



#Main functions
def paths(ending):
    filecounter = 0
    pdf_files = []
    for subdir, dirs, files in os.walk(ROOTDIR, topdown=True):
        for term in EXCLUDE:
            if term in dirs:
                dirs.remove(term)
        for file in files: 
            for term in INCLUDE:
                if term in subdir and file.endswith(ending):
                    filecounter += 1
                    print(f"Dealing with file {subdir}/{file}")
                    pdf_dir = (os.path.join(subdir, file))
                    pdf_files.append(pdf_dir)
                    
    print("Total files: ", filecounter)     
    
    return pdf_files



def topwords_from_jpd(text):
    top = itertools.takewhile(lambda x: len(x) < 50, text)
    out = list(top)

    return out

def cases_from_imgs():
    pass



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



def get_ocrtext(full_text):
    """
    Use OCR fulltext and header to return first page, topwords, judge, fulltext formatted and cleaned
    Topwords are first 10 words found on page
    """
    
    full_text = full_text.split('__newpage__')
    full_text = [x for x in full_text if not x == '\n']
    
    firstpage_form = ''.join(full_text[0])
    page_count = len(full_text)
    lastpage_form = ''.join(full_text[-1])
    fulltext_form = ''.join(list(itertools.chain.from_iterable(full_text)))
    topwords_form = [x.split()[:20] for x in full_text]
    topwords_form = ' '.join(itertools.chain(*topwords_form))
    
    topwords_form, firstpage_form, fulltext_form = clean_ocr(topwords_form, firstpage_form, fulltext_form)
    topwords_og, topwords = format_text(topwords_form)
    
    return fulltext_form, firstpage_form, topwords, page_count, lastpage_form



def clean_ocr(topwords, firstpage_form, fulltext_form):
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

    return topwords, firstpage_form, fulltext_form



def clean_text(inp, cleaning_dict):
    """
    Cleans text used as basis for remaining analysis to prevent false positives
    Removes all whitespace between numbers to capture IDs with regexs
    """
    inp = re.sub(r'(\d)\s+(\d)', r'\1\2', inp)

    for noise, clean in cleaning_dict.items():
        inp = inp.replace(noise, clean)
    
    return inp


def format_text(unformatted):
    og = ' '.join((''.join(unformatted)).split())
    lower = og.lower()

    return og, lower



def get_header(firstpage_form):
    
    """
    Splits first page into a header, ie the part after topwords and before ruling starts
    """
    try:
        header1 = (re.split('(DOMSLUT|Domslut\n|SAKEN\n)', firstpage_form))[0]
        for term in ['PARTER','Parter', 'Kärande', 'KÄRANDE', 'DOM']:
            header2 = header1.split(term)
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


def word_classify(text, entity_req, strictness):
    """
    Inputs:
        - text: string that should be classified (must pass with ORIGINAL CASING ie upper case for names)
        - entity_req: required entity, pass as string; options: PER (person), 
        LOC (location), score 0-1, word (string)
    
    Returns:
        - List with lists of entities with consecutive indices that fulfull the entity requirement
        (person strings, location strings) if found, if required entity not found, returns None
    """
    
    joined_text = []
    split_text = NLP(text)
    in_word=False
    
    # Filter out items of unwanted categories
    if not entity_req == '': 
        clean_list = [x for x in split_text if x['entity'] == entity_req and x['score'] > strictness]
    else:
        clean_list = split_text

    # Group consecutive items (words)
    grouped = [[v for k, v in g] for k, g in itertools.groupby(enumerate(clean_list), lambda v: v[0] - v[1]['index'])]

    # Join tokenized list
    for lst in grouped:
        
        joined = []
        
        for i,token in enumerate(lst):

            if token['entity'] == 'O':
                in_word = False
                continue
        
            if token['word'].startswith('##'):
                if not in_word:
                    joined += [ split_text[i-1] ]
                    joined[-1]['entity'] = token['entity']
                joined[-1]['word'] += token['word'][2:]
            else:
                joined += [ token ]
    
            in_word = True
            
        joined_text.append(joined)
    
    return joined_text



def get_partyname(parties, part_for_name):
    """
    Gets party (plaintiff, defendant) characteristics based on Swedish Bert NER for cases
    where plaintiff and defendant are NOT labeled Kärande and Svarande
    
    For cases where parties are clearly labeled Kärande or Svarande, code goes into else
    """

    print_output("Part for name", part_for_name)
    print_output("Party names", word_classify(part_for_name, 'PER', 0))

    name_for_part = []
    party_lst = [x.split() for x in parties]
    party_lst = list(np.concatenate(party_lst).flat)
    party_lst = [x.strip(',').strip('(').strip(')') for x in party_lst]

    part_for_name = part_for_name.split("advokat")[0]
    p_name = word_classify(part_for_name, 'PER', 0.95)
    
    if p_name:
        p_name = p_name[0] #flattens list assuming only 1 name is in sentence
        name = [x['word'] for x in p_name]
        name = [x for x in name if x.lower() not in party_headings if not any([c in x.lower() for c in cities])]
        
        #Join hyphenated names
        for i in reversed(range(len(name))):
            if name[i] == '-':
                name[i-1: i+2] = [f'{name[i-1]}-{name[i+1]}']
        
        #Check if party name has typo in header
        for s in party_lst:
            for n in name:
                comp = distance(n.lower(),s.lower())
                part_dist = fuzz.partial_ratio(s.lower(), n.lower())
                                    
                if comp < 2 or part_dist == 100:
                    name_for_part.append(s)  
    else:
        part = parties[0]
        part = part.replace('Kärande', "").replace('Svarande', "")
        name_for_part = name = (dictloop(name_pattern, part, 1, [])).split()
    
    return name, name_for_part
        


def get_party(parties, part_for_name, use_ner):
    """
    Gets name based on similarity, to account for misspelled characters a match is 
    considered to be a string that needs max. 1 character swap to be equal to the name
    (in each of the elements of parties)
    Note:
        - else after if p_name gets names that NER didn't recognize as such by
        capturing the words before 6-10 consecutive numbers
    """
    
    plaint_lst = []
    lawyer_part = ""
    
    if use_ner:
        print_output("use_ner=True", '')
        name, part_for_name = get_partyname(parties, part_for_name)
        
    else:
        print_output("use_ner=False", '')
        
        part = parties[0]
        part = clean_text(part, clean_partyname)
        print_output("Part for name if user_ner = False", part)
        name = part_for_name = (dictloop(name_pattern, part, 1, [])).split()
    
    print_output("Party name", name)

    for index, part in enumerate(parties):
        print_output("Part in loop for parties", part)
        # Party (name + address)
        if all(x in part for x in part_for_name):
            plaint_lst.append(part)

            # ID
            try:
                number = ''.join(searchkey(id_pattern, part.lower(), 2).split())
                print_output("ID number",number)
                
            except AttributeError:
                number = "-"
                print_output("ID not found", "")
            
            # Lawyer
            if index + 1 < len(parties):
                
                next_el = parties[index+1]
                print_output("Element for lawyer", next_el)
                
                if any([x in next_el.lower() for x in lawyer_key]):
                    lawyer = 1
                    lawyer_part = next_el
                    plaint_lst.append(next_el)
                    print_output("Lawyer", lawyer)
                    print_output("Plaint_lst", plaint_lst)
                    break
                
                else:
                    lawyer = 0
                    print_output("Lawyer", lawyer)
    
            else:
                lawyer = 0
    name_full = name
    name = name[:-1] if len(name) > 1 else name
    
    print_output('Final plaint_lst', plaint_lst)
    print_output('parties', parties)
    
    new_parties = [x for x in parties if not any(i in x for i in plaint_lst)]
    
    print_output('new_parties', new_parties)
    
    return part, name, name_full, number, lawyer, lawyer_part, new_parties



def get_response(fulltext, plaint_made):
    """
    Gets the case type variable only for those cases where a custody battle was
    found. Variable depends on whether defendant agreed to plaint, contested,
    or tvistat (=joint application). 
    
    Pass: fulltext capitalized, custodybattle capitalized
    Returns variable outcome as string
    """
    matches = []

    for term, resp in defend_response:
        index = fulltext.find(term)
        if index > 0:
            matches.append((resp,term,index))

    for resp, terms_list in defend_resp_dict.items():
        for terms in terms_list:
            sentence = findfirst(terms, fulltext)
            index = fulltext.find(sentence)
            if index > 0:
                matches.append((resp,terms,index))
    
    matches = sorted(matches, key=lambda x: int(x[2]), reverse=False)
    
    if (
            findterms(['yrkade', 'för','egen','del'], fulltext)
            or findterms(['bestred','talan',' i ','övrigt'], fulltext)
            ):
        match = 'contest'
        
    elif matches:
        match = matches[0][0]
        
    else:
        match = 'plaint made, no response found'

    return match

    

def get_custodybattle(fulltext, searchterms):
    """
    Defines whether case is:
        1) custodybattle where defendant agreed to plaint
        2) custodybattle where defendant contested plaint
        3) custodybattle with tvistat
        4) shared application
        5) none of the above found
    
    Will return no custodybattle found if the case does not include legal custody
    
    Returns casetype (see above) and sentence indicating custodybattle
    """
    
    searchtext = fulltext.replace("YRKANDEN", "")
    
    for term in searchterms:
        plaint_made = findfirst(term, searchtext)
        if plaint_made:
            print_output('Term for Plaint_made', term)
            print_output('Plaint_Made', plaint_made)
            break
    print_output("Text indicating plaint_made", plaint_made.split("delimiter"))
    if 'parterna har' in plaint_made.lower():
        plaint_made = 'joint'
    
    if plaint_made and plaint_made != 'joint':
        casetype = get_response(fulltext, plaint_made)
    
    elif (
            findterms(['gemesam','ansök'], fulltext)
            or plaint_made == 'joint'
            ):
        print_output("Text indicating joint app", findterms(['gemesam','ansök'], fulltext))
        casetype = 'joint application'
   
    else:
        print_output("No plaint_made or joint app", "")
        casetype = 'no plaints formulated'
    
    return casetype, plaint_made



def get_parties(header):
    # Split header into 2 parties
    parties = re.split(party_split, header)
    parties = [x for x in parties if x if not x == " " if not 'saken' in x if not x == '\n']
    
    print_output("Parties", parties)
    
    if len(parties) == 1:
        new_parts = []
        i = 0
        og_parties = parties = ''.join(parties)
        parts = [x.lower() for x in re.split('\s|\n', parties)]
        partycities = list(set(parts) & set(cities))
        for city in partycities:
            if i>0:
                for part in parties:
                    if city not in part:
                        new_parts.append([part])       
                parties = ''.join([x for x in parties if city in x])
                        
            parties = parties.split(city)
            new_parts.append(parties)
            i += 1
        
        new_parts = list(itertools.chain.from_iterable(new_parts))
        new_parts = [x for x in new_parts if not any(c in x for c in cities)]
        parties = list(set([x for x in new_parts if re.search(r'\d', x)]))
        
        if not parties:
            parties = re.split(party_city, ''.join(og_parties))
        
        print_output("New parties", parties)
        
    partyhead = ''.join([x for x in header.lower().split('\n') if 'rande' in x])
    
    print_output("Party head: ", partyhead)
    
    return parties, partyhead



def get_plaint_defend(fulltext, header, year):
    """
    Extract plaintiff and defendant boxes from first page (including lawyer info if applicable)
    for readable and scanned docs
    Returns:
        - casetype
        - part (name, address), first name, lawyer dummy for plaintiff and defendant
        - godman dummy for defendant 
    Note:
        Lund 3060-06 (Scan 3. May 2022 at 14.11.pdf) our code switches plaintiff and defendant compared to case because we define plaintiff by plainting for custody, and Lars only makes a plaint for umgänge
    """
    
    print_output("Part for parties (header)", header.split("delimiter"))
    
    casetype, plaint_made = get_custodybattle(fulltext, plaint_terms)
    parties, partyhead = get_parties(header)
    

    if (
            not any(x in header for x in svarande_karande)
            and plaint_made
            or ' och ' in partyhead.lower()
            and plaint_made
            ):
        
        print_output("Getting plaint name 1", "")
        use_ner = True
        plaint_part, plaint_name, plaint_full, plaint_number, plaint_lawyer, p_lawyer_part, new_parties = get_party(parties, plaint_made, use_ner)

    else:

        print_output("Getting plaint name 2", "")
        use_ner = False
        plaint_part, plaint_name, plaint_full, plaint_number, plaint_lawyer, p_lawyer_part, new_parties = get_party(parties, parties[0], use_ner)
    
    print_output("Getting defend name", new_parties)
    defend_part, defend_name, defend_full, defend_number, defend_lawyer, d_lawyer_part, _ = get_party(new_parties, ' '.join(new_parties), use_ner)

    if 'god man' in ' '.join(new_parties).lower():
        defend_godman = 1
        
    else:
        defend_godman = 0
    
    plaint_made = plaint_made.replace("\n", " ")
    
    #Flag cases where a child"s ID is in the header (children as plaintiffs in alimony cases)
    ids = re.findall('\d{6,10}.\d{4}', header)
    for num in ids:
        if len(re.split('\D', num)[0]) == 8:
            childyear = num[:4]
        else:
            childyear = '19'+num[:2] if int(num[:2])>40 else '20'+num[:2]
        age = int(year) - int(childyear)
        if 0 < age < 18:
            flag.append('Child as plaintiff with ID ' + num)

    return plaint_part, plaint_name, plaint_full, plaint_number, plaint_lawyer, p_lawyer_part, defend_part, defend_name, defend_full, defend_number, defend_lawyer, d_lawyer_part, defend_godman, casetype, plaint_made




def get_defendabroad(defend_part, defend_first, defend_godman, fulltext_og, domskal_og):
    """
    Get information on whether defendant is located abroad
    - First checks if any of the cities in Sweden can be found in defendant part (relies on
      defendant part to be accurately split on lawyer term to not confuse defend address
      with lawyer address)
    - Then goes through long list of conditions that suggest defendant to be abroad
    - didnt include defend_first because defend might be referred to by Han
    """
    
    # First get defendant city
    if 'medbor' in defend_part:
        defend_part = ' '.join(re.split(citizen,defend_part))
    defend_city = ''.join((defend_part.strip(' _\n')).split(' ')[-1])
    
    if any([x in defend_city for x in cities]):
        print_output("Abroad 0","")
        defend_abroad = 0
        
    elif (
            any([x in defend_part for x in countries]) or 'okänd' in defend_part
            or defend_godman == 1  and 'saknar kän' in defend_part
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
        print_output("Abroad 2",defend_godman == 1  and 'saknar kän' in defend_part)
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


    
def secret_address(party):
    """
    Dummy whether defendant or plaintiff's address is secret
    Input plaint or defend for party
    """
    secret_party = 1 if 'sekretess' in party else 0
    return secret_party



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
                finalpart = re.split(appeal, lastpage_form)[-1]
                judge_name, _ = get_judge_lastparag(finalpart)
            except:
                judge_name = 'Not found'

    else:
        judge_name = "Not found" 
    
    return judge_name, judge_title



def get_judge_lastparag(lastparagraph):
    """
    Pass lastparagraph (only words following Överklagande) as string
    Removes all words characteristic to last paragraph, only noise and judge
    name should be left. Finds capitalized words similar to regular judge search
    but without new paragraph requirement.
    Returns judge_name as string, if no name found, returns None
    """
    
    noisy = re.split('[0-9]|,|[.]|[\n]|[\s]', lastparagraph)
    
    clean = [x for x in noisy if not any(unwant == x.lower() for unwant in unwanted_judgeterms)]
    clean = [x for x in clean if len(x) >= 3]
    clean = ' '.join(clean) + ' '
    print_output("Clean text input for judge",clean)
    
    name = dictloop(judgesearch_scans, clean, 0,exclude_judge)
    
    print_output("Name input for judge",name)
    
    if name:
        name = word_classify(name, "PER", 0)
        print_output("Name classifyer for judge", name)
        name = list(itertools.chain.from_iterable(name))
        name = ' '.join([x['word'] for x in name])
        name = name.lower() if name else name
    else:
        name = 'Not found'

    return name, clean


def get_judge_scans(judge_string):
    """
    Gets judges name from scanned documetn by going through different text
    parts, judge1 = judge_string, judge2 draws tight bounding boxes wiht 9x9
    kernal in OCR module around text and parses the text in those tight boxes,
    judge3 parses as much text as it can get from the whole page without any
    boxes.
    
    Code then takes list of digital judges generated with STATA, compares combined 
    string of all judge texts with each name and at similarity CUTOFF = 70 AND 
    assigns judge_name = match
    
    Cut judge string at 500 characters, otherwise the BERT model gives a timeout
    error
    
    get_judge_lastparag return judge_name (or None) and clean version of judge_string,
    where unwanted judgeterms have been removed
    """
    
    if len(judge_string) > 500:
        judge_string = judge_string[-500:]
    
    print_output("String for get_judge_scans", judge_string.split("delimit"))
    judge_title = 'N/A'
    judge_name = ''
    cutoff = 70

    judge_name, judge_string = get_judge_lastparag(judge_string)

    if not judge_name:
        
        p_name = word_classify(judge_string, "PER", 0)
        p_name = list(itertools.chain.from_iterable(p_name))
        judge_name = ' '.join([x['word'] for x in p_name])
        
    if not judge_name:
        
        digital_judges = pd.read_excel(JUDGE_LIST)
        try:

            for _, row in digital_judges.iterrows():
                match = row['judge']
                comp_match = fuzz.partial_ratio(match, judge_string)
                
                if comp_match >= cutoff:
                    cutoff = comp_match
                    judge_name = match
            
        except Exception as e:
            print(e)

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
        print_output("Ruling 1","")
        ruling_form = ''.join(re.split('MSLUT|Domslut\n', ''.join(fulltext_form))[1:])
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
    second_ruling_splitter = dictloop(ruling_search,ruling_form,0,[])
    
    ruling_form = re.split(second_ruling_splitter, ruling_form)[0]
    
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
    print_output("Ruling: ",ruling)
    
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
    childnos = list(dict.fromkeys(childnos))
    for num in childnos:
        if len(re.split('\D', num)[0]) == 8:
            childyear = num[:4]
        else:
            childyear = '19'+num[:2] if int(num[:2])>40 else '20'+num[:2]
        age = int(year) - int(childyear)
        
        if 0 < age < 18:
            childid_name[num] = ''

    return childid_name



def get_childname(ruling_og, plaint_name, defend_name, year):
    """
    Extract child ID's first from ruling, if not found there from full text,
    otherwise get child's name and use that as ID
    """
    childid_name = get_childnos(ruling_og, year)
    updated_ruling = ruling_og
    
    if childid_name:
        for i in childid_name:
            print_output("childid", i)
            names = []
            relev = updated_ruling.split(i)[0]
            print_output("relevant part for childid name", relev)
            print_output("Child names",word_classify(relev, "PER",0.99))
            
            #NLP cant get name if only word in relev is the name, so get these names in first if
            name = re.split(",|\s", relev)
            name = [x.strip() for x in name if x.strip()]
            if len(name) == 1:
                names = name
            else:
                p_name = word_classify(relev, "PER",0.9)
                
                if p_name:
                    p_name = p_name[-1]
                    names = [x['word'] for x in p_name]
                else:
                    relev = relev.split()
                    relev = relev[::-1]
                    for word in relev:
                        if not word[0].isupper():
                            break
                        else:
                            names.append(word.strip(','))

            child_first = [x for x in names if x[0:3].isupper()]

            if not child_first:
                child_first = names[0]
            else:
                child_first = child_first[0].capitalize()

            childid_name[i] = child_first
            
            # Remove used part of string from ruling to look for new names
            updated_ruling = ' '.join([x for x in updated_ruling.split(i) if not x == relev])

    else:
        for term in ["vård", "umgänge", "boende"]:
            relev = findfirst([term],ruling_og)
            if relev:
                break
            else:
                relev = ruling_og
        p_name = word_classify(relev, "PER", 0.99)
        pd_names = set(x.lower() for x in plaint_name + defend_name)
                
        for x in p_name:
            name = [n['word'] for n in x]
            names = [x.lower() for x in name]

            if set(names).isdisjoint(pd_names):
                joined = ' '.join(name)
                joined = joined.replace(' - ', '-')
                childid_name[joined] = joined

    childid_name = {'not found':'not found'} if not childid_name else childid_name
    
    print_output("childid_name",childid_name)

    return childid_name
    


def part_ruling(topwords):
    part_rul = 1 if 'deldom' in topwords else 0
    print_output("Topwords",topwords.split("."))

    return part_rul



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
                found = True
                break
            else:
                unreach = 0
                found = False

        unreach = 1 if defend_godman == 1 else unreach
        reachable = [[name, 'kontakt ', 'med']]

        for part in reachable:
            if not found and findterms(part, fulltext_og) and not any([x in findterms(part, fulltext_og) for x in nocontant]):
                unreach = 0
        else:
            continue
        break
    
    #Exception: if defendant is active in case, they cannot be unreachable
    if (
            findterms(['yrkade' 'för' 'egen' 'del'], fulltext_og)
            or findterms(['yrkade', defend_first[0]], fulltext_og)
            ):
        
        unreach = 0

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



def get_outcome(fulltext_og, ruling_og, firstpage_form, child_id, child_first, plaint_first, defend_first):
    """
    Get the ruling/outcomeo of the case:
        1 = shared custody
        2 = custody with plaintiff 
        3 = custody with defendant
        4 = case dismissed
        5 = outcome defined in appendix
    Notes:
    - "lämnas utan bifall" in findVard because if I search in ruling only it picks up when umgange claims or so are dismissed
    - replaces gemensamm with gemensa so that I can search for gemensam. and gemensamt without picking up on gemensamme barn
    """
    
    ruling = ruling_og.lower()
    sentences = re.split('[.]\D', ruling_og)
    
    findVardn = [x for x in sentences if 'vård' in x.lower() and child_id in x.lower()]
    findVardn = [x for x in sentences if 'vård' in x.lower()] if not findVardn else findVardn
    findVardn = '. '.join(findVardn)
    findVardn = findVardn.lower()
    plaint_first = [x.lower()for x in plaint_first]
    defend_first = [x.lower()for x in defend_first]

    print_output("For output: child_first", child_first)
    print_output("For output: plaint_first", plaint_first)
    print_output("For output: defend_first", defend_first)
    print_output("For output: ruling_og", ruling_og.split("delimit"))
    print_output("For output: findVardn", findVardn.split("delimit"))

    #Dismissed or no custody ruling
    if (
            'käromalet ogillas' in ruling_og
            or any(x in findVardn for x in ['avslås', 'avskriv'])
            or all(x in findVardn for x in [' lämna',' utan ',' bifall'])
            or all(x in ruling_og for x in ['lämnas utan bifall', 'talan'])
            ): 
        
        out = 4
        print_output("Outcome 1", out)

    elif (
            'vård' not in ruling and 'vård' not in firstpage_form.lower()
            or any([x in findVardn for x in remind_key])
            or child_first.lower() not in findVardn.lower() and child_first != 'not found'
            ): 
        
        out = 0
        print_output("Outcome 2", out)
        print_output("Condition 1", 'vård' not in ruling and 'vård' not in firstpage_form.lower())
        print_output("Condition 2", any([x in findVardn for x in remind_key]) and 'äktenskaps' in ruling)
        print_output("Condition 3a",  child_first not in findVardn)
        print_output("Condition 3b", child_first not in findVardn and child_first != 'not found')
        print_output("For condition 3a", child_first.split("delimit"))
        print_output("For condition 3a", findVardn)

    else:
        out = 999

    anyVardn = any([x in findVardn for x in reject_outcome])

    #Outcome in appendix
    if 'bilaga' in ruling_og:
        out = 5

    def outcome_search(searchterms, findwhere, exclude, out):
        for part in searchterms:
            if all(x in findwhere for x in part) and not exclude:
                result = out
                print_output("Outcome 3", part)
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
    
    print_output("findVardn", findVardn)
    
    if out not in {0,4,5}: 
        out = outcome_search(sharedCustody, findVardn, anyVardn, 1)
        print_output("Outcome 4", out)
    
    #Sole custody
    if out not in {0,1,4,5}:
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
            print_output("Outcome 5", out)
            if out == 2:
                break

    if out not in {0,1,2,4,5}:
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
            print_output("Outcome 6", out)
            if out == 3:
                break

    if out == 999:
        out = 4 if findterms(['avskr','vård'], fulltext_og) or findterms(['skrivs', 'av'], fulltext_og) else out
        print_output("Outcome 7", out)

    return out



def get_visitation(child_first, ruling_og, plaint_first, defend_first):
    """
    Get ruling on visitation rights
    Notes:
    - Took out summer exclusion because that gave too many false negatives where visitation was defined for the weeks
    AND the summer, could potentially include phys=0 if semester in phys and NOT any weekday term in semester sentence
    - In first if statement split ruling by dismissed sentence to search if 
    first visitation plaint was dismissed BUT another installed (eg Trelleborg 1036-04)
    """
    relev = ruling_og
    
    for term in [child_first.lower(), 'barn']:
        for key in visitation_key:
            target = findfirst([key, term], ruling_og)
            print_output('relevant part for visitation', relev)

            if (    
                    findterms(['avslås', key], relev)
                    or findterms([' lämna',' utan ',' bifall', key], relev)
                    or findterms([key, 'avskriv'], relev)
                    ):
                print_output("Visitation 1","")
                visit = 4
                
                if findfirst(['avslås', key], relev):
                    relev = ruling_og.split(findfirst(['avslås', key], relev))[1]
                elif findfirst([' lämna',' utan ',' bifall', key], relev):
                    relev = ruling_og.split(findfirst([' lämna',' utan ',' bifall', key], relev))
                    relev = relev[1]
                elif findfirst([key, 'avskriv'], relev):
                    relev = ruling_og.split(findfirst([key, 'avskriv'], relev))[1]

            elif target and not any([x.lower() in findfirst([key, term], relev) for x in reject]):
                print_output("Visitation 2","")
                
                if any(x.lower() in target.lower() for x in plaint_first):
                    visit = 1
                    break
                elif any(x.lower() in target.lower() for x in defend_first):
                    visit = 2
                    break
                else:
                    visit = 9
                    break
            
            else:
                print_output("Visitation 3", key + term)
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
    firstsentences = '. '.join(ruling_og.split('.')[:10])
    firstsentences = firstsentences.replace('. . ', '.').replace(' . ', '.')
    print_output("Text for physicalcustody", firstsentences)
    
    for term in physicalcust_list:
        target = findfirst(term, firstsentences)
        print_output("Target sentence for physical custody search", target)
        if (
                findfirst([child_first.lower(), 'avslås'], target)
                or findfirst([child_first.lower(), ' lämna',' utan ',' bifall'], target.lower())
                or findfirst([child_first.lower(), 'avskriv'], target.lower())
                ): 
            phys = 4  
            break
        
        elif (
                child_first.lower() in target.lower()
                and any([x in target.lower() for x in shared_phys])
                ):
            phys = 1
            break
        
        elif (
                child_first.lower() in target.lower()
                and any([x.lower() in target.lower() for x in plaint_first])
                and not any([x in target.lower() for x in exclude_phys])
                ):
            phys = 2
            break
        
        elif (
                child_first.lower() in target.lower()
                and any([x.lower() in target.lower() for x in defend_first])
                and not any([x in target.lower() for x in exclude_phys])
                ):
            phys = 3
            break
        
        else:
            phys = 0
            
    return phys



def get_alimony(ruling_og, plaint_first, defend_first):
    """
    Searches for alimony outcome in ruling
    Continuous variable, if code can assign who receives alimony, returns 1
    for plaintiff, 2 for defendant, 4 when alimony is adjusted to 0,
    if it finds alimony but cannot assign it to a party returns 9, 
    if no alimony is found returns 0, if appendix included in ruling returns 5

    """
    print_output("Target sentence for alimony search", findterms(['underhåll'], ruling_og))
    
    if 'noll' in findterms(['underhåll'], ruling_og):
        alimony = 4
    elif findterms(['underhåll'], ruling_og) and not any([x in findterms(['underhåll'], ruling_og) for x in reject]):
        target = findterms(['underhåll'], ruling_og).split(' ska')[0]
        if any(x.lower() in target for x in plaint_first):
            alimony = 1
        elif any(x.lower() in target for x in defend_first):
            alimony = 2
        else:
            alimony = 9
    elif findterms(['bilaga', 'sidorna'],  ruling_og):
        alimony = 5                    
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
        if term in fulltext and not any([x in sentence.lower() for x in reject]):
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
    found = False
    invest = 0

    for term in invest_key:
        if (
                term in fulltext
                and not any([x in findterms([term], fulltext_og) for x in reject_invest])
                ):
            print_output("Invest 1",term)
            invest = 1
            found = True
    
    if (
            not found
            and findterms([' utred', 'ingsrätt'], fulltext_og)
            and not any([x in findterms([' utred'], fulltext_og) for x in reject_invest])
            and not findterms(['saknas', 'möjlighet', ' utred'], fulltext_og)
            ):
        print_output("Invest 2","")
        invest = 1
        
    elif (
            not found
            and any([x in findterms([' utred'], fulltext_og) for x in legalguardian_terms])
            and not any([x in findterms([' utred'], fulltext_og) for x in reject_invest])
            and not findterms(['saknas', 'möjlighet', ' utred'], fulltext_og)
            ):
        print_output("Invest 3","")
        invest = 1
        
    else:
        for sentence in findterms([' utred'], fulltext_og).split('.'):
            if (
                    not found
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



def get_contactp(ruling_og):
    return 1 if 'kontaktperson' in ruling_og else 0



def get_divorce(out, phys, vis, alim, ruling):
    """
    Identify cases that are only about divorce, otherwise a divorce case with no custody
    ruling could not be differentiated from a case where all custody variables are 0
    Notes:
    - potentially also include mellan, used äktenskaps to minimize false 0 because of misspelled äktenskapsskillnad
    """
    if out == 0  and phys == 0 and vis == 0 and alim == 0 and 'äktenskaps' in ruling: 
        divorce = 1
        divorce_dummy = 1
    elif 'äktenskaps' in ruling:
        divorce = 0
        divorce_dummy = 1
    else:
        divorce = 0
        divorce_dummy = 0
    return divorce, divorce_dummy



def get_estate_dist(ruling_og):
    return 1 if "bodelningsförättare" in ruling_og else 0


def get_visitation_type(ruling_og):
    res = findterms(['umgänge '], ruling_og) + findterms(['umgås '], ruling_og)
    print_output("Visitation_type", res)
    return res



def get_lawyerinfo(lawyer):
    legalguard =  1 if "god man" in lawyer.lower() else 0
    legalaid =  1 if "rättshjälpslagen" in lawyer.lower() else 0
    
    for term in ["advokat", "jur.kand"]:
        if term in lawyer.lower():
            lawyer_title = term
            lawyer_name = " ".join(lawyer.lower().split(term)[1:]).strip().replace("\n", " ")
            
            if lawyer_name.startswith("en"):
                lawyer_name = lawyer_name.split("en", 1)[1]
            
            break
        else:
            lawyer_title = 'Not found'
            lawyer_name = lawyer
    
    return legalguard, legalaid, lawyer_title, lawyer_name



def get_stay_in_home(ruling_og, plaint_first, defend_first):
    for term in stay_in_home_key:
        
        if any(x.lower() in findterms([term], ruling_og) for x in plaint_first):
            print_output("Searchterm for stay in home", term)
            print_output("Target for stay in home", findterms([term], ruling_og))
            res = 1
            break
        elif any(x.lower() in findterms([term], ruling_og) for x in defend_first):
            print_output("Searchterm for stay in home", term)
            print_output("Target for stay in home", findterms([term], ruling_og))
            res = 2
            break
        else:
            res = 0
    
    return res



def get_plaintcategory(plaint_made):
    """
    Takes the sentence defined as original plaint (in get_custodybattle method)
    and through if-else categorizes the original plaint into shared (sole) legal,
    physical custody, visitation, and alimony
    """
    
    #Legal custody
    if 'vård' in plaint_made and ' gemensam ' in plaint_made:
        plaint_legal = 1
    elif 'vård' in plaint_made:
        plaint_legal = 2
    else:
        plaint_legal = 0
        
    #Physical custody
    for term in physicalcust:
            
        if (
                term in plaint_made
                and any([x in plaint_made.lower() for x in shared_phys])
                ):
            plaint_physical = 1
            break
        
        elif (
                term in plaint_made
                and not any([x in plaint_made.lower() for x in exclude_phys])
                ):
            plaint_physical = 2
            break
        
        else:
            plaint_physical = 0
    
    #Visitation
    plaint_visit = 1 if any(x in plaint_made for x in visitation_key) else 0

    #Alimony
    plaint_alim = 1 if 'underhåll' in plaint_made else 0  
    
    return plaint_legal, plaint_physical, plaint_visit, plaint_alim



def get_initial_temp(plaint_made, fulltext, plaint_first, defend_first,child_first):
    
    second_ruling_splitter = dictloop(ruling_search,fulltext,0,[])
    relev = re.split(second_ruling_splitter, fulltext)[1]
    relev = relev.split(plaint_made)    
    before_plaint = relev[0].lower()
    plaint_first = [x.lower() for x in plaint_first]
    defend_first = [x.lower() for x in defend_first]
    child_first = child_first.lower()
    
    print_output("before_plaint for initial situation",before_plaint)

    if len(relev)<=1:
        before_plaint = ".".join(before_plaint.split(".")[:10])
        after_plaint = relev[0].lower()
    else:
        after_plaint = relev[1].lower()
    
    #Initial legal
    if (
            findterms(['vård', ' om ' , 'gemensam'], before_plaint)
            or findterms([ 'dom' ,'förordnades' ,'delad', 'vård'], before_plaint)
            ):
        init_l = 1
    
    elif (
            any(x in findterms(['har' 'ensam' 'vårdnad' 'om'], before_plaint) for x in plaint_first)
            or any(x in findterms(['dom' ,'förordn' ,' ensam' ,'vård'], before_plaint) for x in plaint_first)
            ):
        init_l = 2
        
    elif (##same as above
            any(x in findterms(['har' 'ensam' 'vårdnad' 'om'], before_plaint) for x in defend_first)
            or any(x in findterms(['dom' ,'förordn' ,' ensam' ,'vård'], before_plaint) for x in defend_first)
            ):
        init_l = 3
    
    else:
        init_l = 0
    
    #Initial physical
    if (
            findterms(['växelvist'], before_plaint)
            ):
        init_p = 1
    
    elif (
            any(x in findterms(['bor', child_first], before_plaint) for x in plaint_first)
            or any(x in findterms(['barn', 'stadigvarande', 'boende', ], before_plaint) for x in plaint_first)
            ):
        init_p = 2
        
    elif (
            any(x in findterms(['bor', child_first], before_plaint) for x in defend_first)
            or any(x in findterms(['barn', 'stadigvarande', 'boende', ], before_plaint) for x in defend_first)            ):
        init_p = 3
    
    else:
        init_p = 0
    
    #Temp legal
    if (
            findterms(['vård','förordn', 'interimistiskt', ' gemensam'], after_plaint)
            or findterms(['vård','interimistiskt' ,'beslut' ,'tingsrätt',' gemensam'], after_plaint)
            or findterms(['vård','förordn', ' för ', 'tiden', 'till', 'dess', 'dom', 'meddelas', ' gemensam'], after_plaint)
            or findterms(['vård', ' för ', 'tiden', 'till', 'dess', 'dom', 'meddelas' ,'beslut' ,'tingsrätt',' gemensam'], after_plaint)
            ):
        temp_l = 1
    
    elif (
            any(x in findterms(['vård','förordn', 'interimistiskt', ' gemensam'], after_plaint) for x in plaint_first)
            or any(x in findterms(['vård','interimistiskt' ,'beslut' ,'tingsrätt',' gemensam'], after_plaint) for x in plaint_first)
            or any(x in findterms(['vård','förordn', ' för ', 'tiden', 'till', 'dess', 'dom', 'meddelas', ' gemensam'], after_plaint) for x in plaint_first)
            or any(x in findterms(['vård', ' för ', 'tiden', 'till', 'dess', 'dom', 'meddelas' ,'beslut' ,'tingsrätt',' gemensam'], after_plaint) for x in plaint_first)
            ):
        temp_l = 2
        
    elif (
            any(x in findterms(['vård','förordn', 'interimistiskt', ' gemensam'], after_plaint) for x in defend_first)
            or any(x in findterms(['vård','interimistiskt' ,'beslut' ,'tingsrätt',' gemensam'], after_plaint) for x in defend_first) 
            or any(x in findterms(['vård','förordn', ' för ', 'tiden', 'till', 'dess', 'dom', 'meddelas', ' gemensam'], after_plaint) for x in defend_first)
            or any(x in findterms(['vård', ' för ', 'tiden', 'till', 'dess', 'dom', 'meddelas' ,'beslut' ,'tingsrätt',' gemensam'], after_plaint) for x in defend_first)

            ):
        temp_l = 3
    
    else:
        temp_l = 0
        
    #Temp physical
    if (
            findterms(['boende','förordn', 'interimistiskt', ' gemensam'], after_plaint)
            or findterms(['boende','interimistiskt' ,'beslut' ,'tingsrätt',' gemensam'], after_plaint)
            or findterms(['boende','förordn', ' för ', 'tiden', 'till', 'dess', 'dom', 'meddelas', ' gemensam'], after_plaint)
            or findterms(['boende', ' för ', 'tiden', 'till', 'dess', 'dom', 'meddelas' ,'beslut' ,'tingsrätt',' gemensam'], after_plaint)
            ):
        temp_p = 1
    
    elif (
            any(x in findterms(['boende','förordn', 'interimistiskt', ' gemensam'], after_plaint) for x in plaint_first)
            or any(x in findterms(['boende','interimistiskt' ,'beslut' ,'tingsrätt',' gemensam'], after_plaint) for x in plaint_first)
            or any(x in findterms(['boende','förordn', ' för ', 'tiden', 'till', 'dess', 'dom', 'meddelas', ' gemensam'], after_plaint) for x in plaint_first)
            or any(x in findterms(['boende', ' för ', 'tiden', 'till', 'dess', 'dom', 'meddelas' ,'beslut' ,'tingsrätt',' gemensam'], after_plaint) for x in plaint_first)
            ):
        temp_p = 2
        
    elif (
            any(x in findterms(['boende','förordn', 'interimistiskt', ' gemensam'], after_plaint) for x in defend_first)
            or any(x in findterms(['boende','interimistiskt' ,'beslut' ,'tingsrätt',' gemensam'], after_plaint) for x in defend_first) 
            or any(x in findterms(['boende','förordn', ' för ', 'tiden', 'till', 'dess', 'dom', 'meddelas', ' gemensam'], after_plaint) for x in defend_first)
            or any(x in findterms(['boende', ' för ', 'tiden', 'till', 'dess', 'dom', 'meddelas' ,'beslut' ,'tingsrätt',' gemensam'], after_plaint) for x in defend_first)

            ):
        temp_p = 3
    
    else:
        temp_p = 0


    #Temp visitation
    if (
            findterms(['umgänge','förordn', 'interimistiskt', ' gemensam'], after_plaint)
            or findterms(['umgänge','interimistiskt' ,'beslut' ,'tingsrätt',' gemensam'], after_plaint)
            or findterms(['umgänge','förordn', ' för ', 'tiden', 'till', 'dess', 'dom', 'meddelas', ' gemensam'], after_plaint)
            or findterms(['umgänge', ' för ', 'tiden', 'till', 'dess', 'dom', 'meddelas' ,'beslut' ,'tingsrätt',' gemensam'], after_plaint)
            ):
        temp_v = 1
    
    elif (
            any(x in findterms(['umgänge','förordn', 'interimistiskt', ' gemensam'], after_plaint) for x in plaint_first)
            or any(x in findterms(['umgänge','interimistiskt' ,'beslut' ,'tingsrätt',' gemensam'], after_plaint) for x in plaint_first)
            or any(x in findterms(['umgänge','förordn', ' för ', 'tiden', 'till', 'dess', 'dom', 'meddelas', ' gemensam'], after_plaint) for x in plaint_first)
            or any(x in findterms(['umgänge', ' för ', 'tiden', 'till', 'dess', 'dom', 'meddelas' ,'beslut' ,'tingsrätt',' gemensam'], after_plaint) for x in plaint_first)
            ):
        temp_v = 2
        
    elif (
            any(x in findterms(['umgänge','förordn', 'interimistiskt', ' gemensam'], after_plaint) for x in defend_first)
            or any(x in findterms(['umgänge','interimistiskt' ,'beslut' ,'tingsrätt',' gemensam'], after_plaint) for x in defend_first) 
            or any(x in findterms(['umgänge','förordn', ' för ', 'tiden', 'till', 'dess', 'dom', 'meddelas', ' gemensam'], after_plaint) for x in defend_first)
            or any(x in findterms(['umgänge', ' för ', 'tiden', 'till', 'dess', 'dom', 'meddelas' ,'beslut' ,'tingsrätt',' gemensam'], after_plaint) for x in defend_first)

            ):
        temp_v = 3
    
    else:
        temp_v = 0
    
    
    return init_l, init_p, temp_l, temp_p, temp_v



def filldict_rulings(
        data_rulings, child_id, file, page_count, correction, topwords, fulltext_og,
        ruling, plaint_og, plaint_first, plaint_no, plaint_lawyer,
        defend_og, defend_first, defend_no, defend_lawyer, defend_godman, 
        casetype, domskal_og, ruling_og, child_first, firstpage_form, 
        domskal, fulltext, caseno, courtname, date, year, judge, judgetitle,
        judge_gender, flag, judge_string, plaint_full, defend_full,
        d_lawyer_part, p_lawyer_part, plaint_made
        ):
    
    try:
        defend_secret = secret_address(defend_og)
        plaint_secret = secret_address(plaint_og)
        part = part_ruling(topwords)
        
        defend_abroad = get_defendabroad(defend_og, defend_first, defend_godman, fulltext_og, domskal_og)
        defend_unreach = defend_unreachable(defend_first, defend_godman, fulltext_og)
        out = get_outcome(fulltext_og, ruling_og, firstpage_form, child_id, child_first, plaint_first, defend_first)
        visit = get_visitation(child_first, ruling_og, plaint_first, defend_first)
        phys = get_physicalcustody(ruling_og, ruling, plaint_first, defend_first, child_first)
        alimony = get_alimony(ruling_og, plaint_first, defend_first)
        divorce_only, divorce_dummy = get_divorce(out, phys, visit, alimony, ruling)
        agree_cust, agree_any = get_agreement(domskal, domskal_og, fulltext, out)
        fastinfo = get_fastinfo(fulltext, fulltext_og)
        cooperation = get_cooperation(fulltext_og, fulltext)
        investigation = get_investigation(fulltext, fulltext_og)
        separate = separation_year(fulltext_og, fulltext)
        mainhear = get_mainhearing(fulltext_og)
        judge_string = judge_string.replace('\n', ' ')
        contact_person = get_contactp(ruling)
        visitation_type = get_visitation_type(ruling_og)
        p_legalguard, p_lawyer_legalaidact, p_lawyer_title, p_lawyer_name = get_lawyerinfo(p_lawyer_part)
        _ , d_lawyer_legalaidact, d_lawyer_title, d_lawyer_name = get_lawyerinfo(d_lawyer_part)
        child_id = child_id.replace(' ','')
        estate_dist = get_estate_dist(ruling_og)
        stay_in_home = get_stay_in_home(ruling_og, plaint_first, defend_first)
        plaint_legal, plaint_physical, plaint_visit, plaint_alim = get_plaintcategory(plaint_made)
        casetype_divorce, _ = get_custodybattle(fulltext_og, divorce_terms)
        init_l, init_p, temp_l, temp_p, temp_v = get_initial_temp(plaint_made, fulltext_og, plaint_first, defend_first,child_first)
        
        data_rulings['initial_legal'].append(init_l)
        data_rulings['initial_physical'].append(init_p)
        data_rulings['temp_legal'].append(temp_l)
        data_rulings['temp_physical'].append(temp_p)
        data_rulings['temp_visitation'].append(temp_v)    
        data_rulings['plaint_legal'].append(plaint_legal)
        data_rulings['plaint_physical'].append(plaint_physical)
        data_rulings['plaint_visitation'].append(plaint_visit)
        data_rulings['plaint_alimony'].append(plaint_alim)
        data_rulings['file_path'].append(file)
        data_rulings['plaint_made'].append(plaint_made)
        data_rulings['flag'].append(flag)
        data_rulings['child_id'].append(child_id)
        data_rulings['stay_in_home'].append(stay_in_home)
        data_rulings['estate_distribution_executor'].append(estate_dist)
        data_rulings['divorce'].append(divorce_dummy)
        data_rulings['p_lawyer_title'].append(p_lawyer_title)
        data_rulings['d_lawyer_title'].append(d_lawyer_title) 
        data_rulings['p_lawyer_name'].append(p_lawyer_name)
        data_rulings['d_lawyer_name'].append(d_lawyer_name) 
        data_rulings['p_lawyer_legalaidact'].append(p_lawyer_legalaidact)
        data_rulings['d_lawyer_legalaidact'].append(d_lawyer_legalaidact)  
        data_rulings['d_legalguard'].append(defend_godman)
        data_rulings['p_legalguard'].append(p_legalguard)
        data_rulings['contactperson'].append(contact_person)
        data_rulings['visitation_type'].append(visitation_type)
        data_rulings['plaintiff_name'].append(' '.join(plaint_full))
        data_rulings['defendant_name'].append(' '.join(defend_full))
        data_rulings['child_name'].append(child_first)
        data_rulings['page_count'].append(page_count)
        data_rulings['correction_firstpage'].append(correction)
        data_rulings['case_no'].append(caseno)
        data_rulings['casetype_custody'].append(casetype)
        data_rulings['casetype_divorce'].append(casetype_divorce)
        data_rulings['judge'].append(judge)
        data_rulings['judge_gender'].append(judge_gender)
        data_rulings['court'].append(courtname)
        data_rulings['date'].append(date)
        data_rulings['deldom'].append(part)
        data_rulings['divorce_only'].append(divorce_only)
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
        data_rulings['judge_text'].append(judge_string)

    except: 
        for i in data_rulings:
            data_rulings[i].append('error')

    return data_rulings



def filldict_register(
        data_register, case_type, defend_no, plaint_no, date,
        courtname, doc_type, caseno, judge, judgetitle, file, flag
        ):
    
    data_register['filepath'].append(file)
    #try:
        
    data_register['casetype'].append(case_type)
    data_register['judge'].append(judge)   
    data_register['judgetitle'].append(judgetitle) 
    data_register['defendant'].append(defend_no)            
    data_register['plaintiff'].append(plaint_no)
    data_register['date'].append(date)
    data_register["court"].append(courtname)
    data_register['type'].append(doc_type)  
    data_register['caseid'].append(caseno)
    data_register['flag'].append(flag)

    #except: 
     #   for i in data_register:
      #      data_register[i].append('error')
    
    return data_register



def save(dictionary, SAVE, COUNT, location):
    df = pd.DataFrame(dictionary)
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        if PRINT == 1:
            print(df)
    if SAVE == 1:
        if COUNT == 1 and APPEND == 0:
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
        
        text = open(file, "r")
        full_text = text.read()
        text.close()
        fulltext_form, firstpage_form, topwords, page_count, lastpage_form = get_ocrtext(full_text)
        judge_string = re.split(appeal, lastpage_form)[-1] 
        correction = 0
        readable = 0
    
    print_output("FULLTEXT", fulltext_form.split('delimiter'))
    fulltext_form = clean_text(fulltext_form, clean_general)
    firstpage_form = clean_text(firstpage_form, clean_general)
    header_form = get_header(firstpage_form)
    header_form = clean_text(header_form, clean_header)
    fulltext_og, fulltext = format_text(fulltext_form)
    caseno, courtname, date, year = basic_caseinfo(file, topwords)
    doc_type = get_doctype(file, topwords, fulltext_og)

    if readable == 1:
        judge, judgetitle = get_judge(doc_type, fulltext_og, fulltext, lastpage_form)
    else:
        judge, judgetitle = get_judge_scans(judge_string)

    judge_gender = gend.get_gender((judge.replace('-', ' ')).split()[0])
    
    if doc_type == 'dom' or doc_type == 'deldom':
    
        plaint_og, plaint_first, plaint_full, plaint_no, plaint_lawyer, p_lawyer_part, defend_og, defend_first, defend_full, defend_no, defend_lawyer, d_lawyer_part, defend_godman, casetype, plaint_made = get_plaint_defend(fulltext_form, header_form, year)    
        ruling_form, ruling_og, ruling = get_ruling(fulltext_form)
        case_type = get_casetype(defend_og, plaint_og, fulltext_og, ruling, firstpage_form)

        if not case_type == '1216B':
            domskal_og, domskal = get_domskal(fulltext_og, ruling_form)

            id_name = get_childname(ruling_og, plaint_first, defend_first, year)
            for child_id in id_name:
                child_first = id_name[child_id]
                
                # Save rulings data to file
                dict_rulings = filldict_rulings(
                    DATA_RULINGS, child_id, file, page_count, correction, topwords, fulltext_og,
                    ruling, plaint_og, plaint_first, plaint_no, plaint_lawyer,
                    defend_og, defend_first, defend_no, defend_lawyer, defend_godman, 
                    casetype, domskal_og, ruling_og, child_first, firstpage_form, 
                    domskal, fulltext, caseno, courtname, date, year, judge, judgetitle,
                    judge_gender, flag, judge_string, plaint_full, defend_full,
                    d_lawyer_part, p_lawyer_part, plaint_made
                    )
                save(dict_rulings, SAVE, COUNT, OUTPUT_RULINGS)
            
    else:
        case_type = 'N/A'

    # Save case register to csv
    dict_register = filldict_register(
        DATA_REGISTER, case_type, defend_no, plaint_no, date,
        courtname, doc_type, caseno, judge, judgetitle, file, flag
        )
    
    save(dict_register, SAVE, COUNT, OUTPUT_REGISTER)



#Execute
pics = cases_from_imgs()
scans = paths('.txt')

print("Pics: ", pics)
print("Scans: ", scans)

#For scanned pdfs
for file in scans:
    flag = []
    jpgs = 0
    
    if SAVE == 1:
        try:
            main(file, jpgs)
            print('+')
            
        except Exception as e:
            print(e)
            flag.append(e)
            dict_rulings = filldict_rulings(
                DATA_RULINGS, 'error', file, 'error', 'error', 'error', 'error',
            'error', 'error', 'error', 'error', 'error',
            'error', 'error', 'error', 'error', 'error', 
            'error', 'error', 'error', 'error', 'error', 
            'error', 'error', 'error', 'error', 'error', 'error', 'error', 'error',
            'error', flag, 'error', 'error', 'error',
            'error', 'error', 'error'
                    )
            
            save(dict_rulings, SAVE, COUNT, OUTPUT_RULINGS)
            
            dict_register = filldict_register(
                DATA_REGISTER, 'error', 'error', 'error', 'error',
                'error', 'error', 'error', 'error', 'error', file, flag
                )
            save(dict_register, SAVE, COUNT, OUTPUT_REGISTER)

    else:
        main(file, jpgs)

        
        
#For scans as photos (jpgs)
"""
for case in pics:
    jpgs = 1
    flag = []
    
    if SAVE == 1:
        try:
            main(case, jpgs)
            
        except Exception as e:
            
            flag.append(e)
            dict_rulings = filldict_rulings(
                    DATA_RULINGS, 'error', file, 'error', 'error', 'error', 'error',
                    'error', 'error', 'error', 'error', 'error', 'error','error',
                    'error', 'error', 'error', 'error','error', 'error', 'error',
                    'error', 'error','error', 'error', 'error', 'error', 'error',
                    'error', 'error', 'error', 'error', flag
                    )
            save(dict_rulings, SAVE, COUNT, OUTPUT_RULINGS)
            
            dict_register = filldict_register(
                DATA_REGISTER, 'error', 'error', 'error', 'error',
                'error', 'error', 'error', 'error', 'error', file, flag
                )
            save(dict_register, SAVE, COUNT, OUTPUT_REGISTER)
    else:
        main(case, jpgs)
"""
end_time = time.time()
print("\n----Time to run in minutes: ", (end_time-start_time)/60)
