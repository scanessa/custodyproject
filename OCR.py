import cv2, pytesseract, os, glob
from pdf2image import convert_from_path
import numpy as np

os.chdir('P:/2020/14/Kodning/Scans')

#Define paths
pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"
pdf_dir = 'P:/2020/14/Kodning/Scans'

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
def preprocess(img_path):
    image = cv2.imread(img_path)
    gray1 = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_not(gray1)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    return thresh
    

def jpg_to_string(path):
    string_list = []
    for image in path:
        img = cv2.imread(image)
        custom_config = r'--oem 3 --psm 6'
        img_string = pytesseract.image_to_string(img, config=custom_config, lang='swe')
        string_list.append(img_string) 
    return string_list

def display(_original):
    print(_original)
    og = cv2.imread(_original)
    cv2.imwrite('P:/2020/14/Kodning/Scans/original.jpg', og)
    cv2.imwrite('P:/2020/14/Kodning/Scans/new.jpg', preprocess(_original))

#display(r"P:/2020/14/Kodning/Scans/sample1.jpg")

full_text = jpg_to_string(['P:/2020/14/Kodning/Scans/sample1_pg1.jpg'])
#Execute
"""
for pdf_file in pdf_files:
    print('Currently reading with OCR: ', pdf_file)
    jpg_paths = pdf_to_jpg(pdf_file)
    full_text = jpg_to_string(jpg_paths)
"""
print(full_text)
