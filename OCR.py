import cv2, pytesseract, os, glob, subprocess
from pdf2image import convert_from_path

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
    thresh = cv2.threshold(gray1, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    return thresh
    
def jpg_to_string(path):
    string_list = []
    for image in path:
        #Apply global thresholding only to scanned docs, take out for photos
        cv2.imwrite(image.split('.')[0] + '_thresh.jpg', preprocess(image))
        
        subprocess.call([
            'python', 
            'P:/2020/14/Kodning/Code/page_dewrap/page_dewarp.py', 
            image.split('.')[0] + '_thresh.jpg'
            ])
        
        img = cv2.imread(image.split('.')[0] + '_thresh_straight.png')
        custom_config = r'--oem 3 --psm 6'
        img_string = pytesseract.image_to_string(img, config=custom_config, lang='swe')
        string_list.append(img_string) 
    return string_list

#display('sample1_pg2.jpg')

#Execute

for pdf_file in pdf_files:
    print('Currently reading with OCR: ', pdf_file)
    jpg_paths = pdf_to_jpg(pdf_file)
    full_text = jpg_to_string(jpg_paths)
    print(full_text)
