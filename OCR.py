# -*- coding: utf-8 -*-
"""
This code reads in scanned documents, draws bounding boxes around text blocks
and OCR's the bounding boxes
@author: ifau-SteCa
"""
import itertools
import os
import subprocess
import time
import pytesseract
import cv2
from pdf2image import convert_from_path

os.chdir('P:/2020/14/Kodning/Scans/all_scans')
start_time = time.time()

#Define paths
pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"
PDF_DIR = 'P:/2020/14/Kodning/Scans/all_scans'

#General settings
LANGUAGE = 'swe'
CUSTOM_CONFIG = '--psm 4 --oem 3'
kernal = cv2.getStructuringElement(cv2.MORPH_RECT, (50,50))

def pdf_to_jpg(pdf):
    """ Convert PDF to into seperate JPG files."""

    img_files = []
    pages = convert_from_path(pdf, 350)
    i = 1
    pdf_name = pdf.split('.')[0]
    for page in pages:
        image_name = pdf_name + '_pg' + str(i) + ".jpg"
        page.save(image_name, "JPEG")
        i = i+1
        img_files.append(image_name)
    return img_files

def preprocess(img_path):
    """ Preproccess image for page_warp.py straightening."""

    image = cv2.imread(img_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255,
    	cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 21, 20)
    inverted = cv2.bitwise_not(thresh)
    median = cv2.medianBlur(inverted, 3)
    # erode = cv2.erode(median, np.ones((3,3), np.uint8), iterations=1) including erode
    # gives an error in the page dewarp script for 210929_114535
    return median

def get_contour_precedence(contour, cols):
    tolerance_factor = 10
    origin = cv2.boundingRect(contour)
    return ((origin[1] // tolerance_factor) * tolerance_factor) * cols + origin[0]

def bounding_boxes(subprocess_output):
    """Draw contours around text boxes and OCR text."""

    string_list = []
    img = cv2.imread(subprocess_output)
    height, width, shape = img.shape
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (7,7), 0)
    thresh = cv2.adaptiveThreshold(blur, 255,cv2.ADAPTIVE_THRESH_MEAN_C,
                                   cv2.THRESH_BINARY_INV, 21, 20)
    dilate = cv2.dilate(thresh,kernal,iterations = 1)
    contours = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[0] if len(contours) == 2 else contours[1]
    contours = sorted(contours, key=lambda x:get_contour_precedence(x, img.shape[1]))

    for cnt in contours:
        x,y,w,h = cv2.boundingRect(cnt)
        if (
                50 < h < 700 and w > 200 and y > 10 and y+h < height-35 
                or (700 < h < 2500 and w > 1000 and y > 100 and y+h < height-35)
                ):
            
            cv2.rectangle(img, (x,y),(x+w,y+h),(36,255,12),2)
            roi = img[y:y+h, x:x+w]
            cv2.rectangle(img, (x,y),(x+w,y+h),(36,255,12),2)
            img_string = pytesseract.image_to_string(roi, lang=LANGUAGE, config = CUSTOM_CONFIG)
            string_list.append(img_string)
            
    #cv2.imwrite("bbox.jpg", img)
    
    return string_list

def ocr_main(file):
    """Main function gets OCR'ed text from bounding boxes and saves to strings."""
    
    full_text = []
    header = []
    
    if file.endswith('.pdf'):
        path = pdf_to_jpg(file)
    elif file.endswith('.JPG'):
        path = file

    for image in path:
        filename = image.split('.')[0]
        cv2.imwrite(image.split('.')[0] + '_thresh.jpg', preprocess(image))

        subprocess.call([
            'python',
            'P:/2020/14/Kodning/Code/page_dewrap/page_dewarp.py',
            filename + '_thresh.jpg'
            ])

        text = bounding_boxes(filename + '_thresh_straight.png')
        full_text.append(text)
        header.append(text[:4])
        
        for file in [filename + '.jpg',
                     filename + '_thresh.jpg',
                     filename + '_thresh_straight.png']:
            os.remove(file)
        
    firstpage_form = ''.join(full_text[0])
    page_count = len(full_text)
    judge_string = ''.join(full_text[-1][-2:]) if len(full_text[-1]) >= 2 else full_text[-1][-1]
    lastpage_form = ''.join(full_text[-1])
    fulltext_form = ''.join(list(itertools.chain.from_iterable(full_text)))
    topwords = ''.join(list(itertools.chain.from_iterable(header)))

    return firstpage_form, lastpage_form, fulltext_form, judge_string, topwords, page_count

