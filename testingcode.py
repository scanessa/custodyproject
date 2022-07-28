from PIL import Image
import cv2
import glob


ROOT = "P:/2020/14/Kodning/Scans/all_scans/100signatures/test/others/"
combined = []
files = glob.glob(ROOT + "*_sign.jpg")
tests = glob.glob(ROOT + "*_test.jpg")
count = 0


import os
import image_similarity_measures
from sys import argv
from image_similarity_measures.quality_metrics import rmse, ssim, sre


test_img = cv2.imread("P:/2020/14/Kodning/Scans/all_scans/100signatures/test/2062-07_pg1_test.jpg")

ssim_measures = {}
rmse_measures = {}
sre_measures = {}

scale_percent = 100 # percent of original img size
width = int(test_img.shape[1] * scale_percent / 100)
height = int(test_img.shape[0] * scale_percent / 100)
dim = (width, height)
   
for img_path in files:
    data_img = cv2.imread(img_path)
    resized_img = cv2.resize(data_img, dim, interpolation = cv2.INTER_AREA) 
    ssim_measures[img_path]= ssim(test_img, resized_img) 
    rmse_measures[img_path]= rmse(test_img, resized_img) 
    sre_measures[img_path]= sre(test_img, resized_img)

def calc_closest_val(dict, checkMax):
    result = {}
    if (checkMax):
    	closest = max(dict.values())
    else:
    	closest = min(dict.values())
    		
    for key, value in dict.items():
    	print("The difference between ", key ," and the original image is : \n", value)
    	if (value == closest):
    	    result[key] = closest
    	    
    print("The closest value: ", closest)	    
    print("######################################################################")
    return result
    
ssim = calc_closest_val(ssim_measures, True)
rmse = calc_closest_val(rmse_measures, False)
sre = calc_closest_val(sre_measures, True)

print("The most similar according to SSIM: " , ssim)
print("The most similar according to RMSE: " , rmse)
print("The most similar according to SRE: " , sre)



"""
# test image
for test in tests:
    print(test)
    image = cv2.imread(test)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    test_hist = cv2.calcHist([gray_image], [0],
    						None, [256], [0, 256])
    
    # Test img
    image = cv2.imread(test)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    test_hist = cv2.calcHist([gray_image], [0],None, [256], [0, 256])

# Imgs to compare against test
for file in files:
    
    print(count)
    count += 1
    
    i = 0
    c = 0
    
    image = cv2.imread(file)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    img_hist = cv2.calcHist([gray_image], [0],None, [256], [0, 256])
    
    while i<len(test_hist) and i<len(img_hist):
    	c+=(test_hist[i]-img_hist[i])**2
    	i+= 1

    c = c**(1 / 2)
    combined.append([c, file])

matches = sorted(combined, key=lambda x: x[0], reverse=False)

print(min(matches))
"""

