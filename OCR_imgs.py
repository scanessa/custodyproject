# -*- coding: utf-8 -*-
"""
@author: Stella Canessa


This code reads in images in one folder, extracts the text through OCR and 
saves the text from each image as a .txt file. Then it reads in all txt files
and saves the text to an 'all.txt' file with all the text from the images, splits
this large text by page, searches for SLUT in each page (first page), and 
saves the first page + all following pages that don't contain SLUT as a combined
.txt file for this case

HOW TO USE: Set PATH variabel to folder where court doc images are located and run


"""
import os
import time
import pytesseract
import cv2
import pandas as pd
import glob
import re

from fpdf import FPDF
from io import StringIO
from multiprocessing import Pool
from page_dewarp import dewarp_main

start_time = time.time()
pdf_converter = FPDF()

#Define paths
pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"
PATH = "P:/2020/14/Tingsratter/Sodertorns/Domar/all_scans/"

#General settings
LANG = 'swe'
CONFIG_TEXTBODY = '--psm 6 --oem 3' 
CONFIG_FULL = '--psm 11 --oem 3'
CORES = 5
kernal_sign = cv2.getStructuringElement(cv2.MORPH_RECT, (11,11))



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
    filename = ''.join(image.split('.JPG')[:-1])
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



def ocr_img(image):
    """
    

    """
    try:
        #reduce_noise(image)
        filename = ''.join(image.split('.JPG')[:-1])
        #filename = filename +'--clean'
        dewarp_main(filename + '.jpg')
        name = image.rsplit(".", 1)
        with open(name[0]+"--.txt", "w") as file:
            file.write("\n__newpage__\n")
            file.write("\n_f_\n" + filename.split('\\')[-1] + "\n_f_\n")
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



def save_seperate(all_txt):
    path = PATH
    os.chdir(path)
    res = []
    indices = []
    counter = 1
    
    text = all_txt.split("__newpage__")
    firsts = [x for x in text if 'SLUT' in x]
    
    for f in firsts:
        temp = text.index(f)
        indices.append(temp)
    
    indices = indices[0]
    if indices != 0:
        unassigned = ''.join(text[:indices])
        text = text[indices:]
        with open(path + "case_no_start_page.txt", "w") as file:
            file.write(unassigned)
            file.close()

    for elem in text:
        if (
                not any(x in elem for x in ['SLUT','Domslut'])
                ):
            res[-1].append(elem)
        else:
            res.append([elem])
    
    for case in res:
        case = '__newpage__'.join(case)
        filename = re.compile('\n_f_\n.*\n_f_\n').findall(case)[-1]
        filename = filename.replace('\n_f_\n','')
        with open(path + filename + ".txt", "w") as file:
            file.write(case)
            counter += 1
            file.close()


def main():
    path = PATH
    os.chdir(path)
    

    #To do: classify each image as appendix or not

    #Save OCR'd text from image to txt file
    imgs = glob.glob(path + '*.JPG')
    with Pool(CORES) as p:
        p.map(ocr_img, imgs)
        
    #Join txt files of all cases of the same court to 1 file
    with open(path + "all.txt", "wb") as outfile:
        for f in glob.glob("*.txt"):
            with open(f, "rb") as infile:
                outfile.write(infile.read())
                
    #Split all.txt into seperate cases and save as seperate .txt files
    with open(path + "all.txt", "r") as infile:
        all_txt = infile.read()
        infile.close()
        
    save_seperate(all_txt)
    
    #Delete helper files
    for fname in os.listdir(path):
        if '--' in fname:
            os.remove(os.path.join(path, fname))
    


if __name__ == '__main__':
    
    path = PATH
    files = glob.glob(path + '*.JPG')
    print(files)
    
    start = time.time()

    main()
    
    done = time.time()
    elapsed = done - start
    print(elapsed)
    

