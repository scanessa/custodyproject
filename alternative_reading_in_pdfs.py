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
    
Notes:
    Sometimes judge name is mistakenly read in after domskal heading, try to capture this maybe with strict restriction of 
    paragraph between? otherwise the code will always find 'something' after domskal
    
    
"""
appendixStart = '((?<!se )Bilaga [1-9]|(?<!se )Bilaga A|sida\s+1\s+av)'

import re, shutil, glob, io, pandas as pd

from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter

import PyPDF2

def searchKey(string, part, g):
    finder = re.compile(string)
    match = finder.search(part)
    if match is not None:
        searchResult = match.group(g)
    else:
        searchResult = None
    return searchResult

#Define Paths
pdf_dir = "P:/2020/14/Kodning/Test-round-2/check_cases"
output_path = 'P:/2020/14/Kodning/Test-round-2/custody_data_test2.csv'

#Read in PDFs
pdf_files = glob.glob("%s/*.pdf" % pdf_dir)
print(pdf_files)

pages_text = []

#Loop over files and extract data
for file in pdf_files:
    # creating a pdf file object
    pdfFileObj = open(file, 'rb')
     
    # creating a pdf reader object
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
     
    # printing number of pages in pdf file
    pageNos = pdfReader.numPages
     
    # creating a page object
    for i in range(0, pageNos):
        pageObj = pdfReader.getPage(i)
        pages_text.append(pageObj.extractText())

    # closing the pdf file object
    pdfFileObj.close()
 
    #Convert full text to clean string
    fullTextFormatted = ''.join(pages_text)
    firstPage = pages_text[0]
    if "Rättelse" in firstPage:
        fullTextOG = ' '.join(''.join(pages_text[1:]).split())
        firstPage = ' '.join(''.join(pages_text[1]).split())
        dummyRat = 1
    else:
        fullTextOG = ' '.join(''.join(pages_text).split())
        dummyRat = 0

    splitTextOG = re.split('_{10,40}', fullTextOG)
        
    if len(splitTextOG) > 1: 
        headerOG = re.split('_{10,40}', firstPage)[0]   
        header = headerOG.lower()    
        appendixPage = [i for i, item in enumerate(pages_text) if re.search(appendixStart, item)]
        if not appendixPage:
            appendixPageNo = len(pages_text)
        else:
            appendixPageNo = appendixPage[0]
        lastPageFormatted = '.'.join((pages_text[appendixPageNo-1]).split(".")) + '.'.join((pages_text[appendixPageNo-2]).split("."))
        lastPageFormatted3 = (pages_text[appendixPageNo-2]).split(".")
        lastPageOG = pages_text[appendixPageNo-1]
        lastPage = lastPageOG.lower()                       
        fullTextOG = (re.split(appendixStart, fullTextOG)[0])  
        fullText = fullTextOG.lower()
        rulingString = ''.join(re.split('_{10,40}',fullTextOG)[1:])
        try:
            rulingOnly = re.split('YRKANDEN', rulingString)[0].lower()
        except AttributeError:
            rulingOnly = re.split('(_{15,35}|-{15,35})', rulingString)[0].lower() 
        fullTextList = fullText.split(".")   
        
    
        
        
        
    print(fullText)
    
    print('judge name:')
    print(searchKey('\n\s*\n\s*(([A-ZÅÄÖ][a-zåäöé]+\s+){2,4})\n\s*\n', lastPageFormatted, 1))
    
    
    