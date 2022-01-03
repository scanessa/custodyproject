import cv2, pytesseract, os
import tempfile
from pdf2image import convert_from_path
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"

#CONVERT PDF TO JPG
pdfs = 'P:/2020/14/Kodning/Test_scanned_docs_phone_app/Scanned_from_courts/pdftoimage/9-01.pdf'
pages = convert_from_path(pdfs, 350)
os.chdir("P:/2020/14/Kodning/Test_scanned_docs_phone_app/Scanned_from_courts/Photos/New_pictures/")

i = 1
for page in pages:
    image_name = "Page_" + str(i) + ".jpg"  
    page.save(image_name, "JPEG")
    i = i+1        
    print(image_name)

#OCR ON THE TRANSFORMED IMAGE WITH TESSERACT
img = cv2.imread("P:/2020/14/Kodning/Test_scanned_docs_phone_app/Scanned_from_courts/Photos/New_pictures/Page_11.jpg")
print(img)

# Adding custom options
custom_config = r'--oem 3 --psm 6'
a = pytesseract.image_to_string(img, config=custom_config)
print(a.split(" "))
