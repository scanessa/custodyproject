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

filepaths_doc = 'P:/2020/14/Kodning/Clean_csvs_move_files/filepaths.txt' 
includes = ''

error_paths = [] 

def searchKey(string, part):
    finder = re.compile(string)
    match = finder.search(part)
    return match

def read_filepaths(doc):
    with open(doc,'r') as f:
        paths = f.read().splitlines() 
    return paths

def move_files(paths, error_files, pdf_dir):
    errors = 0
    for file in paths:
        p = pathlib.PureWindowsPath(file)
        p = str(p.as_posix())
        print(p)
        try:
            shutil.move(file,pdf_dir)
        except:
            errors += 1
            error_files.append(file)
    
    print('%d files threw an error: ' %(errors), error_paths)
    return errors, error_files

def copy_files(paths, error_files, pdf_dir):
    errors = 0
    for file in paths:
        p = pathlib.PureWindowsPath(file)
        p = str(p.as_posix())
        print(p)
        try:
            shutil.copy(file,pdf_dir)
        except:
            errors += 1
            error_files.append(file)
    
    print('%d files threw an error: ' %(errors), error_paths)
    return errors, error_files

def true_file(files):
    for fname in files:
        if not os.path.isfile(fname):
            print('N: ', fname)
            
def file_counter(path, searchkey):
    fileCount = len(glob.glob1(path,searchkey))   
    return fileCount
         
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
                os.rename(os.path.join(subdir, file), os.path.join(subdir, file_new))
                existing += 1
                
def changename(rootdir):
    """
    Remove () from filename
    """
    for subdir, dirs, files in os.walk(rootdir, topdown=True):
        for file in files:
            if includes in subdir and file.endswith('.JPG'):
                file_new = file.replace("(","_").replace(")","").replace(" ","_").replace("ä","a").replace("ö","o").replace("ü","u").replace("å","a")
                print('OLD: ', os.path.join(subdir, file))
                print('NEW: ', os.path.join(subdir, file_new))
                os.rename(os.path.join(subdir, file), os.path.join(subdir, file_new))

def randomsample(folder, samplesize, copyto):
    """
    To generate a random sample of files used for machine learning training
    folder: string, target folder with all files from which sample should be drawn
    samplesize: int, size of desired sample
    copyto: string, folder to which the sample files should be copied
    
    Note:
    - make sample size bigger than intended to have backups for testing
    - normal split is 70-20-10, put + 100 files for backup
    
    """
    allfiles = glob.glob(folder + "/*.pdf") #change to JPG if needed
    randomlist = random.sample(range(0, len(allfiles)), samplesize)
    sample = [allfiles[n] for n in randomlist]
    copy_files(sample, error_paths, copyto)

#Execute
#randomsample("P:/2020/14/Tingsratter/Sodertorns/Domar/all_scans", 600, "P:/2020/14/Kodning/Scans/classification/firstlastpage") #CHANGE SHUTIL.MOVE TO SHUTIL.COPY FOR FIRST ROUND
#randomsample("P:/2020/14/Kodning/Scans/classification/firstlastpage/validation", 50, "P:/2020/14/Kodning/Scans/classification/firstlastpage/testing") 

# Courts with scans: Lunds, Malmö, Stockholm, Helsingborgs, Hässleholms, Göteborgs
randomsample("P:/2020/14/Tingsratter/Lunds/Domar/Leverans/courtvisit/phone2", 5, "P:/2020/14/Kodning/Scans/all_scans/others/new")



