"""
Extracts signature field by finding object with largest hegiht x width
that is not too close to the page boudnaries

Moves processed files to seperate folder

Author: Stella Canessa
Date: 26.07.22
"""

import cv2
import pandas as pd
from io import StringIO
import pytesseract
import glob
import shutil

pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"
kernal_sign = cv2.getStructuringElement(cv2.MORPH_RECT, (35,15))
ROOTPATH = "P:/2020/14/Kodning/Scans/all_scans/100signatures/"

DETAILS = False


def detect_text(path):
    """
    OCRs full page to data and identifies text region through high confidence 
    word matches (90% in general, 70% for first 3 lines of text to capture
    case number and date)
    """
    img = cv2.imread(path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
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

    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        print(ocr_df)

    
    return top, left, bot, right

def cntrs(path):
    
    found = False
    print(path)
    
    fullname = path.split("\\")[1]
    name = fullname.split(".jpg")[0]
    
    imread_img = cv2.imread(path)
    gray = cv2.cvtColor(imread_img,cv2.COLOR_BGR2GRAY)
    ret,thresh = cv2.threshold(gray,127,255,cv2.THRESH_BINARY)
    height, width = thresh.shape
    median = cv2.bitwise_not(thresh)
    dilate = cv2.dilate(median,kernal_sign,iterations = 1)
    
    if DETAILS:
        cv2.imwrite(ROOTPATH+"thresh.jpg", thresh)
        cv2.imwrite(ROOTPATH+"median2.jpg", median)
        cv2.imwrite(ROOTPATH+"dilate.jpg", dilate)
    
    contours = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[0] if len(contours) == 2 else contours[1]
    
    prev_w = 100
    prev_h = 70
    
    for cnt in contours:
        x,y,w,h = cv2.boundingRect(cnt)
        
        if (
                w > prev_w
                and h > prev_h
                and y+h < height-200
                and w+x < width-400
                ):
            
            print(x,y,w,h,height, width)

            roi = imread_img[y:y+h, x:x+w]
            
            prev_w = w if w > prev_w else prev_w
            prev_h = h if h > prev_h else prev_h
            
            found = True
    
    if found:
        cv2.imwrite(ROOTPATH + name + "_sign.jpg", roi)
        shutil.move(ROOTPATH + fullname,ROOTPATH+"extracted/")
    
    

for file in glob.glob(ROOTPATH+"*.jpg"):
    cntrs(file)
    
    



