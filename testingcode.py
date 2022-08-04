
from multiprocessing import Pool
import cv2
import os
import time
from pdf2image import convert_from_path
import glob
from page_dewarp import dewarp_main
import pytesseract
from io import StringIO
import pandas as pd

path = "P:/2020/14/Kodning/Scans/all_scans/"
save_path = "P:/2020/14/Kodning/Scans/all_scans/exclude/multiprocessing/images_save"
os.makedirs(save_path, exist_ok=True)
pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"
CONFIG_TEXTBODY = '--psm 6 --oem 3' 

def pdf_to_jpg(pdf):

    img_files = []
    appendix_pages = 0
    ocr_error = ''
    i = 1
    appendix_files = False
    pages = convert_from_path(pdf, 300)
    pdf_name = ''.join(pdf.split('.pdf')[:-1])
    
    for page in pages:
        image_name = pdf_name + '_pg' + str(i) + ".jpg"
        page.save(image_name, "JPEG")
        
        img_files.append(image_name)
        
        i = i+1

    return img_files, ocr_error


def reduce_noise(image):
    filename = ''.join(image.split('.jpg')[:-1])
    img = cv2.imread(image)
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    ret,thresh = cv2.threshold(gray,130,255,cv2.THRESH_BINARY)
    median = cv2.medianBlur(thresh, 3)

    cv2.imwrite(filename + '_clean.jpg', median)
    
def detect_text(imread_img):

    img_rgb = cv2.cvtColor(imread_img, cv2.COLOR_BGR2RGB)
    ocr_data = pytesseract.image_to_data(img_rgb, lang="swe", config='--psm 6')
    ocr_df = pd.read_table(StringIO(ocr_data), quoting=3)
        
    confident_words_df = ocr_df[
        (ocr_df["conf"] > 90)
        & (ocr_df["line_num"] > 3)
        & (ocr_df["text"].str.len() - ocr_df["text"].str.count(" ") > 3)
        | (ocr_df["conf"] > 70)
        & (ocr_df["line_num"] <= 3)
        & (ocr_df["text"].str.len() - ocr_df["text"].str.count(" ") > 3)
    ]
    
    top = (confident_words_df["top"].min()) - 100 if (confident_words_df["top"].min()) - 100 > 0 else (confident_words_df["top"].min())
    left = confident_words_df["left"].min()
    bot = (confident_words_df["top"] + confident_words_df["height"]).max()
    right = (confident_words_df["left"] + confident_words_df["width"]).max()


    return top, left, bot, right

def get_text(filename):

    img = cv2.imread(filename)
    top, left, bot, right = detect_text(img)
    text = pytesseract.image_to_string(img[top:bot, left:right, :], lang="swe", config = CONFIG_TEXTBODY)

    return text
    
def main_ocr(image):
    
    os.chdir(path)
    reduce_noise(image)
    filename = ''.join(image.split('.jpg')[:-1])
    filename = filename +'_clean'
    dewarp_main(filename + '.jpg')
    
    """
    name = image.split(".", 2)
    with open("P:/2020/14/Kodning/Scans/all_scans/"+name[0]+".txt", "w") as file:
        file.write("_____"+image+"_______")
        text = get_text(filename + '_straight.png')
        file.write(text)
        file.write("_____"+image+"_______")
        print(image)
        file.close()
    """



def main():
    lst = glob.glob(path + '*.pdf')
    print(lst)
    
    """
    for pdf in lst:
        pdf_to_jpg(pdf)
    imgs = glob.glob(path + '*.jpg')
    for img in imgs:
        main_ocr(img)
    """
    
    # number of processors used will be equal to workers
    with Pool(60) as p:
        p.map(pdf_to_jpg, lst)
    
    
    imgs = glob.glob(path + '*.jpg')
    with Pool(60) as p:
        p.map(main_ocr, imgs)
    

if __name__ == '__main__':
    start = time.time()

    main()
    
    done = time.time()
    elapsed = done - start
    print(elapsed)
