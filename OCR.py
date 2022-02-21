import cv2, pytesseract, os, glob, subprocess, time
from pdf2image import convert_from_path

os.chdir('P:/2020/14/Kodning/Scans')
start_time = time.time()

#Define paths
pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"
pdf_dir = 'P:/2020/14/Kodning/Scans'

#General settings
language = 'swe'
kernal = cv2.getStructuringElement(cv2.MORPH_RECT, (50,50))

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
    median = cv2.medianBlur(inverted, 3)
    return median

def get_contour_precedence(contour, cols):
    tolerance_factor = 10
    origin = cv2.boundingRect(contour)
    return ((origin[1] // tolerance_factor) * tolerance_factor) * cols + origin[0]

def bounding_boxes(subprocess_output):
    string_list = []
    img = cv2.imread(subprocess_output)
    height, width, channels = img.shape 
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (7,7), 0)
    thresh = cv2.adaptiveThreshold(blur, 255,cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 21, 20)
    dilate = cv2.dilate(thresh,kernal,iterations = 1)
    cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    cnts = sorted(cnts, key=lambda x:get_contour_precedence(x, img.shape[1]))
    for c in cnts:
        x,y,w,h = cv2.boundingRect(c)
        if 50 < h < 700 and w > 200 and y > 10 and y+h < height-35 or (700 < h < 2500 and w > 1000 and y > 100 and y+h < height-35):
            cv2.rectangle(img, (x,y),(x+w,y+h),(36,255,12),2)
            roi = img[y:y+h, x:x+w]
            cv2.rectangle(img, (x,y),(x+w,y+h),(36,255,12),2)
            img_string = pytesseract.image_to_string(roi, lang=language)
            string_list.append(img_string) 
            
    cv2.imwrite("bbox.jpg", img)

    return string_list

def jpg_to_string(path):
    page_list = []
    for image in path:
        filename = image.split('.')[0]
        cv2.imwrite(image.split('.')[0] + '_thresh.jpg', preprocess(image))
        subprocess.call([
            'python', 
            'P:/2020/14/Kodning/Code/page_dewrap/page_dewarp.py', 
            filename + '_thresh.jpg'
            ])

        page_list.append(bounding_boxes(filename + '_thresh_straight.png'))
        
        """
        for file in [filename + '.jpg', 
                     filename + '_thresh.jpg',
                     filename + '_thresh_straight.jpg']:
            os.remove(file)
        """
        
    return page_list

#Execute

for pdf_file in pdf_files:
    print('Currently reading with OCR: ', pdf_file)
    jpg_paths = pdf_to_jpg(pdf_file)
    full_text = jpg_to_string(jpg_paths)
    print(full_text)
print("\nRuntime: \n" + "--- %s seconds ---" % (time.time() - start_time))