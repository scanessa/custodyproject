
"""

This code goes through all the PDFs in one folder and sorts them into 4 categories: 
    
1217 A - 膋tenskapsskillnad\domar; divorce/custody battles (ideal case)
1217 B - 膋tenskapsskillnad\domar utan v鋜dnadstvist; divorce with no custody battles
1216 A - V錼dnad\domar; custody battles of non-divorcing parents
1216 B - V錼dnad\domar d鋜 socialf鋜valtning 鋜 k鋜ande eller svarande; legal guardian cases


"""

#Set Up
import glob 
import shutil 
import re
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter
import io

#Define Paths
#Where to find PDFs that code should loop through
pdf_dir = "P:/2020/14/Tingsr鋞ter/种_Case_Sorting_SC/Domar" 

#Different output folders 
path_1217A = "P:/2020/14/Tingsr鋞ter/种_Case_Sorting_SC/Domar/1217 膋tenskapsskillnad/Domar"
path_1217B = "P:/2020/14/Tingsr鋞ter/种_Case_Sorting_SC/Domar/1217 膋tenskapsskillnad/Domar utan v錼dnadstvist"
path_1216A = "P:/2020/14/Tingsr鋞ter/种_Case_Sorting_SC/Domar/1216 V錼dnad/Domar"
path_1216B = "P:/2020/14/Tingsr鋞ter/种_Case_Sorting_SC/Domar/1216 V錼dnad/Domar d鋜 socialtj鋘st 鋜 k鋜ande eller svarande"
path_unassigned = "P:/2020/14/Tingsr鋞ter/种_Case_Sorting_SC/Domar/Unassigned"
path_other = "P:/2020/14/Tingsr鋞ter/种_Case_Sorting_SC/Domar/Other"

#Automatically read in all pdfs in folder
pdf_files = glob.glob("%s/*.pdf" % pdf_dir)

print(pdf_files)

#Loop over files and extract data
for file in pdf_files:
    
    #Read in text from each PDF    
    resource_manager = PDFResourceManager()
    file_handle = io.StringIO()
    converter = TextConverter(resource_manager, file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)

    with open(file, 'rb') as fh:

        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)

        text = file_handle.getvalue()

    # close open handles
    converter.close()
    file_handle.close()

    #Convert full text to clean string
    fullText = ''.join(text)
    fullText = ' '.join(fullText.split())    
    fullTextOG = fullText
    fullText = fullText.lower()  
        
    #Other docs
    otherDocs1 = "slutligt\s+beslut|tingsr鋞t.?(\w+ ){0,3}protokoll"
    otherDocs2 = re.compile(otherDocs1)
    otherDocs = otherDocs2.search(fullText)
    
    if otherDocs is not None:
        shutil.move(file, path_other)
        print("0")
        continue
    
    #Split text into different parts
    try:
        splitText = re.split('domslut ', fullText)
        rulingString = splitText[1]
    except IndexError:
        try:
            splitText = re.split("_{10,30}", fullText)
            rulingString = splitText[1]
        except IndexError:
            shutil.move(file, path_unassigned)
            print("15")
            continue
        
    print("Currently reading:")
    print(file)
    #print(fullText)
    
    firstString = splitText[0]
    #Full text without appendix
    fullText = re.split('sida\s+1\s+av', fullText)[0]
    rulingOnly = re.split('yrkanden', rulingString)[0]
    split1 = re.split('svarande|motpart', firstString)[0]
    
    parentsString = "d?e? 鋜 (\w+ ){1,4}f鰎鋖drar"
    parentsSearch = re.compile(parentsString)
    parentsSearchRes = parentsSearch.search(fullText)
    
    usedToBeMarried = 'varit gifta'
    usedToBeMarriedA = re.compile(usedToBeMarried)
    usedToBeMarriedB = usedToBeMarriedA.search(fullText)               

    ## Analytics for categoriying files   
    #Check if plaintiff or defendant lack personal ID (legal guardian case indicator)
    searchPlaintNo = 'k鋜ande.*?[,]\s+\d*.?.?\d{4}'
    searchPlaintRes = re.compile(searchPlaintNo)
    plaintNo = searchPlaintRes.search(firstString)
    searchDefNo = '(svarande|motpart).*?[,]\s+\d*.?.?\d{4}'
    searchDefRes = re.compile(searchDefNo)
    defNo = searchDefRes.search(firstString)
    
    svarandeString = re.split('(svarande|motpart)', firstString)[1]          
    split1 = re.split('(svarande|motpart)', firstString)[0]              
    k鋜andeString = re.split('k鋜ande', split1)[1] 
    
    ## Assign cases to 4 folders according to search terms; program loops thorugh text and at first True if statement moves file and doesn't execute other elifs, if statements are hierarchical 
    
    # 1216 B: legal guardian cases
    if 's鋜skilt f鰎ordnad v錼dnadshavare' in fullText:
        shutil.move(file, path_1216B)
        print("1")
        continue
    elif "social" in svarandeString or "social" in k鋜andeString or "kommun" in svarandeString or "kommun" in k鋜andeString or "n鋗nden" in svarandeString or "n鋗nden" in k鋜andeString or "stadsjurist" in svarandeString or "stadsjurist" in k鋜andeString:             
        shutil.move(file, path_1216B)
        print("2")
        continue
    elif "overflyttas" in fullText:
        shutil.move(file, path_1216B)
        print("3")
        continue
    elif "ensamkommande flyktingbarn" in fullText:
        shutil.move(file, path_1216B)
        print("4")
        continue
    #elif parentsSearchRes is not None:
     #   shutil.move(file, path_1216B)
      #  print("5")
       # continue
        
    #1217 B: divorce without custody battle
    elif 'de har inga gemensamma barn' in fullText:
        shutil.move(file, path_1217B)
        print("6")
        continue
    
    #1217 A: divorce with custody
    elif "deldom" in firstString:
        shutil.move(file, path_1217A)
        print("7")  
    elif '鋕tenskapsskillnad' in rulingOnly:
        if "v錼dn" in rulingOnly:
            custodySentence = [sentence + "." for sentence in rulingOnly.split(".") if "v錼dn" in sentence]
            custodyString = "".join(custodySentence)
            print("8")
            if "p錷inner" in custodyString:
                shutil.move(file, path_1217B)
                print("9")
                continue
            else:
                #1217 A: divorce and custody in same case/ruling
                shutil.move(file, path_1217A)
                print("10")
                continue
        else:
            shutil.move(file, path_1217B)
            print("11")
            continue
    
    #1216 A: custody without divorce
    elif 'v錼dn' in rulingOnly:
        shutil.move(file, path_1216A)
        print("12")
        continue
    elif usedToBeMarriedB is not None:                                 
        shutil.move(file, path_1216A)
        print("13")
        continue
    elif "umg鋘ge" or "umg錽" in rulingOnly:
        #Physical custody cases
        shutil.move(file, path_1216A)
        print("13a")
        continue
            
    #Unclear cases
    else:
        shutil.move(file, path_unassigned)
        print("14")
        continue

print("Done")        
      

    


