# -*- coding: utf-8 -*-
"""
Created on Wed Feb 16 16:08:06 2022

@author: ifau-SteCa
"""

import cv2, os, numpy as np
import pytesseract

pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"
os.chdir('P:/2020/14/Kodning/Scans')

img = cv2.imread('Dom T 212-08_pg1_thresh.jpg')
kernel = np.ones((5,5), np.uint8)
img_dilation = cv2.dilate(img, kernel, iterations=1)
img_erosion = cv2.erode(img_dilation, kernel, iterations=1)
 
cv2.imwrite('img.jpg', img_erosion) # Display img with median filter

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

    