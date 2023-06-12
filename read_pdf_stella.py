# -*- coding: utf-8 -*-
"""
Created on Fri Jun  2 13:50:00 2023

@author: hoffmann
"""

from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Users\hoffmann\AppData\Local\anaconda3\Library\bin\tesseract.exe'
custom_oem_psm_config = r'--oem 3 --psm 7'
image = Image.open('G:/PraktikantInnen/PRAKTIKANTINNEN/Hoffmann/Read_pdf_Stella/cropped.png')
text = pytesseract.image_to_string(image)
print(text)