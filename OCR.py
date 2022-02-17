import cv2, pytesseract, os, glob, subprocess, time
from pdf2image import convert_from_path
import numpy as np

os.chdir('P:/2020/14/Kodning/Scans')
start_time = time.time()

#Define paths
pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"
pdf_dir = 'P:/2020/14/Kodning/Scans'

#General settings
custom_config = r'--oem 3 --psm 6'
language = 'swe'
kernel3 = np.ones((3,3), np.uint8)
kernel5 = np.ones((5,5), np.uint8)

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
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255,
    	cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 21, 20)
    inverted = cv2.bitwise_not(thresh)
    median = cv2.medianBlur(inverted, 7)   
    dilate = cv2.dilate(median, kernel3, iterations=1)
    erode = cv2.erode(dilate, kernel5, iterations=1)
    return erode

def tesseract_text(file_thresh_straight, string_list):    
    img = cv2.imread(file_thresh_straight)
    img_string = pytesseract.image_to_string(img, config=custom_config, lang=language)
    string_list.append(img_string) 

def jpg_to_string(path):
    string_list = []
    for image in path:
        filename = image.split('.')[0]
        cv2.imwrite(image.split('.')[0] + '_thresh.jpg', preprocess(image))
        
        subprocess.call([
            'python', 
            'P:/2020/14/Kodning/Code/page_dewrap/page_dewarp.py', 
            filename + '_thresh.jpg'
            ])

        tesseract_text(filename + '_thresh_straight.png', string_list)
        
        for file in [filename + '.jpg', filename + '_thresh.jpg']:
            os.remove(file)

    return string_list

#Execute

for pdf_file in pdf_files:
    print('Currently reading with OCR: ', pdf_file)
    jpg_paths = pdf_to_jpg(pdf_file)
    full_text = jpg_to_string(jpg_paths)
    print(full_text)
print("\nRuntime: \n" + "--- %s seconds ---" % (time.time() - start_time))