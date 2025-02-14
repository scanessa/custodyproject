# -*- coding: utf-8 -*-
"""
Created on Wed Apr 12 13:22:43 2023

@author: ifau-SteCa

Code to get the name of the last round of scanned docs (Malmö, Lund, 1992-1997)
"""

#Import packages
import glob
from PyPDF2 import PdfFileReader, PdfFileWriter
from pdf2image import convert_from_path
import pytesseract
import cv2
import csv
import os
from multiprocessing import Pool

pdfWriter = PdfFileWriter()
CONFIG_TEXTBODY = '--psm 7 --oem 3'
CORES = 15

paths = []
judges = []

#Get last page as image
def extract_page_pdf(file):
    """
    Input: path of files where one page should be extracted

    """

    #Extract last page as pdf
    file_base_name = file.replace('.pdf', '')
    pdf = PdfFileReader(file)
    page_num = pdf.numPages - 1
    
    pdfWriter.addPage(pdf.getPage(page_num))
    
    with open('{0}_subset.pdf'.format(file_base_name), 'wb') as f:
        pdfWriter.write(f)
        f.close()
    
    #Save as image
    images = convert_from_path(file.replace('.pdf', '_subset.pdf'))
    for i in range(len(images)):
       images[i].save(file.replace('.pdf', '_pic.JPG'), 'JPEG')



#Get name from image
def get_text(filename):
    """ 
    Uses detect text function to read text only from area on page where text
    could be extracted with high accuracy
    """
    img = cv2.imread(filename)
    text = pytesseract.image_to_string(img, lang="swe", config = CONFIG_TEXTBODY)

    text = text.replace('”', '').replace('"', '').replace('|', '')
    paths.append(filename)
    judges.append(text)



def save(folder):
    rows = zip(paths, judges)
    
    with open(folder + "judge_names.csv", "w") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)



def main(folder):
    """
    Inputs: folder where files lie that should be transcribed
    """
    os.chdir(folder)
    files_raw = glob.glob(folder + '*.pdf')
    with Pool(CORES) as p:
        p.map(extract_page_pdf, files_raw)
    
    files_img = glob.glob(folder + '*_pic.JPG') 
    for file in files_img:
        get_text(file)
    
    save(folder)
        
    
        
#Execute
if __name__ == '__main__':
    #main("P:/2020/14/Kodning/Scans/all_scans/")
    main("P:/2020/14/Tingsratter/Malmo/Domar/all_scans/new/")
    
    
    
    
    
    
    
    
    
    
    
    
