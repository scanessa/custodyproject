# -*- coding: utf-8 -*-
"""
@author: Stella Canessa

This code reads in scanned documents, draws bounding boxes around text blocks
and OCR's the bounding boxes

"""
import os
import time
import pytesseract
import cv2
import subprocess
import itertools

from PIL import Image
from pdf2image import convert_from_path

from searchterms import unwanted_judgeterms

os.chdir('P:/2020/14/Kodning/Scans/all_scans')
start_time = time.time()

#Define paths
pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"

#General settings
LANG = 'swe'
CONFIG_TEXTBODY = '--psm 4 --oem 3'
CONFIG_ONELINE = '--psm 7 --oem 3'
CONFIG_FULL = '--psm 11 --oem 3'
kernal = cv2.getStructuringElement(cv2.MORPH_RECT, (25,25))
kernal_sign = cv2.getStructuringElement(cv2.MORPH_RECT, (9,9))



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



def get_contour_precedence(contour, cols):
    tolerance_factor = 10
    origin = cv2.boundingRect(contour)
    
    return ((origin[1] // tolerance_factor) * tolerance_factor) * cols + origin[0]



def preprocess(imread_img, image):
    """ Preproccess image for page_warp.py straightening."""
    
    #### PIL code for removing blue signature
    im = Image.open(image)

    R, G, B = im.convert('RGB').split()
    r = R.load()
    g = G.load()
    b = B.load()
    w, h = im.size
    
    
    # Convert non-black pixels to white
    for i in range(w):
        for j in range(h):
            if(
                    b[i, j] > 10
                    and 1.5*(r[i, j]) < b[i, j]
                    and 1.5*(g[i, j]) < b[i, j]
                    ):
                r[i, j] = 255 # Just change R channel
    
    # Merge just the R channel as all channels
    im = Image.merge('RGB', (R, R, R))
    im.save(image)
    
    imread_img = cv2.imread(image)
    ####
    
    gray = cv2.cvtColor(imread_img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (7,7), 0)
    thresh = cv2.adaptiveThreshold(blur, 255,cv2.ADAPTIVE_THRESH_MEAN_C,
                               cv2.THRESH_BINARY, 21, 20)

    return thresh


def detect_text(img, filename):
    
    bottom_left = []
    bottom_right = []
    top_left = []
    top_right = []


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
        ratio = w/h
        
        if ratio > 2 and y+h < height-35 and y > 10 and x > 10:
            
            bottom_left.append(y)
            bottom_right.append(y+h)
            top_left.append(x)
            top_right.append(x+w)
    
    y_min = min(bottom_left)
    h_max = max(bottom_right)
    x_min = min(top_left)
    w_max = max(top_right)

    crop = img[y_min:y_min+h_max, x_min:x_min+w_max]
    
    cv2.imwrite(filename + "crop.jpg", crop)



def txt_box(subprocess_output, kernal_input):
    """Draw contours around text boxes and OCR text."""

    string_list = []
    img = cv2.imread(subprocess_output)
    height, width, shape = img.shape
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (7,7), 0)
    thresh = cv2.adaptiveThreshold(blur, 255,cv2.ADAPTIVE_THRESH_MEAN_C,
                                   cv2.THRESH_BINARY_INV, 21, 20)
    dilate = cv2.dilate(thresh,kernal_input,iterations = 1)
    contours = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[0] if len(contours) == 2 else contours[1]
    contours = sorted(contours, key=lambda x:get_contour_precedence(x, img.shape[1]))

    for cnt in contours:
        x,y,w,h = cv2.boundingRect(cnt)
        ratio = w/h
        
        if ratio > 1:

            roi = img[y:y+h, x:x+w]
            #cv2.rectangle(img, (x,y),(x+w,y+h),(10,100,0),2)
            #cv2.imwrite("bbox.jpg",img)
            img_string = pytesseract.image_to_string(roi, lang=LANG, config = CONFIG_TEXTBODY)
            string_list.append(img_string)
    
    return string_list



def clean_text(text_list):
    text_list = [text.replace('\x0c', '') for text in text_list]
    text_list = [t for t in text_list if t]
    text_list = [t for t in text_list if t.replace('\n', '').strip()]
    
    return text_list
    

def final_passage(lastpage, passg):
    """
    Drops all works from last page string that come before last paragraph
    Last paragraph is recognized by ÖVERKLAG header
    Returns list, input should be list
    """
    if isinstance(lastpage, str):
        lastpage = lastpage.split(" ") #make sure all of these lists have individual words as their seperate strings
    lastpage = clean_text(lastpage)
    
    for term in ['ÖVERKLAG','Överklag','överklag']:
        if any(term in string for string in lastpage):
            lastpage = list(itertools.dropwhile(lambda x: term not in x, lastpage))
            lastpage = lastpage[1:]

    lastwords = [x.lower() for x in lastpage]
    lastpage = [x for x in lastwords if not any(unwant in x for unwant in unwanted_judgeterms)]
            
    return lastpage



def ocr_main(file):
    """Main function gets OCR'ed text from bounding boxes and saves to strings."""
    
    full_text = []
    header = []
    pdf = 0
    
    if file.endswith('.pdf'):
        path = pdf_to_jpg(file)
        pdf = 1
    elif file.endswith('.JPG') or file.endswith('.jpg'):
        path = []
        path.append(file)

    for page_no, image in enumerate(path):
        img = cv2.imread(image)
        filename = image.split('.')[0]
        
        if "Sodertorn" in filename:
            detect_text(img, filename)
            img = cv2.imread(filename + "crop.jpg")
            os.remove(filename + "crop.jpg")

        cv2.imwrite(filename + '_thresh.jpg', preprocess(img,image))
                
        subprocess.call([
            'python',
            'P:/2020/14/Kodning/Code/page_dewrap/page_dewarp.py',
            filename + '_thresh.jpg'
            ])

        text = txt_box(filename + '_thresh_straight.png', kernal)
        text = clean_text(text)

        if page_no == len(path)-1:

            last = cv2.imread(filename + '_thresh_straight.png')
            judge_small = txt_box(filename + '_thresh_straight.png', kernal_sign)
            judge_large = pytesseract.image_to_string(last, lang=LANG, config = CONFIG_FULL)

            passg = "judge_small"
            judge_small = final_passage(judge_small,passg)
            passg = "judge_large"
            judge_large = final_passage(judge_large, passg)

        full_text.append(text)
        header.append(text[:4])

        if pdf == 1:
            os.remove(filename + '.jpg')
        
        for file in [filename + '_thresh.jpg',
                     filename + '_thresh_straight.png'
                     ]:
            os.remove(file)
        
    return full_text, header, judge_small, judge_large
