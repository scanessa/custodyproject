# -*- coding: utf-8 -*-
"""
Created on Wed Feb 16 16:08:06 2022

@author: ifau-SteCa
"""

import cv2,os, subprocess
import numpy as np
os.chdir('P:/2020/14/Kodning/Scans')
kernel3 = np.ones((3,3), np.uint8)

def preprocess(img_path):
    image = cv2.imread(img_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255,
    	cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 21, 20)
    inverted = cv2.bitwise_not(thresh)
    median = cv2.medianBlur(inverted, 3)
    erode = cv2.erode(median, kernel3, iterations=1)
    return erode

kernal = cv2.getStructuringElement(cv2.MORPH_RECT, (35,35))

subprocess.call([
            'python', 
            'P:/2020/14/Kodning/Code/page_dewrap/page_dewarp.py', 
            "P:/2020/14/Kodning/Scans/gavle1_pg1.jpg"
            ])

img = cv2.imread("P:/2020/14/Kodning/Scans/gavle1_pg1_straight.png")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
blur = cv2.GaussianBlur(gray, (7,7), 0)
thresh = cv2.adaptiveThreshold(blur, 255,cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 21, 20)
dilate = cv2.dilate(thresh,kernal,iterations = 1)
cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cnts = cnts[0] if len(cnts) == 2 else cnts[1]
cnts = sorted(cnts, key = lambda x: cv2.boundingRect(x)[0])
for c in cnts:
    x,y,w,h = cv2.boundingRect(c)
    if 50 < h < 400 and w > 150:
        cv2.rectangle(img, (x,y),(x+w,y+h),(36,255,12),2)


cv2.imwrite("gray.jpg", gray)
cv2.imwrite("blur.jpg", blur)
cv2.imwrite("thresh.jpg", thresh)
cv2.imwrite("dilate.jpg", dilate)
cv2.imwrite("bbox.jpg", img)


"""
#CONTOURING
img = cv2.imread("Dom T 212-08_pg2_thresh_straight.png")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
ret, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)
rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 50))
dilation = cv2.dilate(thresh1, rect_kernel, iterations = 1)
contours, hierarchy = cv2.findContours(dilation, cv2.RETR_EXTERNAL,
												cv2.CHAIN_APPROX_NONE)
im2 = img.copy()

i = 0

for cnt in contours:
    x,y,w,h = cv2.boundingRect(cnt)
    cropped = im2[y:y+h, x:x+w]
    
    if 300 < x < 2600:
        rect = cv2.rectangle(im2, (x,y), (x+w,y+h),(0,255,0),2) 
        cv2.imwrite('rect1.jpg',rect)
        
    text = pytesseract.image_to_string(cropped)
    
    print('x y w h', x,y,w,h)
    
    i += 1
    
    if i >= 10000000 :
        break
"""

    