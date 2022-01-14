import cv2, pytesseract, os, glob
import numpy as np
from pdf2image import convert_from_path
from matplotlib import pyplot as plt
from PIL import Image                                                                                


#Define paths
pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"
pdf_dir = 'P:/2020/14/Kodning/Test_scanned_docs_phone_app/Scanned_from_courts/Photos/New_pictures/'

#Read in pdfs
pdf_files = glob.glob("%s/*.pdf" % pdf_dir)

#Convert pdf to jpg
def pdf_to_jpg(pdf):
    img_files = []
    pages = convert_from_path(pdf, 350)
    i = 1
    pdf_name = pdf.split('.')[0]
    for page in pages:
        image_name = pdf_name + '_pg' + str(i) + ".jpg"  
        page.save(image_name, "JPEG")
        i = i+1    
        img_files.append(image_name)
    return img_files

#OCR
def jpg_to_string(path):
    string_list = []
    for image in path:
        img = cv2.imread(image)
        
        """
        #Image preprocessing
        kernel = np.ones((5,5),np.uint8)
        inverted = cv2.bitwise_not(img)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresh, im_bw = cv2.threshold(gray,127,255,cv2.THRESH_BINARY)
        erosion = cv2.erode(inverted,kernel,iterations = 1)
        
        #Preview image
        cv2.imwrite('processed_img.jpg', im_bw)
        img_prev = Image.open('processed_img.jpg')
        img_prev.show() 
        """
        custom_config = r'--oem 3 --psm 6'
        img_string = pytesseract.image_to_string(img, config=custom_config, lang='swe')
        string_list.append(img_string) 
    return string_list

#Execute
for pdf_file in pdf_files:
    jpg_paths = pdf_to_jpg(pdf_file)
    full_text = jpg_to_string(jpg_paths)
    print(full_text)
