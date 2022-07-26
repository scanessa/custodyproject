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
    
    





















"""

OLD SIGNATURE EXTRACTOR


Extract signatures from an image
Original author:
# ----------------------------------------------
# --- Author         : Ahmet Ozlu
# --- Mail           : ahmetozlu93@gmail.com
# --- Date           : 17th September 2018
# ----------------------------------------------

Adapted by: Stella Canessa
Date: 26.07.22

"""
"""
import cv2
import os
import matplotlib.pyplot as plt
from skimage import measure, morphology
from skimage.measure import regionprops
import numpy as np

#CONSTANTS
# the parameters are used to remove small size connected pixels outliar 
constant_parameter_1 = 84
constant_parameter_2 = 350
constant_parameter_3 = 80

# the parameter is used to remove big size connected pixels outliar
constant_parameter_4 = 30

kernal = cv2.getStructuringElement(cv2.MORPH_RECT, (51,51))

def sort_contours(contours):

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


def crop(img, path):
    
    os.chdir(path)
    height, width = img.shape
    
    invert = cv2.bitwise_not(img)
    dilate = cv2.dilate(invert,kernal,iterations = 2)
    
    cv2.imwrite("dilate.jpg", dilate)
    
    contours = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[0] if len(contours) == 2 else contours[1]
    
    for cnt in contours:
        
        x,y,w,h = cv2.boundingRect(cnt)
        cv2.rectangle(img, (x,y),(x+w,y+h),(255, 128, 0),5)
        cv2.putText(img=img, text="BOX", org=(x, y), fontFace=cv2.FONT_HERSHEY_TRIPLEX, fontScale=3, color=(0, 255, 0),thickness=2)
        cv2.imwrite('bbox.jpg', img)
        
        area = w*h/1000
        
        print(area, w, h)
        
        if y+h < height-35 and 100 < area < 550:
            
            cv2.rectangle(img, (x,y),(x+w,y+h),(255, 128, 0),5)
            #cv2.putText(img=img, text=str(counter), org=(x, y), fontFace=cv2.FONT_HERSHEY_TRIPLEX, fontScale=3, color=(0, 255, 0),thickness=2)
            crop = img[y:y+h, x:x+w]
            cv2.imwrite('crop.jpg', crop)
    
    return crop



def extract_signature(path, filename):
    
    os.chdir(path)

    img = cv2.imread(path + filename, 0)
    img = cv2.adaptiveThreshold(img, 255,cv2.ADAPTIVE_THRESH_MEAN_C,
                                   cv2.THRESH_BINARY, 21, 20)

    # connected component analysis by scikit-learn framework
    blobs = img > img.mean()
    blobs_labels = measure.label(blobs, background=1)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    the_biggest_component = 0
    total_area = 0
    counter = 0
    average = 0.0
    
    for region in regionprops(blobs_labels):
        if (region.area > 10):
            total_area = total_area + region.area
            counter = counter + 1

        # take regions with large enough areas
        if (region.area >= 250):
            if (region.area > the_biggest_component):
                the_biggest_component = region.area
    
    average = (total_area/counter)

    # experimental-based ratio calculation, modify it for your cases
    # a4_small_size_outliar_constant is used as a threshold value to remove connected outliar connected pixels
    # are smaller than a4_small_size_outliar_constant for A4 size scanned documents
    a4_small_size_outliar_constant = ((average/constant_parameter_1)*constant_parameter_2)+constant_parameter_3
    
    # experimental-based ratio calculation, modify it for your cases
    # a4_big_size_outliar_constant is used as a threshold value to remove outliar connected pixels
    # are bigger than a4_big_size_outliar_constant for A4 size scanned documents
    a4_big_size_outliar_constant = a4_small_size_outliar_constant*constant_parameter_4
    
    # remove the connected pixels are smaller than a4_small_size_outliar_constant
    pre_version = morphology.remove_small_objects(blobs_labels, a4_small_size_outliar_constant)

    # remove the connected pixels are bigger than threshold a4_big_size_outliar_constant 
    # to get rid of undesired connected pixels such as table headers and etc.
    component_sizes = np.bincount(pre_version.ravel())
    too_small = component_sizes > (a4_big_size_outliar_constant)
    too_small_mask = too_small[pre_version]
    pre_version[too_small_mask] = 0

    # save the the pre-version which is the image is labelled with colors
    # as considering connected components
    plt.imsave(path + 'pre_version.png', pre_version)
    
    # read the pre-version
    img2 = cv2.imread(path + 'pre_version.png', 0)
    
    # ensure binary
    img2 = cv2.threshold(img2, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    
    # Save last page without signature
    diff = cv2.bitwise_xor(img,img2)
    diff = cv2.bitwise_not(diff)
    cv2.imwrite(path + filename.split('.jpg')[0] + '_nosign.jpg', diff)
    
    # Save only cropped signature image
    cropped = crop(img2, path)
    cv2.imwrite(path + filename.split('.jpg')[0] + '_signature.jpg', cropped)

#extract_signature("P:/2020/14/Kodning/Scans/all_scans/", 'Scan 2. May 2022 at 09.09_pg2.jpg')
"""
