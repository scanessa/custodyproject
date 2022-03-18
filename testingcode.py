# -*- coding: utf-8 -*-
"""
Created on Thu Mar 17 09:06:04 2022

@author: ifau-SteCa
"""
import cv2
import numpy as np
import os
import imutils 

os.chdir("P:/2020/14/Kodning/Scans/all_scans/")
img_path="P:/2020/14/Kodning/Scans/all_scans/test1_out.JPG"
kernal = cv2.getStructuringElement(cv2.MORPH_RECT, (50,50))

filename = img_path.split("/")[-1]
print(filename)

def crop(img_path):
    
    image = cv2.imread(img_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
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
        
        if area > cont_max:
            cont_max = area
            x_max,y_max,w_max,h_max = cv2.boundingRect(cnt)

    roi = thresh[y_max+800:y_max+h_max-200, x_max+200:x_max+w_max-200]
    inverted = cv2.bitwise_not(roi)
    
    return inverted
    
cropped = crop(img_path)

src = 255 - cropped
src_og = cv2.imread(img_path)
scores = []

def rotate(img, angle):
    rows,cols = img.shape
    M = cv2.getRotationMatrix2D((cols/2,rows/2),angle,1)
    dst = cv2.warpAffine(img,M,(cols,rows))
    return dst


def sum_rows(img):
    # Create a list to store the row sums
    row_sums = []
    # Iterate through the rows
    for r in range(img.shape[0]-1):
        # Sum the row
        row_sum = sum(sum(img[r:r+1,:]))
        # Add the sum to the list
        row_sums.append(row_sum)
    # Normalize range to (0,255)
    row_sums = (row_sums/max(row_sums)) * 255
    # Return
    return row_sums

# Rotate the image around in a circle

scrs = {'Score':[], 'Angle':[], 'ROI':[]}
scores_list = []
angle = 0
score_min = 5000

while angle <= 360:
    print("Angle: ",angle)
    # Rotate the source image
    image = rotate(src, angle)    
    # Crop the center 1/3rd of the image (roi is filled with text)
    h,w = image.shape
    buffer = min(h, w) - int(min(h,w)/1.5)
    img = image.copy()
    roi = img[int(h/2-buffer):int(h/2+buffer), int(w/2-buffer):int(w/2+buffer)]
    # Create background to draw transform on
    bg = np.zeros((buffer*2, buffer*2), np.uint8)
    # Threshold image
    _, roi = cv2.threshold(roi, 140, 255, cv2.THRESH_BINARY)
    # Compute the sums of the rows
    row_sums = sum_rows(roi)
    # Low score --> Zebra stripes
    score = np.count_nonzero(row_sums)
    if score < score_min:
        score_min = score
        scrs['Score'] = (score)
        scrs['ROI'] = (image)
        scrs['Angle'] = (angle)
        scores_list.append(scrs)
        print(score)
    
    if sum(row_sums) < 100000: scores.append(angle)
    # Increment angle and try again
    angle += 90
    
final = max(scores_list, key=lambda x:x['Score'])
image_out = final['ROI']
angle_out = final['Angle']
print(angle_out)
output_image = imutils.rotate(src_og, angle=angle_out)

cv2.imwrite(filename, output_image)

