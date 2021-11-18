# -*- coding: utf-8 -*-
"""
Created on Wed Oct 20 11:14:05 2021

@author: ifau-SteCa

Code loops thorugh court work orders and checks for mention of lotteries, saves the outcome as a binary variable and the respective year to a csv file
"""
import re, io, os, pandas as pd
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter
#import docx 

#Read in PDFs
rootdir = "P:/2020/14/Tingsrätter/"
output_path = 'P:/2020/14/Kodning/lottery_data.csv'

pdf_files = []
unreadable_files = []

"""
exclude = set(["Alingsås",	"Attunda",	"Blekinge",	"Borås",	"Eksjö",	"Eskilstuna",	"Falu",	"Gotland",	"Gällivare"
               ])
"""
includes = 'Arbetsordningar'  
for subdir, dirs, files in os.walk(rootdir, topdown=True):
    #for term in exclude:
        #if term in dirs:
            #dirs.remove(term)
    for file in files:
        if includes in subdir and file.endswith('.pdf'):
            filepath = (os.path.join(subdir, file))
            pdf_files.append(filepath)
            print(f"Dealing with file {subdir}/{file}")
            continue

#Intiialize lists and dictionary to fill
data = {"court":[], "date": [], "lottery": [], "file": [] }
countUnreadable = 0
unreadableDocs = []
countFiles = 0

#Initialize key function
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
"""
def getText(filename):
    doc = docx.Document(filename)
    fullText = []
    for para in doc.paragraphs:
        fullText.append(para.text)
    return '\n'.join(fullText)
"""
#Initialize search terms
dateSearch = {
    '1': "\d{4}-\s?\d{2}\s?-\s?\d{2}",
    '2': "\d+\s+((\w+ ){1})\s?\d{4}"
    }
        
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
    fullTextOG = ' '.join(''.join(pages_text).split())    
    fullText = fullTextOG.lower()  

    #Check if doc is readable
    if fullText == "":
        countUnreadable += 1
        #Generate empty row to check manually
        data["court"].append("-")
        data["date"].append("-")
        data["lottery"].append(999)
        data["file"].append(file)
    else:
        #Get district court name
        courtName = searchKey('Tingsrätter/(\w+)', file, 1)
        data["court"].append(courtName)
   
        #Get date 
        date = searchLoop(dateSearch, fullText, 0)
        data["date"].append(date)

        #Lottery
        if "lotteri" in fullText or "lottas" in fullText or "lottning" in fullText:
            dummy = 1
            data["lottery"].append(dummy)
        else:
            dummy = 0
            data["lottery"].append(dummy)
        
        #File name
        data["file"].append(file)
        
#Dataframe created from dictionary
df = pd.DataFrame(data)
with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    print(df)

#Save to csv
df.to_csv(output_path, sep = ',', encoding='utf-8-sig')


    
    
    
    
    
    
    
    
    
    
    
    
