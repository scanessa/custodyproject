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
import itertools
from PIL import Image
from pdf2image import convert_from_path
from signature_extractor import extract_signature
from page_dewarp import dewarp_main


os.chdir('P:/2020/14/Kodning/Scans/all_scans')
start_time = time.time()

#Define paths
pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"

#General settings
LANG = 'swe'
CONFIG_TEXTBODY = '--psm 6 --oem 3'
CONFIG_ONELINE = '--psm 7 --oem 3'
CONFIG_FULL = '--psm 11 --oem 3'
kernal = cv2.getStructuringElement(cv2.MORPH_RECT, (55,55)) #used to be 25
kernal_sign = cv2.getStructuringElement(cv2.MORPH_RECT, (9,9))
kernal_lines = cv2.getStructuringElement(cv2.MORPH_RECT, (9,1)) 




def pdf_to_jpg(pdf):
    """ Convert PDF to into seperate JPG files."""

    img_files = []
    pages = convert_from_path(pdf, 350)
    i = 1
    pdf_name = ''.join(pdf.split('.')[:-1])
    for page in pages:
        image_name = pdf_name + '_pg' + str(i) + ".jpg"
        page.save(image_name, "JPEG")
        i = i+1
        img_files.append(image_name)

    return img_files



def detect_text(img, filename):
    """ Detects text and crops at text box for Sodertorns files dewarp """
    
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
    sorted_contours = sort_contours(contours)
        
    for cnt in sorted_contours:
        x,y,w,h = cnt[0], cnt[1], cnt[2], cnt[3]
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
    
    return crop



def remove_color(image):
    """ PIL code for removing blue signature """
    
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

    return imread_img



def sort_contours(contours):
    """ 
    Saves corners of each contour to rect list; sorts corners by y value and groups into lines;
    max_height varies the maximum height of a line (by how much the y-values within a line-group can vary)
    Returns list of sorted corners of contour boxes
    """
    rect = []
    for cnt in contours:
        x,y,w,h = cv2.boundingRect(cnt)
        rect.append((x,y,w,h))

    max_height = 25
    
    by_y = sorted(rect, key=lambda x: x[1])
    
    line_y = by_y[0][1]
    line = 1
    by_line = []

    for x, y, w, h in by_y:
        if y > line_y + max_height:
            line_y = y
            line += 1
            
        by_line.append((line, x, y, w, h))
    
    contours_sorted = [(x, y, w, h) for line, x, y, w, h in sorted(by_line)]
    return contours_sorted



def remove_lines(threshed_img, imread_img):

    dilate = cv2.dilate(threshed_img,kernal_lines,iterations = 1)

    # Remove horizontal
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25,1))
    detected_lines = cv2.morphologyEx(dilate, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    cnts = cv2.findContours(detected_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for c in cnts:
        cv2.drawContours(imread_img, [c], -1, (255,255,255), 2)
    
    # Repair image
    repair_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1,6))
    result = 255 - cv2.morphologyEx(255 - imread_img, cv2.MORPH_CLOSE, repair_kernel, iterations=1)
    result = cv2.bitwise_not(result)
    
    return result



def txt_box(dewarp_output, kernal_input):
    """Draw contours around text boxes and OCR text."""

    string_list = []
    img = cv2.imread(dewarp_output)
    height, width, shape = img.shape
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (17,17), 0)
    thresh = cv2.adaptiveThreshold(blur, 255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 15, 20)
    
    dilate = cv2.dilate(thresh,kernal_input,iterations = 1)
    
    contours = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[0] if len(contours) == 2 else contours[1]
    sorted_contours = sort_contours(contours)
    
    counter = 1

    for cnt in sorted_contours:
        x,y,w,h = cnt[0], cnt[1], cnt[2], cnt[3]
        ratio = w/h
        
        if ratio > 1:
            
            roi = img[y:y+h, x:x+w]
            
            #cv2.rectangle(img, (x,y),(x+w,y+h),(10,100,0),2)
            #cv2.putText(img=img, text=str(counter), org=(x, y), fontFace=cv2.FONT_HERSHEY_TRIPLEX, fontScale=1, color=(0, 255, 0),thickness=1)
            #cv2.imwrite("bbox.jpg",img)
            
            img_string = pytesseract.image_to_string(roi, lang=LANG, config = CONFIG_TEXTBODY)
            string_list.append(img_string)
            
            counter += 1
    
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
        filename = ''.join(image.split('.')[:-1])
        
        if page_no == len(path)-1:
            #fp = path[-1].split('\\')[0] + '/'
            #fn = path[-1].split('\\')[1]
            #extract_signature(fp, fn)
            img = remove_color(image)
        if "Sodertorn" in filename:
            img = detect_text(img, filename)
            cv2.imwrite("crop.jpg", img)
        
        dewarp_main(filename + '.jpg')
        text = txt_box(filename + '_straight.png', kernal)
        text = clean_text(text)
        
        """
        if page_no == len(path)-1:

            last = cv2.imread(filename + '_straight.png')
            judge_small = txt_box(filename + '_straight.png', kernal_sign)
            judge_large = pytesseract.image_to_string(last, lang=LANG, config = CONFIG_FULL)

            passg = "judge_small"
            judge_small = final_passage(judge_small,passg)
            passg = "judge_large"
            judge_large = final_passage(judge_large, passg)
        
        """
        judge_small = judge_large = [""] # only to speed up testing docs
        
        full_text.append(text)
        header.append(text[:10])

        if pdf == 1:
            os.remove(filename + '.jpg')
            os.remove(filename + '_straight.png')

    return full_text, header, judge_small, judge_large

#ocr_main("P:/2020/14/Kodning/Scans/all_scans/Skelleftea_TR_T_93-00_deldom_2000-01-18_pg1.jpg")
