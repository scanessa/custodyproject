# -*- coding: utf-8 -*-
"""
Created on Wed Oct 20 11:14:05 2021

@author: ifau-SteCa

Code loops thorugh court work orders and checks for mention of lotteries, saves the outcome as a binary variable and the respective year to a csv file
"""
import re
import pandas as pd
import glob
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter
import io

#Define Paths
#Where to find PDFs that code should loop through
pdf_dir = "P:/2020/14/Tingsrätter/ÖÖ_Case_Sorting_SC/Work orders" 
#Where to output CSV to
output_path = r'/P:/2020/14/Kodning/lottery_data.csv'

#Automatically read in all pdfs in folder
pdf_files = glob.glob("%s/*.pdf" % pdf_dir)

#Intiialize lists and dictionary to fill
data = {"Court":[], "Date": [], "Lottery": [], "File name": [] }
countUnreadable = 0
countDateError = 0
countCourtError = 0
countFiles = 0
        
#Loop over files and extract data
for file in pdf_files:
    #Read in text from each PDF  
    countFiles += 1
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)

    with open(file, 'rb') as fh:

        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)

        text = fake_file_handle.getvalue()

    # close open handles
    converter.close()
    fake_file_handle.close()

    #Convert full text to clean string
    fullText = ''.join(text)
    fullText = ' '.join(fullText.split())    
    fullTextOG = fullText
    fullText = fullText.lower()  

    #Check if doc is readable
    if fullText == "":
        errorMessage = "File at path %s not readable." %(file)
        print("-")
        countUnreadable += 1
        #Generate empty row to check manually
        data["Court"].append("-")
        data["Date"].append("-")
        data["Lottery"].append(999)
        data["File name"].append(file)
    else:
        #Eliminate irrelevant docs 
        print(".")
        
        #Get district court name
        try:
            courtSearchKey = "((\w+ ){1})tingsr?.?ätt"
            courtSearch = re.compile(courtSearchKey)
            courtSearchRes = courtSearch.search(fullText).group(0)
            data["Court"].append(courtSearchRes)
        except AttributeError:
            try:
                #Get court name from email
                courtSearchKey = "((\w+){1})[.]?.?tingsratt"
                courtSearch = re.compile(courtSearchKey)
                courtSearchRes = courtSearch.search(fullText).group(0)
                data["Court"].append(courtSearchRes)
            except AttributeError:
                print("Court name error in file %s" %(file))
                print(fullText)
                courtSearchRes = "Error, not found"
                data["Court"].append(courtSearchRes)
                countCourtError += 1
        
        #Get date 
        try:
            dateKey = "\d{4}-\s?\d{2}\s?-\s?\d{2}"
            dateSearch = re.compile(dateKey)
            dateSearchRes = dateSearch.search(fullText).group(0)
            data["Date"].append(dateSearchRes)
        except AttributeError:
            try:
                dateKey = "\d+\s+((\w+ ){1})\s?\d{4}"
                dateSearch = re.compile(dateKey)
                dateSearchRes = dateSearch.search(fullText).group(0)
                data["Date"].append(dateSearchRes)
            except AttributeError:
                print("Date error in file %s" %(file))
                print(fullText)
                dateSearchRes = "Error, not found"
                data["Date"].append(dateSearchRes)
                countDateError += 1
        
        #Lottery
        if "lotteri" in fullText or "lottas" in fullText or "lottning" in fullText:
            dummy = 1
            data["Lottery"].append(dummy)
        else:
            dummy = 0
            data["Lottery"].append(dummy)
        
        #File name
        data["File name"].append(file)
        
#Dataframe created from dictionary
df = pd.DataFrame(data)
print(df)
print("Files where the court name is not detected: %s" %(countCourtError))
print("Files where the date is not detected: %s" %(countDateError))
print("Files that are not readable: %s" %(countUnreadable))

#Save to csv
#df.to_csv(output_path, sep = ';', encoding='utf-8-sig')


    
    
    
    
    
    
    
    
    
    
    
    
