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
rootdir = "P:/2020/14/Tingsrätter/"
output_path = r'P:/2020/14/Kodning/court_docs_register1.csv'

pdf_files = []

exclude = set(["Alingsås",	"Attunda",	"Blekinge",	"Borås",	"Eksjö",	"Eskilstuna",	"Falu",	"Gotland",	"Gällivare",	
               "Gävle",	"Göteborg",	"Halmstad",	"Haparanda",	"Helsingborg",	"Hudiksvall",	"Hässleholm",	"Jönköping",	
               "Kalmar",	"Kristianstad",	"Linköping",	"Luleå",	"Lycksele",	"Malmö",	"Mora",	"Nacka",	
               "Norrköping",	"Norrtälje",	"Nyköping",	"Skaraborg",	"Skellefteå",	"Solna",	"Stockholm",	
               "Sundsvall",	"Södertälje",	"Södertörn",	"Umeå",	"Uppsala",	"Varberg",	"Vänersborg",	
               "Värmland",	"Västmanland",	"Växjö",	"Ystad",		"Örebro",	"Östersund"

               ])
includes = 'all_cases'
for subdir, dirs, files in os.walk(rootdir, topdown=True):
    for term in exclude:
        if term in dirs:
            dirs.remove(term)
    for file in files:
        if includes in subdir:
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
    searchResult = finder.search(part).group(g)
    return searchResult

#Define search terms
searchCaseNo = 'mål\s*(nr|nummer)?[:]?\s*t\s*(\d*.?.?\d*)'
courtSearchKey = "((\w+ ){1})tingsr?.?ätt"
courtSearchEmail = "((\w+){1})[.]?.?tingsratt"
date = '\d{4}-\d{2}-\d{2}'
judge1 = "på (tings)?rättens vägnar\s*(\w+ \w+)"
judge2 = "prövningstillstånd krävs[.]?\s*_*\s*(\w+ \w+)"  
judge3 = "ÖVERKLAGANDE (((\w+ )+(\w+))[.]\s?)+\s?(\w+ \w+)" 
judge4 = '(Lagmannen|Rådmannen|rådmannen|Tingsfiskalen|Tingsnotarien)\s*((\w+ ){1,3}((\w+){1}))[,|;|\s+]\s*[(]?((\w+) protokollförare)?[)]?\s*([A-Z]{2,})'
judge5 = '(för tingsrätten)\s*((\w+\s?-?(\w+\s?-?)+?){1}((\w+\s?-?)*\w+))'
plaintiff = '(Kärande|KÄRANDE)\s*((\w+\s?-?(\w+\s?-?)+?){1}((\w+\s?-?)*\w+))\s*[,]\s*(\d{6,10}.?.?(\d{4})?[,]?\s)?'
defendant = '(Svarande|SVARANDE|Motpart|MOTPART)\s*((\w+\s?-?(\w+\s?-?)+?){1}((\w+\s?-?)*\w+))\s*[,]\s*(\d{6,10}.?.?(\d{4})?[,]?\s)?'
party ='((\w+\s?-?(\w+\s?-?)+?){1}((\w+\s?-?)*\w+))\s*[,]\s*(\d{6,10}.?\s*(\d{4})?[,]?\s)?' 
idNo ='(\d{6,10}.?.?(\d{4})?[,]?\s)'
appendixStart = '(Bilaga [1-9]|Bilaga A|sida\s+1\s+av)'

#Define search word lists
falseJudgeName = ['domskäl', 'yrkanden', 'avgörandet', 'överklagar', 'tingsrätt']

for file in pdf_files: 
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
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,caching=True,check_extractable=True):
            read_position = retstr.tell()
            interpreter.process_page(page)
            retstr.seek(read_position, 0)
            page_text = retstr.read()
            page_text_clean = ' '.join((''.join(page_text)).split())
            pages_text.append(page_text_clean)
            pageCount += 1
    
    #Intiialize lists and dictionary to fill
    data = {'case_id':[], 'type':[], 'case_type':[], 'court':[], 'year':[], 'plaintiff':[], 'defendant':[], 'judge':[], 'filepath':[]}

    data['filepath'].append(file)  
            
    #Convert full text to clean string
    firstPage = pages_text[0]
    if "Rättelse" in firstPage and pageCount > 1:
        firstPage = ''.join(pages_text[1])
        fullTextOG = ''.join(pages_text[1:])
    elif "Rättelse" in firstPage and pageCount < 1:
        firstPage = ''.join(pages_text[0])
        fullTextOG = ''.join(pages_text)
    else:
        fullTextOG = ''.join(pages_text)
        
    splitTextOG = re.split('_{10,40}', fullTextOG)
    noOfFiles += 1                                                      
    firstStringOG = splitTextOG[0] 
    header = re.split('_{10,40}', firstPage)[0]                                   
    firstString = firstStringOG.lower()
    appendixPage = [i for i, item in enumerate(pages_text) if re.search(appendixStart, item)]
    if not appendixPage:
        appendixPageNo = len(pages_text)
    else:
        appendixPageNo = appendixPage[0]
    lastPage = pages_text[appendixPageNo-1].lower()
    fullText = (re.split(appendixStart, fullTextOG)[0]).lower()   
    fullTextList = fullText.split(".") 
    filename = file.lower()           
    
    try:
        svarandeStringOG = re.split(' Svarande|SVARANDE|Motpart|MOTPART|Hustrun|HUSTRUN', header)[1] 
        kärandeStringOG = re.split('Kärande|KÄRANDE|SÖKANDE|Sökande|Mannen|MANNEN', (re.split(' Svarande|SVARANDE|Motpart|MOTPART|Hustrum|HUSTRUM', header)[0]))[1]
        if svarandeStringOG == "":
            svarandeStringOG = re.split(' Svarande|SVARANDE|Motpart|MOTPART|Hustrum|HUSTRUM', header)[2] 
        svarandeString = svarandeStringOG.lower()
        kärandeString = kärandeStringOG.lower()
    except IndexError:
        try:
            svarandeStringOG = re.split('_{10,40}', (re.split('2[.]\s*', (re.split('1[.]\s*', (re.split('PARTER|Parter', header)[1]))[1]))[1]))[0]
            kärandeStringOG = re.split('2[.]\s*', (re.split('1[.]\s*', (re.split('PARTER|Parter', header)[1]))[1]))[0]
            svarandeString = svarandeStringOG.lower()
            kärandeString = kärandeStringOG.lower()
        except:
            svarandeString = '-'
            kärandeString = '-'

    #Case ID
    try:
        caseNo = ''.join((searchKey(searchCaseNo, fullText, 2)).split())
    except AttributeError:
        caseNo = "Not found"
    data['case_id'].append(caseNo)   

    #Document type
    if 'deldom' in filename:
        docType = 1
    elif ' dom ' in filename:
        docType = 2
    elif 'slutligt beslut' in filename:
        docType = 3
    else:
        docType = 999
    data['type'].append(docType)  
                
    #District Court
    try:
        courtName = searchKey(courtSearchKey, fullText, 0)
    except AttributeError:
        try:
            #Get court name from email
            courtName = searchKey(courtSearchEmail, fullText, 0)
        except AttributeError:
            courtName = "Not found"
    data["court"].append(courtName)
    
    #Year Closed
    try:
        year = searchKey(date, fullText, 0)
    except AttributeError:
        year = "Not found"
    data['year'].append(year)
    
    # Plaintiff
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
    if docType == 2 or docType == 999:
        try:
            print("a")
            judgeName = searchKey(judge1, fullText, 2)
        except AttributeError:
            try:
                print("b")
                judgeName = searchKey(judge2, fullText, 1)
            except AttributeError:
                try:
                    print("c")
                    judgeName = searchKey(judge3, fullText, 5)
                except AttributeError:
                    #keep the last 10 strings, find the string wiht nämndemännen and from that string take the first 2-3 words
                    print("d")
                    endTextList = fullTextList[-10:]
                    judgeSearch = ''.join([k for k in endTextList if 'nämndemännen' in k])
                    if judgeSearch != '':
                        print("e")
                        judgeName = re.split('i avgörandet|i målets|i avgrandet|tingsrätt', judgeSearch)[0]
                    else:
                        try:
                            print("f")
                            judgeName = searchKey(judge5, lastPage, 2)
                        except AttributeError:
                            print("g")
                            judgeName = fullTextList[-1]
        for term in falseJudgeName:
            if term in judgeName:
                print('h')
                judgeName = fullTextList[-1]
    else:
        try:
            print("i")
            judgeName = searchKey(judge4, fullTextOG, 2)
        except AttributeError:
            print("j")
            judgeName = "Not found"
    data['judge'].append(judgeName)
    
    #Get additional info from Doms
    if len(splitTextOG) > 1:
        rulingString = splitTextOG[1].lower() 
        rulingOnly = re.split('(_{15,35}|-{15,35}|yrkanden)', rulingString)[0]   
        
        #Case type
        # 1216 B: legal guardian cases
        if 'särskilt förordnad vårdnadshavare' in fullText:
            caseType = "1216B"
        elif "social" in svarandeString or "social" in kärandeString or "kommun" in svarandeString or "kommun" in kärandeString or "nämnden" in svarandeString or "nämnden" in kärandeString or "stadsjurist" in svarandeString or "stadsjurist" in kärandeString:             
            caseType = "1216B"
        elif "overflyttas" in fullText:
           caseType = "1216B"
        elif "ensamkommande flyktingbarn" in fullText:
            caseType = "1216B"
        #1217 B: divorce without custody battle
        elif 'de har inga gemensamma barn' in fullText:
            caseType = "1217B"
        #1217 A: divorce with custody
        elif "deldom" in firstString:
            caseType = "1217A"
        elif 'äktenskapsskillnad' in rulingOnly:
            if "vårdn" in rulingOnly:
                if "påminner" in findSentence("vårdn", rulingOnly):
                    caseType = "1217B"
                else:
                    #1217 A: divorce and custody in same case/ruling
                    caseType = "1217A"
            else:
                 caseType = "1217B"
        #1216 A: custody without divorce
        elif 'vårdn' in rulingOnly:
             caseType = "1216A"
        elif "umgänge" or "umgås" in rulingOnly:
            #Physical custody cases
             caseType = "1216A"
        else:
            caseType = "Not found"
    else:
        caseType = "Not found"
    data['case_type'].append(caseType)

    #Save dictionary to csv
    df = pd.DataFrame(data)
    with pd.option_context('display.max_rows', None, 'display.max_columns', None): 
        print(df)
    df.to_csv(output_path, mode = 'a', sep = ',', encoding='utf-8-sig', header=False)

print('Done')







