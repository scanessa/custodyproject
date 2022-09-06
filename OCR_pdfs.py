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
from appendix_classification import predict

start_time = time.time()
pdf_converter = FPDF()

#Define paths
pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"
PATH = "P:/2020/14/Kodning/Scans/all_scans/"

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



def detect_text(imread_img):
    """
    OCRs full page to data and identifies text region through high confidence 
    word matches (90% in general, 70% for first 3 lines of text to capture
    case number and date)
    """
    img_rgb = cv2.cvtColor(imread_img, cv2.COLOR_BGR2RGB)
    ocr_data = pytesseract.image_to_data(img_rgb, lang="swe", config='--psm 6')
    ocr_df = pd.read_table(StringIO(ocr_data), quoting=3)
        
    confident_words_df = ocr_df[
        (ocr_df["conf"] > 90)
        & (ocr_df["line_num"] > 3)
        & (ocr_df["text"].str.len() - ocr_df["text"].str.count(" ") > 3)
        | (ocr_df["conf"] > 70)
        & (ocr_df["line_num"] <= 3)
        & (ocr_df["text"].str.len() - ocr_df["text"].str.count(" ") > 3)
    ]
    
    top = (confident_words_df["top"].min()) - 100 if (confident_words_df["top"].min()) - 100 > 0 else (confident_words_df["top"].min())
    left = confident_words_df["left"].min()
    bot = (confident_words_df["top"] + confident_words_df["height"]).max()
    right = (confident_words_df["left"] + confident_words_df["width"]).max()


    return top, left, bot, right



def reduce_noise(image):
    """
    Applies a binary threshold to reduce noise in the form of text shining
    through from the next page
    Applies opening/median blur to deal with salt and pepper noise
    resulting from shadow at left page edge
    Saves threshed image under the same image name as unthreshed page
    
    Notes:
        - If median fails, use opening = cv2.morphologyEx(thresh,cv2.MORPH_OPEN,kernel)
        - Thresh at 130 because with 127 defend ID in Dom T 256-99 not read correctly

    """
    filename = ''.join(image.split('.jpg')[:-1])
    img = cv2.imread(image)    
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    ret,thresh = cv2.threshold(gray,130,255,cv2.THRESH_BINARY)
    median = cv2.medianBlur(thresh, 3)

    cv2.imwrite(filename + '--clean.jpg', median)



def get_text(filename):
    """ 
    Uses detect text function to read text only from area on page where text
    could be extracted with high accuracy
    """
    img = cv2.imread(filename)
    top, left, bot, right = detect_text(img)
    if top > 0 and left > 0 and bot > 0 and right > 0:
        text = pytesseract.image_to_string(img[top:bot, left:right, :], lang="swe", config = CONFIG_TEXTBODY)
    else:
        text = pytesseract.image_to_string(img, lang="swe", config = CONFIG_TEXTBODY)

    return text


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
    
    return im



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



def txt_box(dewarp_output, kernal_input):
    """
    Split image by Överklagande part, then draw bounding boxes around characters
    and OCR what is found
    """
    
    string_list = []
    img = cv2.imread(dewarp_output)
    height, width, shape = img.shape

    #Split image by Överklagande
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    ocr_data = pytesseract.image_to_data(img_rgb, lang="swe", config='--psm 6')
    ocr_df = pd.read_table(StringIO(ocr_data), quoting=3)
    
    lastpar = ocr_df[
        (ocr_df["text"] == "ÖVERKLAGAR,")
        | (ocr_df["text"] == "ÖVERKLAGAR")
        | (ocr_df["text"] == "ÖVERKLAGANDE,")
        | (ocr_df["text"] == "ÖVERKLAGANDE")
        | (ocr_df["text"] == "Överklagar,")
        | (ocr_df["text"] == "Överklagar")
        | (ocr_df["text"] == "Överklagande,")
        | (ocr_df["text"] == "Överklagande")
        ]

    if not lastpar.empty:
        top = (lastpar["top"].min()) - 100
        left = lastpar["left"].min()
        img = img[top:height, left:width]
    
    #Draw bounding boxes
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



def final_passage(lastpage):
    """
    Drops all works from last page string that come before last paragraph
    Last paragraph is recognized by ÖVERKLAG header
    Returns list, input should be list
    """
    if isinstance(lastpage, str):
        lastpage = lastpage.split(" ") #make sure all of these lists have individual words as their seperate strings
    
    lastpage = [text.replace('\x0c', '') for text in lastpage]
    lastpage = [t for t in lastpage if t]
    lastpage = [t for t in lastpage if t.replace('\n', '').strip()]
    
    for term in ['ÖVERKLAG','Överklag','överklag']:
        if any(term in string for string in lastpage):
            lastpage = list(itertools.dropwhile(lambda x: term not in x, lastpage))
            lastpage = lastpage[1:]
     
    return lastpage



def classify(file):
    res = predict(file)
    if res == 1:
        newname = file.split('.jpg')[0] + '_appendix.jpg'
        os.rename(file, newname)
    


def ocr_img(image):
    try:
        remove_color(image)
        reduce_noise(image)
        filename = ''.join(image.split('.jpg')[:-1])
        filename = filename +'--clean'
        dewarp_main(filename + '.jpg')
    
        name = image.rsplit(".", 1)
        with open(name[0]+".txt", "w") as file:
            file.write("\n__newpage__\n")
            text = get_text(filename + '--straight.png')
            file.write(text)
            file.close()
    except:
        current_path = os.getcwd()
        os.chdir(current_path + '/ocr_errors/')
        img = cv2.imread(image)
        cv2.imwrite(image.replace('--','_') + '_dewarperror.png', img)
        os.chdir(current_path)
        return



def judge_dets(image):
    try:
        name = image.split("--")
        last = cv2.imread(image)
        
        with open(name[0] + "--pg99.txt", "w") as file:
            """
            judge_small = txt_box(image, kernal_sign)
            judge_small = final_passage(judge_small)
            judge_small = ' '.join(judge_small)
            file.write(judge_small)
            """
            judge_large = pytesseract.image_to_string(last, lang=LANG, config = CONFIG_FULL)
            judge_large = final_passage(judge_large)
            judge_large = ' '.join(judge_large)
            file.write(judge_large)
    
        file.close()
    except:
        current_path = os.getcwd()
        os.chdir(current_path + '/ocr_errors/')
        img = cv2.imread(image)
        cv2.imwrite(image.replace('--','_') + '_dewarperror.png', img)
        os.chdir(current_path)
        return



def main():
    path = PATH
    os.chdir(path)

    #Convert each page in a pdf to an image
    lst = glob.glob(path + '*.pdf')
    with Pool(60) as p:
        p.map(pdf_to_jpg, lst)
    
    #Classify each image as appendix or not
    imgs = glob.glob(path + '*.jpg')
    with Pool(60) as p:
        p.map(classify, imgs)
        
    #Save OCR'd text from image to txt file
    imgs = glob.glob(path + '*.jpg')
    imgs = [x for x in imgs if not 'appendix' in x]
    with Pool(60) as p:
        p.map(ocr_img, imgs)
    
    #Extract more detailed text for judges from last page
    pngs = glob.glob(path + '*.png')
    files = imgs + pngs
    lastpg = []
    
    #Paths of last page of each case
    group_dict = defaultdict(list)
    for fn in files:
        key = fn.split("--")[0]
        group_dict[key].append(fn)
    
    for k,v in group_dict.items():
        lastpg.append(v[-1])
    
    #OCR read last page in more detail
    with Pool(60) as p:
        p.map(judge_dets, lastpg)
    
    #Join txt files of the same court document to 1 file
    group_dict = defaultdict(list)
    for fn in glob.glob("*.txt"):
        key = fn.split("--")[0]
        group_dict[key].append(fn)
    
    for name, content in group_dict.items():
        with open(path + name + ".txt", "wb") as outfile:
            for f in content:
                with open(f, "rb") as infile:
                    outfile.write(infile.read())
    
    #Delete jpg, png, txt files created in the intermediary
    
    for fname in os.listdir(path):
        if '--' in fname and not 'appendix' in fname:
            os.remove(os.path.join(path, fname))
    



if __name__ == '__main__':
    
    path = PATH
    files = glob.glob(path + '*.pdf')
    start = time.time()

    main()
    
    done = time.time()
    elapsed = done - start
    print(elapsed)
    
    


