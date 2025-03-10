# -*- coding: utf-8 -*-
"""
Created on Wed Feb  2 14:49:04 2022

@author: ifau-SteCa
"""
import shutil
import pathlib
import os.path
import re
import glob
import random
import pandas as pd
from pdf2image import convert_from_path
from PyPDF2 import PdfFileReader, PdfFileWriter
from fpdf import FPDF
from PIL import Image

filepaths_doc = 'P:/2020/14/Kodning/Clean_csvs_move_files/filepaths.txt' 
includes = 'all_scans'
ROOTDIR = 'P:/2020/14/Tingsratter/Ystads/'
DESTINATION = "P:/2020/14/Kodning/Test-round-5-Anna/all_scans/fifth100"

error_paths = [] 

def searchKey(string, part):
    finder = re.compile(string)
    match = finder.search(part)
    return match

def read_filepaths(doc):
    with open(doc,'r') as f:
        paths = f.read().splitlines() 
    return paths

def move_files(paths, pdf_dir):
    errors = 0
    for file in paths:
        p = pathlib.PureWindowsPath(file)
        p = str(p.as_posix())
        print(p)
        try:
            shutil.move(file,pdf_dir)
        except:
            errors += 1
    
    print('%d files threw an error: ' %(errors))
    return errors

def copy_files(paths, pdf_dir):
    errors = 0
    for file in paths:
        p = pathlib.PureWindowsPath(file)
        p = str(p.as_posix())
        try:
            shutil.copy(file,pdf_dir)
            print("Copied to: ", pdf_dir)
        except Exception as e:
            errors += 1
            print("Error: ",p,e)
    
    return errors

def get_paths(in_path):
    """
    Generate list of file paths from csv file that contains file paths as a single column labeled "file_path"
    ending = which ending (document type) the file that should be copied has: will be either .pdf, or .JPG, input as string

    """
    data = pd.read_csv(in_path)
    paths = data['file_path'].tolist()
    
    return list(paths)

def true_file(files):
    for fname in files:
        if not os.path.isfile(fname):
            print('N: ', fname)
            
def file_counter(path, searchkey):
    fileCount = len(glob.glob1(path,searchkey))   
    return fileCount

def convert_to_img(path, no_of_pages):
    """
    Convert PDF to into seperate JPG files
    Input:
    - path of target FOLDER
    - no_of_pages = int of number of desired pages desired as images,
      pages = pages[-(no_of_pages):] outputs last pages, change to pages = pages[:no_of_pages] for
      first pages
    
    """

    for file in glob.glob(path + '*.pdf'):
        img_files = []
        pages = convert_from_path(file, 300)
        
        if len(pages) > no_of_pages:
            pages = pages[-(no_of_pages):]
        i = 1
        pdf_name = ''.join(file.split('.pdf')[:-1])
        for page in pages:
            image_name = pdf_name + '_pg' + str(i) + ".jpg"
            page.save(image_name, "JPEG")
            print(image_name)
            i = i+1
            img_files.append(image_name)
        #os.remove(file)
         
def newname(rootdir):
    """
    Rename scanned files bc () throw an error with OCR
    Rename only files that are not in the new name pattern: COURT0, COURT1, ...
    Remove comment for second court definition if court is not folder name
    """
    for subdir, dirs, files in os.walk(rootdir, topdown=True):
        court = subdir.split('/')[4]
        court = 'Sodertorns'
        existing = file_counter(subdir, court + '*')
        for file in files:
            counter = str(existing)
            if includes in subdir and file.endswith('.JPG') and not searchKey(court+'\d',file):
                file_new = court + counter + '.JPG'
                print('OLD: ', os.path.join(subdir, file))
                print('NEW: ', os.path.join(subdir, file_new))
                #os.rename(os.path.join(subdir, file), os.path.join(subdir, file_new))
                existing += 1
                
def changename(rootdir):
    """
    Remove () from filename
    """
    for subdir, dirs, files in os.walk(rootdir, topdown=True):
        for file in files:
            if includes in subdir:
                file_new = file.replace("(","_").replace(")","").replace(" ","_").replace("ä","a").replace("Ä","A").replace("ö","o").replace("Ö","O").replace("ü","u").replace("Ü","U").replace("Å","A").replace("ä","a").replace("å","a")
                print('OLD: ', os.path.join(subdir, file))
                print('NEW: ', os.path.join(subdir, file_new))
                os.rename(os.path.join(subdir, file), os.path.join(subdir, file_new))



def changename_one_folder(rootdir):
    """
    Remove () from filename
    """
    for file in glob.glob(rootdir + "*.pdf"):
        
        file_new = file.replace("_rotated","")
        #file_new = file.replace("(","_").replace(")","").replace(" ","_").replace("ä","a").replace("Ä","A").replace("ö","o").replace("Ö","O").replace("ü","u").replace("Ü","U").replace("Å","A").replace("ä","a").replace("å","a")
        print('OLD: ', file)
        print('NEW: ', file_new)
        os.rename(file, file_new)



def randomsample(rootdir, destination):
    for rootdir, dirs, files in os.walk(rootdir):
        for subdir in dirs:
            dirpath = os.path.join(rootdir, subdir)
            
            if (
                    not "1. Gemensamma dokument" in dirpath
                    and "all_scans" in dirpath
                    and not "ocr_errors" in dirpath
                    
                ):
                
                paths = glob.glob(dirpath + "/*.pdf")
                print(dirpath)
                allfiles = [x for x in paths if not any(term in x.lower() for term in ["aktbil","dagbok","beslut"])]
                
                prop = round(len(allfiles) * 0.004)
                
                filenames = random.sample(allfiles, prop)
                filenames = [os.path.join(dirpath, x) for x in filenames]
                copy_files(filenames, destination)
                

def rotate_pdf(folder):
    for file in glob.glob(folder + '*.pdf'):
        print(file)
        pdf = PdfFileReader(file)
        #degrees = pdf.getPage(0).get('/Rotate')
        degrees = 90
        #print(file, degrees)

        pdf = PdfFileReader(file)
        writer = PdfFileWriter()
        num_pages = pdf.getNumPages()
        
        if degrees == 90 or degrees == 270 or degrees == 180:
            
            output_file = open(file.split('.pdf')[0] + '_rotated.pdf', 'wb')
            
            for i in range(num_pages):
                page = pdf.getPage(i)
                page.rotateClockwise(degrees)
                writer.addPage(page)
            
            writer.write(output_file)
            output_file.close()
            
            shutil.move(file,folder + 'old')



def convert_img_pdf(path):
    imagelist = glob.glob(path + '*.JPG')
    print(imagelist)
    # imagelist is the list with all image filenames
    
    for image in imagelist:
        image_1 = Image.open(image)
        im_1 = image_1.convert('RGB')
        im_1.save(image.replace(".JPG",".pdf"))
        
    

def extract_page_pdf(path):
    """
    Input: path of files where one page should be extracted

    """
    
    for file in glob.glob(path + '*.pdf'):
        print(file)
        pdf_file_path = file
        file_base_name = pdf_file_path.replace('.pdf', '')
        
        pdf = PdfFileReader(pdf_file_path)
        
        page_num = pdf.numPages - 1
        
        print(page_num)
        
        pdfWriter = PdfFileWriter()
        pdfWriter.addPage(pdf.getPage(page_num))
        
        with open('{0}_subset.pdf'.format(file_base_name), 'wb') as f:
            pdfWriter.write(f)
            f.close()


if __name__ == '__main__':
    print('Executing...')
    paths_a = get_paths("P:/2020/14/Kodning/RA_files/prep/sample_pid_paths.csv")
    copy_files(paths_a, "P:/2020/14/Kodning/RA_files/pid/")
    #extract_page_pdf("P:/2020/14/Kodning/RA_files/pid/")
    #changename("P:/2020/14/Tingsratter/Lunds/Domar/all_scans/new/")
    
    
    
    
