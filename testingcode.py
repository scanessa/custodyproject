"""
Attempting to clean up the different scripts

"""
import re
import time
import io
import os
import subprocess
import itertools
import pytesseract
import cv2
from pdf2image import convert_from_path
import pandas as pd
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter


#General settings
ROOTDIR = "P:/2020/14/Kodning/Scans"
OUTPUT_REGISTER = "P:/2020/14/Tingsrätter/Case_Sorting_SC/case_register_data.csv"
OUTPUT_RULINGS = "P:/2020/14/Tingsrätter/Case_Sorting_SC/rulings_data.csv"

#OCR
pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"
PAGE_DEWARP_PATH = 'P:/2020/14/Kodning/Code/page_dewrap/page_dewarp.py'
LANGUAGE = 'swe'
CUSTOM_CONFIG = '--psm 4 --oem 3'
kernal = cv2.getStructuringElement(cv2.MORPH_RECT, (50,50))

#Specify folders to search PDFs in
EXCLUDE = set([])
SAVE = 1
COUNT = 1
start_time = time.time()

#Cleaning
OCR_CORR_HEADER = {
    'Kiärande':'Kärande',
    'KIÄRANDE':'KÄRANDE',
    'Mal':'Mål',
    'Mäl':'Mål'
    }

OCR_CORR_TEXT = {
    'Domskill':'Domskäl',
    'DOMSKILL':'DOMSKÄL'
    }

#Define search terms
legalGuardingTerms = ["social", "kommun", "nämnden", "stadsjurist", 'stadsdel', 'familjerätt']
nameCaps = '[A-ZÅÄÖ]{3,}'
svarandeSearch = ' Svarande|SVARANDE|Motpart|MOTPART|SVARANDE och KÄRANDE |MANNEN|Mannen'
idNo ='((\d{6,10}.?.?(\d{4})?)[,]?\s)'
appendix_start = '((?<!se )Bilaga 1|(?<!se )Bilaga A|sida\s+1\s+av)'
searchCaseNo = 'må.\s*(nr)?[.]?\s*t\s*(\d*\s*.?.?\s*\d*)'
capLetters = '[A-ZÅÐÄÖÉÜÆØÞ]'
allLetters = '[A-ZÅÐÄÖÉÜÆØÞ][a-zåäáïüóöéæøßþîčćžđšžůúýëçâêè]'

dateSearch = {
    '1' : 'dom\s+(\d*-\d*-\d*)',
    '2' : 'dom\s+sid\s*1\s*[(][0-9]*[)]\s*(\d*-\d*-\d*)',
    '3' : '(\d{4}-\d{2}-\d{2})'
    }

judgeSearch = {
    '1': '\n\s*\n\s*((' + allLetters + '+\s+){2,4})\n\s*\n', #normal names
    '2': '\n\s*\n\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s+)\n\s*\n', #first name hyphenated
    '3': '\n\s*\n\s*(' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+\s+)\n\s*\n', #last name hypthenated
    '4': '\n\s*\n\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s*-\s*' + allLetters + '+\s+)\n\s*\n', #first and last name hyphenated
    '5': '\n\s*\n\s*(' + allLetters + '+\s' + capLetters + '\s' + allLetters + '+\s+)\n\s*\n', #name with initial as second name
    '6': '\n\s*\n\s*(' + capLetters + '\s' + capLetters + '\s' + allLetters + '+\s+)\n\s*\n', #first and second name as initial
    #if there is a note in the line following the judge's name
    '7': '\n\s*\n\s*((' + allLetters + '+\s+){2,4})\n', #normal names
    '8': '\n\s*\n\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s+)\n', #first name hyphenated
    '9': '\n\s*\n\s*(' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+\s+)\n', #last name hypthenated
    '10': '\n\s*\n\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s*-\s*' + allLetters + '+\s+)\n', #first and last name hyphenated
    '11': '\n\s*\n\s*(' + allLetters + '+\s' + capLetters + 's\s' + allLetters + '+\s+)\n', #name with initial as second name
    '12': '\n\s*\n\s*(' + capLetters + '\s' + capLetters + '\s' + allLetters + '+\s+)\n', #name with initial as second name
    #For documents where judge didnt sign
    '13': '(rådmannen|tingsfiskalen)\s*((' + allLetters + '+\s+){2,4})',
    '14': '(rådmannen|tingsfiskalen)\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s+)', #first name hyphenated
    '15': '(rådmannen|tingsfiskalen)\s*(' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+\s+)', #last name hypthenated
    '16': '(rådmannen|tingsfiskalen)\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s*-\s*' + allLetters + '+\s+)', #first and last name hyphenated
    '17': '(rådmannen|tingsfiskalen)\s*(' + allLetters + '+\s' + capLetters + '\s' + allLetters + '+\s+)', #name with initial as second name
    '18': '(rådmannen|tingsfiskalen)\s*(' + capLetters + '\s' + capLetters + '\s' + allLetters + '+\s+)', #name with initial as second name
    #when judge's name ends with .
    '25': '\n\s*\n\s*((' + allLetters + '+\s+){1,3}' + allLetters + '+).\s*\n\n', #normal names
    '26': '\n\s*\n\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+).\s*\n', #first name hyphenated
    '27': '\n\s*\n\s*(' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+).\s*\n', #last name hypthenated
    '28': '\n\s*\n\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s*-\s*' + allLetters + ').\s*\n', #first and last name hyphenated
    '29': '\n\s*\n\s*(' + allLetters + '+\s' + capLetters + '\s' + allLetters + '+).\s*\n', #name with initial as second name
    '30': '\n\s*\n\s*(' + capLetters + '\s' + capLetters + '\s' + allLetters + '+\s+).\s*\n', #name with initial as second name
    #Only one new line before judge's name
    '31': '\n\s*((' + allLetters + '+\s+){2,4})\n\s*\n', #normal names
    '32': '\n\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s+)\n\s*\n', #first name hyphenated
    '33': '\n\s*(' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+\s+)\n\s*\n', #last name hypthenated
    '34': '\n\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s*-\s*' + allLetters + '+\s+)\n\s*\n', #first and last name hyphenated
    '35': '\n\s*(' + allLetters + '+\s' + capLetters + '\s' + allLetters + '+\s+)\n\s*\n', #name with initial as second name
    '36': '\n\s*(' + capLetters + '\s' + capLetters + '\s' + allLetters + '+\s+)\n\s*\n' #name with initial as second name
    }
judgeSearchNoisy = {
    '1': '\n\s*\n(.*)'
    }

judgeProtokollPreffix = '(Lagmannen|lagmannen|Rådmannen|rådmannen|notarien|Beredningsjuristen|beredningsjuristen|tingsfiskalen|Tingsfiskalen)'
suff1 = '[,|;]?\s*[(]?'
suff2 = '((\w+)?\s*(Protokollförare|protokollförare|ordförande))?'
suff3 = '[)]?\s*([A-ZÅÄÖ]{2,})'
judgeProtokollSuffix = suff1 + suff2+ suff3

judgeSearchProtokoll = {
    '1': judgeProtokollPreffix + '\s*(([A-ZÅÄÖ][a-zåäöé]+\s*){2,4})' + judgeProtokollSuffix, #normal names
    '2': judgeProtokollPreffix + '\s*([A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ][a-zåäöé]+\s+)'+ judgeProtokollSuffix, #first name hyphenated
    '3': judgeProtokollPreffix + '\s*([A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s+)'+ judgeProtokollSuffix, #last name hypthenated
    '4': judgeProtokollPreffix + '\s*([A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s+)'+ judgeProtokollSuffix, #first and last name hyphenated
    '5': judgeProtokollPreffix + '\s*([A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ]\s[A-ZÅÄÖ][a-zåäöé]+\s+)'+ judgeProtokollSuffix, #name with initial as second name
    '6': judgeProtokollPreffix + '\s*(([A-ZÅÄÖ][a-zåäöé]+\s*){1})' + '[,|;]?\s*[(]?((\w+) [p|P]rotokollförare)?[)]?\s*([A-Z])' #only last name 
    }

#Define keys for simple word search
fastInfoKey = ['snabbupplysning', 'upplysning', 'snabbyttrande']
corpTalksKey = ['samarbetssamtal','medlingssamtal',' medling', ' medlare']
mainHearingKey = ['huvudförhandling' , ' rättegång ' , 'sakframställning' , ' förhör ', 'tingsrättens förhandling','huvud- förhandling' ]
lawyerKey = ["ombud:", 'god man:',  'advokat:', "ombud", 'god man',  'advokat']
investigationKey = ['vårdnadsutredning','boendeutredning','umgängesutredning']
allOutcomes = ["vård", "umgänge", "boende"]
umgangeKey = ['umgänge', 'umgås']
separationKey = ['separera', 'relationen tog slut', 'förhållandet tog slut', 'relationen avslutades', 
                 'förhållandet avslutades', 'skildes', 'skiljas', 'skiljer' ]
excludePhysical = ['jämna' , 'växelvis', 'skyddat']
rejectKey = ['avskriv',' ogilla','utan bifall','avslå',' inte ','skrivs', 'kvarstå', ' inga '] 
rejectInvest = ['avskriv',' ogilla','utan bifall','avslå',' inte ',' inga ', ' utöva '] 
rejectKeyOutcome = ['avskriv',' ogilla','utan bifall','avslå',' inte ','skrivs', 'kvarstå', ' inga ', 'utan']  
remindKey = ['bibehålla' ,'påminn' ,'erinra' ,'upply', 'kvarstå', 'fortfarande ']
footer = ['telefax', 'e-post', 'telefon', 'besöksadress', 'postadress', 'expeditionstid', 'dom']
countries = ['saknas', 'u.s.a.', 'u.s.a', 'usa', 'afghanistan', 'albanien', 'algeriet', 'andorra', 'angola', 'antigua och barbuda', 'argentina', 'armenien', 'australien', 'azerbajdzjan', 'bahamas', 'bahrain', 'bangladesh', 'barbados', 'belgien', 'belize', 'benin', 'bhutan', 'bolivia', 'bosnien och hercegovina', 'botswana', 'brasilien', 'brunei', 'bulgarien', 'burkina faso', 'burundi', 'centralafrikanska republiken', 'chile', 'colombia', 'costa rica', 'cypern', 'danmark', 'djibouti', 'dominica', 'dominikanska republiken', 'ecuador', 'egypten', 'ekvatorialguinea', 'elfenbenskusten', 'el salvador', 'eritrea', 'estland', 'etiopien', 'fiji', 'filippinerna', 'finland', 'frankrike', 'förenade arabemiraten', 'gabon', 'gambia', 'georgien', 'ghana', 'grekland', 'grenada', 'guatemala', 'guinea', 'guinea-bissau', 'guyana', 'haiti', 'honduras', 'indien', 'indonesien', 'irak', 'iran', 'irland', 'island', 'israel', 'italien', 'jamaica', 'japan', 'jemen', 'jordanien', 'kambodja', 'kamerun', 'kanada', 'kap verde', 'kazakstan', 'kenya', 'kina', 'kirgizistan', 'kiribati', 'komorerna', 'kongo-brazzaville', 'kongo-kinshasa', 'kroatien', 'kuba', 'kuwait', 'laos', 'lesotho', 'lettland', 'libanon', 'liberia', 'libyen', 'liechtenstein', 'litauen', 'luxemburg', 'madagaskar', 'malawi', 'malaysia', 'maldiverna', 'mali', 'malta', 'marocko', 'marshallöarna', 'mauretanien', 'mauritius', 'mexiko', 'mikronesiska federationen', 'moçambique', 'moldavien', 'monaco', 'montenegro', 'mongoliet', 'myanmar', 'namibia', 'nauru', 'nederländerna', 'nepal', 'nicaragua', 'niger', 'nigeria', 'nordkorea', 'nordmakedonien', 'norge', 'nya zeeland', 'oman', 'pakistan', 'palau', 'panama', 'papua nya guinea', 'paraguay', 'peru', 'polen', 'portugal', 'qatar', 'rumänien', 'rwanda', 'ryssland', 'saint kitts och nevis', 'saint lucia', 'saint vincent och grenadinerna', 'salo-monöarna', 'samoa', 'san marino', 'são tomé och príncipe', 'saudiarabien', 'schweiz', 'senegal', 'seychellerna', 'serbien', 'sierra leone', 'singapore', 'slovakien', 'slovenien', 'somalia', 'spanien', 'sri lanka', 'storbritannien', 'sudan', 'surinam', 'swaziland', 'sydafrika', 'sydkorea', 'sydsudan', 'syrien', 'tadzjikistan', 'tanzania', 'tchad', 'thailand', 'tjeckien', 'togo', 'tonga', 'trinidad och tobago', 'tunisien', 'turkiet', 'turkmenistan', 'tuvalu', 'tyskland', 'uganda', 'ukraina', 'ungern', 'uruguay', 'usa', 'uzbekistan', 'vanuatu', 'vatikanstaten', 'venezuela', 'vietnam', 'vitryssland', 'zambia', 'zimbabwe', 'österrike', 'östtimor']
cities = ['alingsås', 'arboga', 'arvika', 'askersund', 'avesta', 'boden', 'bollnäs', 'borgholm', 'borlänge', 'borås', 'djursholm', 'eksjö', 'enköping', 'eskilstuna', 'eslöv', 'fagersta', 'falkenberg', 'falköping', 'falsterbo', 'falun', 'filipstad', 'flen', 'gothenburg', 'gränna', 'gävle', 'hagfors', 'halmstad', 'haparanda', 'hedemora', 'helsingborg', 'hjo', 'hudiksvall', 'huskvarna', 'härnösand', 'hässleholm', 'höganäs', 'jönköping', 'kalmar', 'karlshamn', 'karlskoga', 'karlskrona', 'karlstad', 'katrineholm', 'kiruna', 'kramfors', 'kristianstad', 'kristinehamn', 'kumla', 'kungsbacka', 'kungälv', 'köping', 'laholm', 'landskrona', 'lidingö', 'lidköping', 'lindesberg', 'linköping', 'ljungby', 'ludvika', 'luleå', 'lund', 'lycksele', 'lysekil', 'malmö', 'mariefred', 'mariestad', 'marstrand', 'mjölby', 'motala', 'nacka', 'nora', 'norrköping', 'norrtälje', 'nybro', 'nyköping', 'nynäshamn', 'nässjö', 'oskarshamn', 'oxelösund', 'piteå', 'ronneby', 'sala', 'sandviken', 'sigtuna', 'simrishamn', 'skanör', 'skanör med falsterbo', 'skara', 'skellefteå', 'skänninge', 'skövde', 'sollefteå', 'solna', 'stockholm', 'strängnäs', 'strömstad', 'sundbyberg', 'sundsvall', 'säffle', 'säter', 'sävsjö', 'söderhamn', 'söderköping', 'södertälje', 'sölvesborg', 'tidaholm', 'torshälla', 'tranås', 'trelleborg', 'trollhättan', 'trosa', 'uddevalla', 'ulricehamn', 'umeå', 'uppsala', 'vadstena', 'varberg', 'vaxholm', 'vetlanda', 'vimmerby', 'visby', 'vänersborg', 'värnamo', 'västervik', 'västerås', 'växjö', 'ystad', 'åmål', 'ängelholm', 'örebro', 'öregrund', 'örnsköldsvik', 'östersund', 'östhammar']


def paths(include):
    pdf_files = []
    for subdir, dirs, files in os.walk(ROOTDIR, topdown=True):
        for term in EXCLUDE:
            if term in dirs:
                dirs.remove(term)
        for file in files: 
            if include in subdir and file.endswith('.pdf'):
                print(f"Dealing with file {subdir}/{file}\n")
                pdf_dir = (os.path.join(subdir, file))
                pdf_files.append(pdf_dir)
                continue
    return pdf_files



def read_file(file):
    pages_text_formatted = []
    page_count= 0
    
    def filereader_params():
        rsrcmgr = PDFResourceManager()
        retstr = io.StringIO()
        laparams = LAParams(line_margin=3)
        device = TextConverter(rsrcmgr, retstr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        return retstr,interpreter

    def appendix_pages(no_of_firstpage):      
        appendix_pageno = appendix[-1]
        fulltext_form = pages_text_formatted[no_of_firstpage:(appendix_pageno)]
        return appendix_pageno, fulltext_form
    
    def text_parts(no_of_firstpage):
        firstpage_form = pages_text_formatted[no_of_firstpage]
        fulltext_form = pages_text_formatted[no_of_firstpage:]
        return fulltext_form, firstpage_form
        
    retstr, interpreter = filereader_params()
    
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,caching=True,check_extractable=True):
            read_position = retstr.tell()
            interpreter.process_page(page)
            retstr.seek(read_position, 0)
            page_text = retstr.read()
            pages_text_formatted.append(page_text)
            page_count += 1
    
    firstpage_form = pages_text_formatted[0]
    appendix = [k for k, item in enumerate(pages_text_formatted) if re.search(appendix_start, item)]
    appendix_pageno = len(pages_text_formatted)
    lastpage_form = pages_text_formatted[appendix_pageno-1]
    
    if "Rättelse" in firstpage_form:
        correction = 1
        firstpage_form = ''.join(pages_text_formatted[1])
        fulltext_form, firstpage_form = text_parts(1)
        if appendix:
            appendix_pageno, fulltext_form= appendix_pages(1)
    else:
        correction = 0
        fulltext_form, firstpage_form = text_parts(0)
        if appendix:
            appendix_pageno, fulltext_form = appendix_pages(0)    
    return correction, appendix_pageno, fulltext_form, firstpage_form, lastpage_form



def read_ocr(file):
    
    def pdf_to_jpg(pdf):
        """ Convert PDF to into seperate JPG files."""
    
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
    
    def preprocess(img_path):
        """ Preproccess image for page_warp.py straightening."""
    
        image = cv2.imread(img_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        thresh = cv2.adaptiveThreshold(blurred, 255,
        	cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 21, 20)
        inverted = cv2.bitwise_not(thresh)
        median = cv2.medianBlur(inverted, 3)
        # erode = cv2.erode(median, np.ones((3,3), np.uint8), iterations=1) including erode
        # gives an error in the page dewarp script for 210929_114535
        return median
    
    def get_contour_precedence(contour, cols):
        tolerance_factor = 10
        origin = cv2.boundingRect(contour)
        return ((origin[1] // tolerance_factor) * tolerance_factor) * cols + origin[0]
    
    def bounding_boxes(subprocess_output):
        """Draw contours around text boxes and OCR text."""
    
        string_list = []
        img = cv2.imread(subprocess_output)
        height, width, shape = img.shape
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (7,7), 0)
        thresh = cv2.adaptiveThreshold(blur, 255,cv2.ADAPTIVE_THRESH_MEAN_C,
                                       cv2.THRESH_BINARY_INV, 21, 20)
        dilate = cv2.dilate(thresh,kernal,iterations = 1)
        contours = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = contours[0] if len(contours) == 2 else contours[1]
        contours = sorted(contours, key=lambda x:get_contour_precedence(x, img.shape[1]))
    
        for cnt in contours:
            x,y,w,h = cv2.boundingRect(cnt)
            if 50 < h < 700 and w > 200 and y > 10 and y+h < height-35 or (700 < h < 2500 and w > 1000 and y > 100 and y+h < height-35):
                cv2.rectangle(img, (x,y),(x+w,y+h),(36,255,12),2)
                roi = img[y:y+h, x:x+w]
                cv2.rectangle(img, (x,y),(x+w,y+h),(36,255,12),2)
                img_string = pytesseract.image_to_string(roi, lang=LANGUAGE, config = CUSTOM_CONFIG)
                string_list.append(img_string)
        return string_list
    
    def main(path):
        """Main function gets OCR'ed text from bounding boxes and saves to strings."""
    
        full_text = []
        header = []
        for image in path:
            filename = image.split('.')[0]
            cv2.imwrite(image.split('.')[0] + '_thresh.jpg', preprocess(image))
    
            subprocess.call([
                'python',
                'P:/2020/14/Kodning/Code/page_dewrap/page_dewarp.py',
                filename + '_thresh.jpg'
                ])
    
            text = bounding_boxes(filename + '_thresh_straight.png')
            full_text.append(text)
            header.append(text[:4])
    
            for file in [filename + '.jpg',
                         filename + '_thresh.jpg',
                         filename + '_thresh_straight.png']:
                os.remove(file)
        firstpage_form = ''.join(full_text[0])
        judge_string = ''.join(full_text[-1][-2:]) if len(full_text[-1]) >= 2 else full_text[-1][-1]
        lastpage_form = ''.join(full_text[-1])
        fulltext_form = ''.join(list(itertools.chain.from_iterable(full_text)))
        header = ''.join(list(itertools.chain.from_iterable(header)))
        return firstpage_form, lastpage_form, fulltext_form, judge_string, header
    
    #Execute
    jpg_paths = pdf_to_jpg(file)
    firstpage_form, lastpage_form, fulltext_form, judge_string, header = main(jpg_paths)
    return firstpage_form, lastpage_form, fulltext_form, judge_string, header



def clean_ocr(header, firstpage_form, fulltext_form):
    for old, new in OCR_CORR_HEADER.items():
        header = header.replace(old, new)
        firstpage_form = firstpage_form.replace(old, new)
    for old, new in OCR_CORR_TEXT.items():
        firstpage_form = firstpage_form.replace(old, new)
        fulltext_form = fulltext_form.replace(old, new)
    return header, firstpage_form, fulltext_form



def format_text(unformatted):
    og = ' '.join((''.join(unformatted)).split())
    lower = og.lower()
    return og, lower



def get_header(firstpage_form):
    try:
        header1 = (re.split('DOMSLUT', firstpage_form))[0]
        for term in ['PARTER','Parter']:
            header2 = header1.split(term)
            if len(header2) != 1:
                break
        header = header2[1]
    except IndexError:                
        try:
            header = re.split('Mål ', re.split('_{10,40}', firstpage_form)[0])[1] 
        except IndexError:
            try:
                header = ''.join(firstpage_form.split('')[0:20])
            except IndexError:
                header = ''.join(firstpage_form)
    try:
        topwords = ' '.join(firstpage_form.split()[0:20].lower())
    except IndexError:
        topwords = ''.join(firstpage_form.lower())
    return header, topwords



def get_lastpage(fulltext_form, lastpage_form):
    for page in fulltext_form:
        for term in ['\nÖVERKLAG','\nÖverklag','\nHUR MAN ÖVERKLAG',
                     '\nHur man överklag','\nHur Man Överklag',
                     'Anvisning för överklagande']:
            if term in page:
                lastpage_sorted = page
                break
            else: 
                lastpage_sorted = '.'.join(lastpage_form.split("."))
        else:
            continue
        break
    return lastpage_sorted



def get_plaint_defend(header):
    try:
        defend_og = re.split('Svarande|SVARANDE', header)[1] 
        plaint_og = re.split('Kärande|KÄRANDE', (re.split('Svarande|SVARANDE', header)[0]))[1]
        if defend_og == "":
            defend_og = re.split('Svarande|SVARANDE', header)[2] 
        elif len(plaint_og.split()) < 4:
            defend_og = re.split("(?i)SVARANDE och KÄRANDE|SVARANDE OCH GENKÄRANDE ", header)[1]
            plaint_og = re.split('(?i)KÄRANDE och SVARANDE|KÄRANDE OCH GENSVARANDE', 
                                       (re.split("SVARANDE och KÄRANDE|SVARANDE OCH GENKÄRANDE ", header)[0]))[1]
    except IndexError:
        try:
            defend_og = re.split(svarandeSearch, header)[1]
            plaint_og = re.split('Kärande|KÄRANDE|Hustrun|HUSTRUN', (re.split(svarandeSearch, header)[0]))[1]
            if defend_og == "":
                defend_og = re.split(svarandeSearch, header)[2]
        except IndexError:
            try:
                first = header.split('1.')[1]
                defend_og = first.split('2.')[1]
                plaint_og = first.split('2.')[0]
            except IndexError:
                defend_og = plaint_og = 'not found, not found'
    defend = defend_og.lower()
    plaint = plaint_og.lower()
    return defend, defend_og, plaint, plaint_og



#Execute        
readable_files = paths('all_cases')
scanned_files = paths('all_scans')

for doc in readable_files:
    correction, appendix_pageno, fulltext_form, firstpage_form, lastpage_unsorted = read_file(doc)
    COUNT += 1
    
for doc in scanned_files:
    print(doc)
    firstpage_form, lastpage_form, fulltext_form, judge_string, header = read_ocr(doc)
    header, firstpage_form, fulltext_form = clean_ocr(header, firstpage_form, fulltext_form)
    defend, defend_og, plaint, plaint_og = get_plaint_defend(header)
    print(defend.split('.'))

df = pd.read_csv(r'P:/2020/14/Tingsrätter/Case_Sorting_SC/rulings_data.csv')
print(df)




         