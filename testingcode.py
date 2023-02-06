import os
ROOTDIR = "P:/2020/14/Tingsratter/"
OUTPUT_REGISTER = "P:/2020/14/Kodning/Data/case_register_data.csv"
OUTPUT_RULINGS = "P:/2020/14/Kodning/Data/rulings_data.csv"
JUDGE_LIST = "P:/2020/14/Data/Judges/list_of_judges_cleaned.xls"
EXCLUDE = set(['other_half', 'ocr_errors'])
INCLUDE = set(['all_scans','all_cases'])

#Main functions
def paths(ending,incl,excl):
    filecounter = 0
    pdf_files = []
    for subdir, dirs, files in os.walk(ROOTDIR, topdown=True):
        for term in excl:
            if term in dirs:
                dirs.remove(term)
        for file in files: 
            for term in incl:
                if term in subdir and file.endswith(ending):
                    filecounter += 1
                    print(f"Dealing with file {subdir}/{file}")
                    pdf_dir = (os.path.join(subdir, file))
                    pdf_files.append(pdf_dir)
                    
    print("Total files: ", filecounter)     
    
    return pdf_files



scans = paths('.txt',['all_scans'],['ocr_errors','misclassified','only_appendix','appendix_only'])
pdfs = paths('.pdf',['all_cases'],[])

all_files = scans + pdfs

print("All files: ", len(all_files))
