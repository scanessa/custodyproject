# -*- coding: utf-8 -*-
"""
Created on Thu Mar 17 09:06:04 2022

@author: ifau-SteCa
"""
import cv2
import numpy as np
import os
import imutils
import pytesseract
from pytesseract import Output

os.chdir("P:/2020/14/Kodning/Scans/all_scans/")
img_path="P:/2020/14/Kodning/Scans/all_scans/test6_outSodertorn.JPG"
kernal = cv2.getStructuringElement(cv2.MORPH_RECT, (50,50))

def crop(img_path):
    """
    Crop awaz page borders and background of image so that text orientation can be extracted
    """
    img = cv2.imread(img_path)
    height, width, shape = img.shape
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255,
    	cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 21, 20)

    cont_max = 0
    dilate = cv2.dilate(thresh,kernal,iterations = 1)
    contours = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[0] if len(contours) == 2 else contours[1]

    for cnt in contours:
        x,y,w,h = cv2.boundingRect(cnt)
        area = w * h
        
        if (
                area > cont_max
                and y+h < height-150
                and x+w < width-150
                and x > 150 and y > 150
                ):
            cont_max = area
            x_max,y_max,w_max,h_max = cv2.boundingRect(cnt)
    
    cv2.rectangle(img, (x_max,y_max),(x_max+w_max,y_max+h_max),(36,255,12),2)
    cv2.imwrite("largestbox.jpg", img)
    
    roi = thresh[y_max:y_max+h_max, x_max:x_max+w_max]
    inverted = cv2.bitwise_not(roi)
    cv2.imwrite("crop.jpg", inverted)
    
    return inverted
    


def rotate(img, angle):
    rows,cols = img.shape
    M = cv2.getRotationMatrix2D((cols/2,rows/2),angle,1)
    dst = cv2.warpAffine(img,M,(cols,rows))

    return dst


def sum_rows(img):
    row_sums = []
    for r in range(img.shape[0]-1):
        row_sum = sum(sum(img[r:r+1,:]))
        row_sums.append(row_sum)
    row_sums = (row_sums/max(row_sums)) * 255

    return row_sums


def find_angle():
    """
    Rotate image 90, 180, 270, 360 degrees and check at which rotation light-dark pixel pattern is 
    closest to a "Zebra stripe" patter, this will be the horizontal rotation
    Returns list of dictionaries with score and corresponding angle
    """
    angle = 0
    score_min = 50000
    scrs = {'Score':[], 'Angle':[]}
    scores_list = []
    
    while angle <= 360:
        print("Angle: ",angle)
        src = 255 - crop(img_path)
        image = rotate(src, angle)    
        h,w = image.shape
        buffer = min(h, w) - int(min(h,w)/1.5)
        img = image.copy()
        roi = img[int(h/2-buffer):int(h/2+buffer), int(w/2-buffer):int(w/2+buffer)]
        _, roi = cv2.threshold(roi, 140, 255, cv2.THRESH_BINARY)
        row_sums = sum_rows(roi)
        score = np.count_nonzero(row_sums)
        if score < score_min:
            score_min = score
            print(score_min)
            scrs['Score'] = (score)
            scrs['Angle'] = (angle)
            scores_list.append(scrs)

        angle += 90
    
    return scores_list

def rotate_img(img_path):
    """
    Get maximum score and corresponding angle, rotate original image by this angle and save under same name
    Get tesseract details of newly saved image, extract orientation,
    if orientation = 180 rotate image again by 180 degrees and save
    """
    scores = find_angle()
    filename = img_path.split("/")[-1]

    final = max(scores, key=lambda x:x['Score'])
    angle_out = final['Angle']
    print(angle_out)
    src_og = cv2.imread(img_path)
    output_image = imutils.rotate(src_og, angle=angle_out)
    cv2.imwrite(filename, output_image)

    dets = pytesseract.image_to_osd("P:/2020/14/Kodning/Scans/all_scans/crop.jpg", output_type=Output.DICT)
    orientation = dets['orientation']
    print("Orientation: ", orientation)
    if orientation == 180:
        rotated = cv2.imread(img_path)
        output_image = imutils.rotate(rotated, angle=180)
        cv2.imwrite(filename, output_image)

rotate_img(img_path)