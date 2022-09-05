# -*- coding: utf-8 -*-
"""
@author: Stella Canessa

This code reads in scanned documents, draws bounding boxes around text blocks
and OCR's the bounding boxes

When converting pages to imgs it starts numbering with 10 to keep the correct order,
otherwise python will read pages 1,2,3,4,5,6,7,8,9,10 as 1,10,2,3,4,5....
"""
import os
import time
import pytesseract
import cv2
import itertools
import pandas as pd
import glob
import shutil

from fpdf import FPDF
from PIL import Image
from pdf2image import convert_from_path
from io import StringIO
from multiprocessing import Pool
from collections import defaultdict
from page_dewarp import dewarp_main

start_time = time.time()
pdf_converter = FPDF()

#Define paths
pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"
PATH = "P:/2020/14/Kodning/Test-round-5-Anna/all_scans/second500/"

#General settings
LANG = 'swe'
CONFIG_TEXTBODY = '--psm 6 --oem 3' 
CONFIG_FULL = '--psm 11 --oem 3'

kernal_sign = cv2.getStructuringElement(cv2.MORPH_RECT, (11,11))


def pdf_to_jpg(pdf):
    """
    Convert PDF to into seperate JPG files and classifies pages in appendix/court page
    appendix = True if page is an appendix page, include i>1 in if statement because 
    first page is never an appendix
    """
    
    try:
        
        img_files = []
        ocr_error = ''
        i = 10
        pages = convert_from_path(pdf, 300)
        pdf_name = ''.join(pdf.split('.pdf')[:-1])
        
        for page in pages:
            image_name = pdf_name + '--pg' + str(i) + ".jpg"
            page.save(image_name, "JPEG")
            
            img_files.append(image_name)
            
            i = i+1
    
        return img_files, ocr_error
    
    except:
        current_path = os.getcwd()
        new_path = current_path + '/ocr_errors/'
        os.chdir(new_path)
        shutil.copy(pdf,new_path)
        os.chdir(current_path)
        return

def main():
    path = PATH
    os.chdir(path)

    lst = glob.glob(path + '*.pdf')

    #Converts each page in a pdf to an image
    with Pool(60) as p:
        p.map(pdf_to_jpg, lst)



if __name__ == '__main__':
    
    path = PATH
    files = glob.glob(path + '*.pdf')
    start = time.time()

    main()
    
    done = time.time()
    elapsed = done - start
    print(elapsed)
    
    

