"""Extract signatures from an image."""
# ----------------------------------------------
# --- Author         : Ahmet Ozlu
# --- Mail           : ahmetozlu93@gmail.com
# --- Date           : 17th September 2018
# ----------------------------------------------

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


def crop(img, path):
    
    os.chdir(path)
    height, width = img.shape
    
    invert = cv2.bitwise_not(img)
    dilate = cv2.dilate(invert,kernal,iterations = 1)
    contours = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[0] if len(contours) == 2 else contours[1]
    
    for cnt in contours:
        
        x,y,w,h = cv2.boundingRect(cnt)
        cv2.rectangle(img, (x,y),(x+w,y+h),(255, 128, 0),5)
        cv2.imwrite('bbox.jpg', img)
        
        area = w*h/1000
                
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

