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

Courts: "Alingsås",	"Attunda",	"Blekinge",	"Borås",	"Eksjö",	"Eskilstuna",	"Falu",	"Gotland",	"Gällivare",	"Gävle",	"Göteborg",	"Halmstad",	"Haparanda",	"Helsingborg",	"Hudiksvall",	"Hässleholm",	"Jönköping",	"Kalmar",	"Kristianstad",	"Linköping",	"Luleå",	"Lund",	"Lycksele",	"Malmö",	"Mora",	"Nacka",	"Norrköping",	"Norrtälje",	"Nyköping",	"Skaraborg",	"Skellefteå",	"Solna",	"Stockholm",	"Sundsvall",	"Södertälje",	"Södertörn",	"Uddevalla",	"Umeå",	"Uppsala",	"Varberg",	"Vänersborg",	"Värmland",	"Västmanland",	"Växjö",	"Ystad",	"Ångermanland",	"Örebro",	"Östersund",

"""

import re, io, os, pandas as pd 
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter

#Read in PDFs
rootdir = "P:/2020/14/Tingsrätter/ÖÖ_Case_Sorting_SC/Domar/all_cases/Check3"
output_path = "P:/2020/14/Kodning/court_docs_register1.csv"

pdf_files = []
unreadable_files = []

"""
exclude = set(["Alingsås",	"Attunda",	"Blekinge",	"Borås",	"Eksjö",	"Eskilstuna",	"Falu",	"Gotland",	"Gällivare",	
               "Gävle",	"Göteborg",	"Halmstad",	"Haparanda",	"Helsingborg",	"Hudiksvall",	"Hässleholm",	"Jönköping",	
               "Kalmar",	"Kristianstad",	"Linköping",	"Luleå",	"Lycksele",	"Malmö",	"Mora",	"Nacka",	
               "Norrköping",	"Norrtälje",	"Nyköping",	"Skaraborg",	"Skellefteå",	"Solna",	"Stockholm",	
               "Sundsvall",	"Södertälje",	"Södertörn",	"Umeå",	"Uppsala",	"Varberg",	"Vänersborg",	
               "Värmland",	"Västmanland",	"Växjö",	"Ystad",		"Örebro",	"Östersund"
               ])
"""
includes = 'all_cases'  #change back to all cases to loop over all files
for subdir, dirs, files in os.walk(rootdir, topdown=True):
    #for term in exclude:
        #if term in dirs:
            #dirs.remove(term)
    for file in files:
        if includes in subdir and file.endswith('.pdf'):
            pdf_dir = (os.path.join(subdir, file))
            pdf_files.append(pdf_dir)
            print(f"Dealing with file {subdir}/{file}")
            continue
        
#Initialize variables
noOfFiles = 0
noUnreadable = 0

#Define key functions
def findSentence(string, part):
    sentenceRes = [sentence + '.' for sentence in part.split('.') if string in sentence]
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

#Define search terms
svarandeSearch = ' Svarande|SVARANDE|Motpart|MOTPART|SVARANDE och KÄRANDE '
searchCaseNo = 'mål\s*(nr|nummer)?[:]?\s*t\s*(\d*.?.?\d*)'

date = '\d{4}-\d{2}-\d{2}'
plaintiff = '(Kärande|KÄRANDE)\s*((\w+\s?-?(\w+\s?-?)+?){1}((\w+\s?-?)*\w+))\s*[,]\s*(\d{6,10}.?.?(\d{4})?[,]?\s)?'
defendant = '(Svarande|SVARANDE|Motpart|MOTPART)\s*((\w+\s?-?(\w+\s?-?)+?){1}((\w+\s?-?)*\w+))\s*[,]\s*(\d{6,10}.?.?(\d{4})?[,]?\s)?'
party ='((\w+\s?-?(\w+\s?-?)+?){1}((\w+\s?-?)*\w+))\s*[,]\s*(\d{6,10}.?\s*(\d{4})?[,]?\s)?' 
idNo ='(\d{6,10}.?.?(\d{4})?[,]?\s)'
appendixStart = '(Bilaga [1-9]|Bilaga A|sida\s+1\s+av)'
word = '[a-zåäöé]{4,15}'

courtSearch = {
    '1': "((\w+ ){1})tingsr?.?ätt",
    '2': "((\w+){1})[.]?.?tingsratt"
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

judgeProtokollPreffix = '(Lagmannen|lagmannen|Rådmannen|rådmannen)'
judgeProtokollSuffix = '[,|;]?\s*[(]?((\w+) protokollförare)?[)]?\s*([A-Z]{2,})'

judgeSearchProtokoll = {
    '1': judgeProtokollPreffix + '\s*(([A-ZÅÄÖ][a-zåäöé]+\s*){2,4})' + judgeProtokollSuffix, #normal names
    '2': judgeProtokollPreffix + '\s*([A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ][a-zåäöé]+\s+)'+ judgeProtokollSuffix, #first name hyphenated
    '3': judgeProtokollPreffix + '\s*([A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s+)'+ judgeProtokollSuffix, #last name hypthenated
    '4': judgeProtokollPreffix + '\s*([A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s+)'+ judgeProtokollSuffix, #first and last name hyphenated
    '5': judgeProtokollPreffix + '\s*([A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ]\s[A-ZÅÄÖ][a-zåäöé]+\s+)'+ judgeProtokollSuffix #name with initial as second name
    }

#Define search word lists
falseJudgeName = ['domskäl', 'yrkanden', 'avgörandet', 'överklagar', 'tingsrätt']
remindTerms = ["erinrar", "påminn"]
legalGuardingTerms = ["social", "kommun", "nämnden", "stadsjurist"]

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
              
    #Intiialize dictionary
    data = {'case_id':[], 'type':[], 'case_type':[], 'court':[], 'year':[], 'plaintiff':[], 'defendant':[], 'judge':[], 'filepath':[]}
    data['filepath'].append(file)  
            
    #Convert full text to clean string
    firstPage = pages_text[0]
    if "Rättelse" in firstPage:
        fullTextOG = ''.join(pages_text[1:])
        firstPage = ''.join(pages_text[1])
    else:
        fullTextOG = ''.join(pages_text)
        
    splitTextOG = re.split('_{10,40}', fullTextOG)
    if len(splitTextOG) == 1:
        splitTextOG = re.split('[A-ZÅÄÖ]{5,}', fullTextOG)
    
    noOfFiles += 1                                                      
    headerOG = re.split('_{10,40}', firstPage)[0]   
    header = headerOG.lower()    
    appendixPage = [i for i, item in enumerate(pages_text) if re.search(appendixStart, item)]
    if not appendixPage:
        appendixPageNo = len(pages_text)
    else:
        appendixPageNo = appendixPage[0]
    lastPageFormatted1 = '.'.join((pages_text_formatted[appendixPageNo-1]).split("."))
    lastPageFormatted2 = '.'.join((pages_text_formatted[appendixPageNo-2]).split("."))
    lastPageFormatted = lastPageFormatted1 + lastPageFormatted2
    lastPageFormatted3 = (pages_text_formatted[appendixPageNo-1]).split(".")
    
    if "ÖVERKLAG" not in lastPageFormatted:
        judgePageNo = ([i for i, item in enumerate(pages_text) if re.search("ÖVERKLAG", item)])[0]+1
        lastPageFormatted = '.'.join((pages_text_formatted[judgePageNo-1]).split("."))
        print( (pages_text_formatted[judgePageNo-1]).split("."))
    
    lastPageOG = pages_text[appendixPageNo-1]
    lastPage = lastPageOG.lower()                       
    fullText = (re.split(appendixStart, fullTextOG)[0]).lower()   
    fullTextList = fullText.split(".")   
        
    try:
        svarandeStringOG = re.split(svarandeSearch, headerOG)[1] 
        kärandeStringOG = re.split('Kärande|KÄRANDE', (re.split(svarandeSearch, headerOG)[0]))[1]
        if svarandeStringOG == "":
            svarandeStringOG = re.split(svarandeSearch, headerOG)[2] 
        elif len(kärandeStringOG.split()) < 4:
            svarandeStringOG = re.split("(?i)SVARANDE och KÄRANDE|SVARANDE OCH GENKÄRANDE ", headerOG)[1]
            kärandeStringOG = re.split('(?i)KÄRANDE och SVARANDE|KÄRANDE OCH GENSVARANDE', (re.split("SVARANDE och KÄRANDE|SVARANDE OCH GENKÄRANDE ", headerOG)[0]))[1]
        svarandeString = svarandeStringOG.lower()
        kärandeString = kärandeStringOG.lower()
    except IndexError:
        try:
            svarandeStringOG = re.split('_{10,40}', (re.split('2[.]\s*', (re.split('1[.]\s*', (re.split('PARTER|Parter', headerOG)[1]))[1]))[1]))[0]
            kärandeStringOG = re.split('2[.]\s*', (re.split('1[.]\s*', (re.split('PARTER|Parter', headerOG)[1]))[1]))[0]
            svarandeString = svarandeStringOG.lower()
            kärandeString = kärandeStringOG.lower()
        except IndexError:
            try:
                svarandeStringOG = re.split("Hustrun|HUSTRUN", headerOG)[1] 
                kärandeStringOG = re.split('Mannen|MANNEN', (re.split("Hustrun|HUSTRUN", headerOG)[0]))[1]
                svarandeString = svarandeStringOG.lower()
                kärandeString = kärandeStringOG.lower()
            except IndexError:
                svarandeString = '-'
                kärandeString = '-'
    
    filename = file.lower() 
    
    #Case ID
    try:
        caseNo = ''.join((searchKey(searchCaseNo, fullText, 2)).split())
    except AttributeError:
        caseNo = "Not found"
    data['case_id'].append(caseNo)   

    #Document type
    if 'deldom' in filename or ' deldom ' in header:
        docType = "deldom"
    elif ' dom ' in filename or ' dom.' in filename or ' dom;' in filename or ' dom ' in header:
        docType = "dom"
    elif 'slutligt beslut' in filename:
        docType = "slutligt beslut"
    elif "Dagbok" in header or "dagbok" in header:
        docType = "dagbok"
    elif "Protokoll" in header or "protokoll" in header:
        docType = "protokoll"
    else:
        docType = "Not found"
    data['type'].append(docType)  

    #District Court
    courtName = searchLoop(courtSearch, fullText, 1).strip()
    if courtName is None or searchKey(word, courtName, 0) is None:
        courtName = "Not found"
    data["court"].append(courtName)
    
    #Year Closed
    try:
        year = searchKey(date, fullText, 0)
    except AttributeError:
        year = "Not found"
    data['year'].append(year)
    
    # Plaintiff and Defendant
    if docType == "dagbok":
        plaintNo = '-'
        defNo = '-'
    else:
        try: 
            #For documents where the plaintiff is clearly labeled by karande
            plaintNo = ''.join(searchKey(idNo, kärandeString, 0).split())
        except AttributeError:
            #For documents which don't label the plaintiff by kärande
            try:
                plaintNo = ''.join(searchKey(idNo, kärandeString, 0).split())
            except AttributeError:
                plaintNo = "-"
    data['plaintiff'].append(plaintNo) 

    # Defendant
    try: 
        #For documents where the defendant is clearly labeled by svarande
        defNo = ''.join(searchKey(idNo, svarandeString, 0).split())
    except AttributeError:
        #For documents which don't label the defendant by svarande
        try:
            defNo = ''.join(searchKey(idNo, svarandeString, 0).split())
        except AttributeError:
            defNo = "-"
    data['defendant'].append(defNo)            
    
    #Name of judge
    print(lastPageFormatted3)
    if docType == 'slutligt beslut' or docType == 'protokoll':
        judgeName = searchLoop(judgeSearchProtokoll, fullTextOG, 2)
    elif docType == 'dom' or docType == 'deldom':
        try:
            print("judge1")
            judgeName = (((searchLoop(judgeSearch, lastPageFormatted, 1)).split('\n'))[0]).strip()
        except:
            print("judge2")
            judgeName = fullText.split('.')[-1]
    else:
        judgeName = "Not found"
    data['judge'].append(judgeName)    

    #Get additional info from Doms
    if docType == 'dom' or docType == 'deldom':
        print("additional info from doms")
        rulingString = splitTextOG[1].lower() 
        rulingOnly = re.split('(_{15,35}|-{15,35}|yrkanden)', rulingString)[0]   
        
        #Case type
        # 1216 B: legal guardian cases
        for term in legalGuardingTerms:
            if term in svarandeString or term in kärandeString:
                print("2")
                caseType = "1216B"
        if "overflyttas" in fullText:
            print("3")
            caseType = "1216B"
        elif "ensamkommande flyktingbarn" in fullText:
            print("4")
            caseType = "1216B"
        elif 'de har inga gemensamma barn' in fullText:
            print("5")
            caseType = "1217B"
        elif 'äktenskapsskillnad' in rulingOnly or 'äktenskapsskillnad' in firstPage:
            if "vårdn" in rulingOnly: 
                for term in remindTerms:
                    if term in findSentence("vårdn", firstPage):
                        print("7")
                        caseType = "1217B"
                    else:
                        #1217 A: divorce and custody in same case/ruling
                        print("8")
                        caseType = "1217A"
            else:
                print("9") 
                caseType = "1217B"
        elif 'vårdn' in rulingOnly:
            print("10") 
            caseType = "1216A"
        elif "umgänge" or "umgås" in rulingOnly:
            #Physical custody cases
            print("11")
            caseType = "1216A"
        else:
            print("12")
            caseType = "Not found"
    else:
        print("12")
        caseType = "N/A"
    data['case_type'].append(caseType)
        
    #Save dictionary to csv
    
    df = pd.DataFrame(data)
    with pd.option_context('display.max_rows', None, 'display.max_columns', None): 
        print(df) 
    """
    if pageCount == 1 and noOfFiles == 1:
        df.to_csv(output_path, sep = ',', encoding='utf-8-sig', header=True)
    else:
        df.to_csv(output_path, mode = 'a', sep = ',', encoding='utf-8-sig', header=False)
    #Delete variables
    allvars = [caseNo, caseType, filename, docType, courtName, year, plaintNo, defNo, judgeName, svarandeStringOG, kärandeStringOG]
    for var in allvars:
        del var
    """
    """
except:
    noUnreadable += 1
    unreadable_files.append(file)
    continue
    """

print("Total files read in:")
print(noOfFiles)
print("Total unreadable:")
print(noUnreadable)
print("Unreadable files:")
print(unreadable_files)
print('Done')







